"""SSBP's dependency-free content publisher. See CONTENT-GUIDE.md.

Markdown intentionally supports only paragraphs, ##/### headings, flat lists,
pipe tables, links, bold, emphasis and inline code. HTML is escaped in Markdown.
Existing articles use trusted HTML fragments so migration preserves their content.
"""
from pathlib import Path
from datetime import datetime, date
from zoneinfo import ZoneInfo
from html import escape
from urllib.parse import urlsplit
from string import Template
import argparse
import json
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://ssbp.co.kr'
TZ = ZoneInfo('Asia/Seoul')
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
PUBLIC_FILES = ['index.html', '_redirects', '_headers', 'robots.txt',
                'favicon.ico', 'favicon-16x16.png', 'favicon-32x32.png',
                'apple-touch-icon.png']
PUBLIC_DIRS = ['assets', 'about', 'services', 'certification', 'rnd',
               'policy-fund', 'contact']

def read_post(path):
    text = path.read_text(encoding='utf-8')
    if not text.startswith('+++\n') or '\n+++\n' not in text[4:]:
        raise ValueError(f'{path.name}: JSON metadata must be between +++ lines')
    raw, body = text[4:].split('\n+++\n', 1)
    post = json.loads(raw)
    post.update(_path=path, _body=body)
    return post

def serialize(post):
    meta = {k:v for k,v in post.items() if not k.startswith('_')}
    return '+++\n' + json.dumps(meta, ensure_ascii=False, indent=2) + '\n+++\n' + post['_body']

def load_posts(root):
    posts = [read_post(p) for p in sorted((root/'content/insights').glob('*.md'))]
    seen, queues = set(), set()
    for p in posts:
        slug = p.get('slug', '')
        if not SLUG.fullmatch(slug) or slug in seen or p['_path'].stem != slug:
            raise ValueError(f'Invalid/duplicate slug or filename: {slug}')
        seen.add(slug)
        for field in ('title','description','category'):
            if not isinstance(p.get(field),str) or not p[field].strip():
                raise ValueError(f'{slug}: missing {field}')
        if p.get('status') not in ('draft','published'):
            raise ValueError(f'{slug}: invalid status')
        if p.get('format') not in ('markdown','html') or not p['_body'].strip():
            raise ValueError(f'{slug}: invalid/empty body')
        if p.get('queue') is not None:
            q=p['queue']
            if not isinstance(q,int) or q<1 or q in queues:
                raise ValueError('Invalid or duplicate publication queue')
            queues.add(q)
        if p['status']=='published':
            d=date.fromisoformat(p['published'])
            if p.get('modified') and date.fromisoformat(p['modified'])<d:
                raise ValueError(f'{slug}: modified precedes published')
    if not posts:
        raise ValueError('No articles found')
    return posts

def safe_link(url):
    parts = urlsplit(url)
    if url.startswith('//') or parts.scheme not in ('','https','http','mailto'):
        raise ValueError(f'Unsupported link: {url}')
    return escape(url, quote=True)

INLINE = re.compile(r'`([^`]+)`|\[([^\]\n]+)\]\(([^\s)]+)\)|\*\*([^*\n]+)\*\*|\*([^*\n]+)\*')
def inline(text):
    out, pos = [], 0
    for m in INLINE.finditer(text):
        out.append(escape(text[pos:m.start()]))
        if m[1] is not None: out.append('<code>'+escape(m[1])+'</code>')
        elif m[2] is not None: out.append('<a href="'+safe_link(m[3])+'">'+escape(m[2])+'</a>')
        elif m[4] is not None: out.append('<strong>'+escape(m[4])+'</strong>')
        else: out.append('<em>'+escape(m[5])+'</em>')
        pos=m.end()
    return ''.join(out)+escape(text[pos:])

