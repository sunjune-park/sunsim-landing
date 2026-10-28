import importlib.util
import json
from pathlib import Path
from datetime import date
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET

spec=importlib.util.spec_from_file_location('insights',Path(__file__).with_name('insights.py'))
app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)

class PublishingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)/'site'
        shutil.copytree(app.ROOT,self.root,ignore=shutil.ignore_patterns('dist','__pycache__','.git'))
        self.today=date(2026,10,28)
    def tearDown(self): self.tmp.cleanup()
    def drafts(self): return sorted([p for p in app.load_posts(self.root) if p['status']=='draft'],key=lambda p:p['queue'])
    def test_existing_urls_and_draft_exclusion(self):
        expected=app.visible_posts(app.load_posts(self.root),self.today)
        app.build(self.root,self.today)
        out=self.root/'dist'
        self.assertEqual(len(list((out/'insight').glob('*/index.html'))),len(expected))
        xml=ET.parse(out/'sitemap.xml')
        urls=[n.text for n in xml.findall('.//{*}loc')]
        self.assertEqual(len(urls),len(set(urls)))
        for p in expected:
            self.assertIn(app.ORIGIN+'/insight/'+p['slug']+'/',urls)
            page=(out/'insight'/p['slug']/'index.html').read_text()
            self.assertIn('datetime="'+p['published']+'"',page)
            self.assertEqual(page.count('<h1>'),1)
        for p in self.drafts():
            self.assertFalse((out/'insight'/p['slug']).exists())
            self.assertNotIn(p['slug'],(out/'insight/index.html').read_text())
            self.assertFalse(any(p['slug'] in u for u in urls))
        for name in ['content','scripts','templates','CONTENT-GUIDE.md','netlify.toml']:
            self.assertFalse((out/name).exists())
    def test_three_posts_and_retry_idempotence(self):
        if len(self.drafts())<3:self.skipTest('Queue already completed')
        first=app.publish_next(self.root,today=self.today,batch='test-batch')
        self.assertEqual(len(first),3)
        source={p: p.read_bytes() for p in (self.root/'content/insights').glob('*.md')}
        self.assertEqual(app.publish_next(self.root,today=self.today,batch='test-batch'),[])
        self.assertEqual(source,{p:p.read_bytes() for p in source})
        for p in first:self.assertTrue((self.root/'dist/insight'/p['slug']/'index.html').exists())
    def test_future_date_is_not_published(self):
        if not self.drafts():self.skipTest('Queue completed')
        p=self.drafts()[0];p.update(status='published',published='2099-01-01')
        p['_path'].write_text(app.serialize(p))
        app.build(self.root,self.today)
        self.assertFalse((self.root/'dist/insight'/p['slug']).exists())
    def test_failed_build_rolls_back_publication(self):
        if not self.drafts():self.skipTest('Queue completed')
        app.build(self.root,self.today)
        old_feed=(self.root/'dist/insight/feed.json').read_bytes()
        p=self.drafts()[0];p['_body']+='\n[Invalid internal link](/insight/not-published/)\n'
        p['_path'].write_text(app.serialize(p))
        before=p['_path'].read_bytes()
        with self.assertRaisesRegex(ValueError,'unpublished'):app.publish_next(self.root,today=self.today,batch='failure-test')
        self.assertEqual(p['_path'].read_bytes(),before)
        self.assertEqual((self.root/'dist/insight/feed.json').read_bytes(),old_feed)
    def test_markdown_safety_and_tables(self):
        rendered=app.markdown('## 제목\n\n<script>alert(1)</script>\n\n| A | B |\n|---|---|\n| 가 | 나 |\n\n- **굵게**\n- [상담](/contact/)')
        self.assertNotIn('<script>',rendered)
        self.assertIn('article-table-wrap',rendered)
        self.assertIn('<strong>굵게</strong>',rendered)
        with self.assertRaises(ValueError):app.markdown('[bad](javascript:alert)')
        with self.assertRaises(ValueError):app.markdown('| A | B |\n|---|---|\n| only one |')
    def test_invalid_content_does_not_replace_dist(self):
        app.build(self.root,self.today)
        old=(self.root/'dist/insight/index.html').read_bytes()
        p=app.load_posts(self.root)[0];p['slug']='../escape';p['_path'].write_text(app.serialize(p))
        with self.assertRaises(ValueError):app.build(self.root,self.today)
        self.assertEqual(old,(self.root/'dist/insight/index.html').read_bytes())

if __name__=='__main__':unittest.main()
