"""Sync shared layout into static source pages; Insight is generated at build."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
parts = {name: (root / 'partials' / (name + '.html')).read_text().strip()
         for name in ('header', 'footer')}
for page in root.rglob('*.html'):
    if set(page.relative_to(root).parts) & {'partials', 'templates', 'content', 'dist', 'tests'}:
        continue
    text = page.read_text()
    for name, fragment in parts.items():
        if name == 'header' and page == root / 'index.html':
            fragment = fragment.replace('site-header solid', 'site-header')
        pattern = rf'<!-- shared:{name}:start -->[\s\S]*?<!-- shared:{name}:end -->'
        replacement = f'<!-- shared:{name}:start -->\n{fragment}\n<!-- shared:{name}:end -->'
        text = re.sub(pattern, lambda _: replacement, text)
    page.write_text(text)