def markdown(text):
    lines=text.strip().splitlines()
    out=[]; i=0; section=False
    while i<len(lines):
        line=lines[i].strip()
        if not line: i+=1; continue
        if line.startswith(('## ','### ')):
            if section: out.append('</section>')
            out.append('<section><h2>'+inline(line.split(' ',1)[1])+'</h2>')
            section=True; i+=1
        elif line.startswith('#') or line.startswith('```'):
            raise ValueError('Use ## headings; fenced code is not supported')
        elif line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i+=1
            if len(rows)<3 or not all(re.fullmatch(r':?-{3,}:?',c) for c in rows[1]):
                raise ValueError('Invalid Markdown table separator')
            if any(len(r)!=len(rows[0]) for r in rows):
                raise ValueError('Mismatched table columns')
            out.append('<div class="article-table-wrap"><table><thead><tr>'+''.join('<th scope="col">'+inline(c)+'</th>' for c in rows[0])+'</tr></thead><tbody>')
            out.extend('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in r)+'</tr>' for r in rows[2:])
            out.append('</tbody></table></div>')
        elif re.match(r'(?:[-*] |\d+\. )',line):
            ordered=bool(re.match(r'\d+\. ',line)); tag='ol' if ordered else 'ul'
            pattern=r'\d+\. ' if ordered else r'[-*] '
            out.append('<'+tag+'>')
            while i<len(lines) and re.match(pattern,lines[i].strip()):
                out.append('<li>'+inline(re.sub(pattern,'',lines[i].strip(),count=1))+'</li>'); i+=1
            out.append('</'+tag+'>')
        else:
            para=[line]; i+=1
            while i<len(lines) and lines[i].strip() and not re.match(r'(?:#|\||[-*] |\d+\. )',lines[i].strip()):
                para.append(lines[i].strip()); i+=1
            out.append('<p>'+inline(' '.join(para))+'</p>')
    if section: out.append('</section>')
    return '\n'.join(out)

def json_script(value):
    return json.dumps(value,ensure_ascii=False,indent=2).replace('<','\\u003c')

def breadcrumb(title=None, url=None):
    items=[('홈',ORIGIN+'/'),('Insight',ORIGIN+'/insight/')]
    if title: items.append((title,url))
    return {'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[
        {'@type':'ListItem','position':i+1,'name':n,'item':u} for i,(n,u) in enumerate(items)]}

def layout(root,text,home=False):
    for name in ('header','footer'):
        part=(root/'partials'/f'{name}.html').read_text(encoding='utf-8').strip()
        if name=='header' and home: part=part.replace('site-header solid','site-header')
        text=re.sub(r'<!-- shared:'+name+r':start -->[\s\S]*?<!-- shared:'+name+r':end -->',
                    lambda _:f'<!-- shared:{name}:start -->\n{part}\n<!-- shared:{name}:end -->',text)
    return text

def row(post,home=False):
    h='h3' if home else 'h2'
    cls='insight-row reveal-up' if home else 'insight-row'
    return f'<a class="{cls}" href="/insight/{post["slug"]}/"><span class="insight-cat">{escape(post["category"])}</span><{h}>{escape(post["title"])}</{h}><span class="insight-status">{post["published"].replace("-",".")} →</span></a>'

def article(root,p):
    url=f'{ORIGIN}/insight/{p["slug"]}/'
    schema={'@context':'https://schema.org','@type':'BlogPosting','@id':url+'#article',
            'mainEntityOfPage':url,'headline':p['title'],'description':p['description'],
            'datePublished':p['published'],'dateModified':p.get('modified') or p['published'],
            'inLanguage':'ko-KR','author':{'@id':ORIGIN+'/#organization'},'publisher':{'@id':ORIGIN+'/#organization'}}
    if p['format']=='html':
        body=p['_body']
    else:
        body='<div class="article-content article-markdown"><p class="article-lead">'+escape(p['description'])+'</p>'+markdown(p['_body'])+'</div>\n<div class="article-end"><a href="/insight/">← 전체 글 보기</a><a href="/contact/">상담 문의 →</a></div>'
    vals={k:escape(p[k]) for k in ('title','description','category')}
    vals.update(url=url,published=p['published'],display_date=p['published'].replace('-','.'),
                subtitle='<p class="archive-intro">'+escape(p['subtitle'])+'</p>' if p.get('subtitle') else '',
                body=body,breadcrumb=json_script(breadcrumb(p['title'],url)),article_schema=json_script(schema))
    rendered=Template((root/'templates/insight-article.html').read_text(encoding='utf-8')).substitute(vals)
    return layout(root,rendered)

def visible_posts(posts,today):
    return sorted([p for p in posts if p['status']=='published' and date.fromisoformat(p['published'])<=today],
                  key=lambda p:(-date.fromisoformat(p['published']).toordinal(),p.get('order',p.get('queue',9999)),p['slug']))

def validate_links(staging,posts):
    published={p['slug'] for p in posts}
    for page in staging.rglob('*.html'):
        for href in re.findall(r'href=["\']([^"\']+)["\']',page.read_text(encoding='utf-8')):
            parsed=urlsplit(href)
            if parsed.netloc and parsed.netloc!='ssbp.co.kr': continue
            match=re.fullmatch(r'/insight/([^/]+)/?',parsed.path)
            if match and match[1] not in published:
                raise ValueError(f'{page.name} links to unpublished article {match[1]}')

def build(root=ROOT,today=None):
    today=today or datetime.now(TZ).date()
    posts=visible_posts(load_posts(root),today)
    # Compile into a temporary tree; an invalid manuscript never replaces dist.
    with tempfile.TemporaryDirectory(prefix='ssbp-build-') as temp:
        staging=Path(temp)/'dist'; staging.mkdir()
        for name in PUBLIC_FILES:
            if (root/name).is_file(): shutil.copy2(root/name,staging/name)
        for name in PUBLIC_DIRS:
            if (root/name).is_dir(): shutil.copytree(root/name,staging/name)
        for page in staging.rglob('*.html'):
            page.write_text(layout(root,page.read_text(encoding='utf-8'),page==staging/'index.html'),encoding='utf-8')
        for p in posts:
            target=staging/'insight'/p['slug']/'index.html'; target.parent.mkdir(parents=True)
            target.write_text(article(root,p),encoding='utf-8')
        archive=Template((root/'templates/insight-index.html').read_text(encoding='utf-8')).substitute(
            rows='\n'.join(row(p) for p in posts),breadcrumb=json_script(breadcrumb()))
        (staging/'insight').mkdir(exist_ok=True)
        (staging/'insight/index.html').write_text(layout(root,archive),encoding='utf-8')
        home=staging/'index.html'
        text=home.read_text(encoding='utf-8')
        text,count=re.subn(r'<!-- generated:insights:start -->[\s\S]*?<!-- generated:insights:end -->',
            lambda _:'<!-- generated:insights:start -->\n'+'\n'.join(row(p,True) for p in posts[:3])+'\n<!-- generated:insights:end -->',text)
        if count!=1: raise ValueError('Home Insight marker missing or duplicated')
        home.write_text(text,encoding='utf-8')
        ns='http://www.sitemaps.org/schemas/sitemap/0.9'
        ET.register_namespace('',ns); site=ET.Element('{'+ns+'}urlset')
        routes=json.loads((root/'content/site-pages.json').read_text(encoding='utf-8'))
        for route in routes:
            target=staging/(route.lstrip('/')+'index.html')
            if not target.exists(): raise ValueError('Missing static route: '+route)
            node=ET.SubElement(site,'{'+ns+'}url'); ET.SubElement(node,'{'+ns+'}loc').text=ORIGIN+route
        for p in posts:
            node=ET.SubElement(site,'{'+ns+'}url')
            ET.SubElement(node,'{'+ns+'}loc').text=ORIGIN+'/insight/'+p['slug']+'/'
            ET.SubElement(node,'{'+ns+'}lastmod').text=p.get('modified') or p['published']
        ET.indent(site)
        ET.ElementTree(site).write(staging/'sitemap.xml',encoding='utf-8',xml_declaration=True)
        (staging/'insight/feed.json').write_text(json.dumps([
            {'slug':p['slug'],'title':p['title'],'published':p['published'],'url':ORIGIN+'/insight/'+p['slug']+'/'} for p in posts],ensure_ascii=False,indent=2),encoding='utf-8')
        validate_links(staging,posts)
        output=root/'dist'
        if output.exists(): shutil.rmtree(output)
        shutil.copytree(staging,output)
    return posts

def publish_next(root=ROOT,limit=3,batch=None,today=None):
    today=today or datetime.now(TZ).date()
    batch=batch or today.isoformat()
    if not 1<=limit<=3: raise ValueError('Publication batch must be between 1 and 3')
    # A date-based batch is idempotent: a retry can only fill remaining slots.
    posts=load_posts(root)
    done=[p for p in posts if p.get('published_batch')==batch and p['status']=='published']
    remaining=max(0,limit-len(done))
    queue=sorted([p for p in posts if p['status']=='draft' and p.get('queue') is not None],key=lambda p:p['queue'])
    selected=queue[:remaining]; backups={p['_path']:p['_path'].read_text(encoding='utf-8') for p in selected}
    try:
        for p in selected:
            p.update(status='published',published=today.isoformat(),modified=today.isoformat(),published_batch=batch)
            p['_path'].write_text(serialize(p),encoding='utf-8')
        build(root,today)
    except Exception:
        for path,text in backups.items(): path.write_text(text,encoding='utf-8')
        raise
    return selected

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['build','publish','list'])
    parser.add_argument('--limit',type=int,default=3)
    parser.add_argument('--apply',action='store_true',help='Required to change draft status')
    args=parser.parse_args()
    if args.command=='build': print(f'Built {len(build())} published articles into dist/')
    elif args.command=='list':
        for p in load_posts(ROOT): print(p['status'],p.get('queue','-'),p['slug'])
    else:
        if not args.apply: parser.error('publish requires --apply (changes manuscripts)')
        selected=publish_next(limit=args.limit)
        print(json.dumps({'published':[p['slug'] for p in selected]},ensure_ascii=False))

if __name__=='__main__': main()
