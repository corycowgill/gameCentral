#!/usr/bin/env python3
"""Rewrite the hand-kept game counts and the JSON-LD game list in index.html
from the game tiles themselves, so adding a tile never leaves them stale.

Usage: python3 tools/sync-game-list.py   (run from the repo root)

The page also corrects these at load time in the browser; this keeps the
static HTML right for crawlers that don't run JavaScript.
"""
import html
import json
import re
from pathlib import Path

page = Path(__file__).resolve().parent.parent / 'index.html'
src = page.read_text(encoding='utf-8')

tiles = re.findall(
    r'<a href="([^"]+)" class="game-card[^"]*"[^>]*>.*?<div class="card-title">(.*?)</div>',
    src, re.S)
games = [{'name': html.unescape(re.sub(r'<[^>]+>', '', t)).strip(), 'url': u} for u, t in tiles]
n = len(games)

item_list = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    'name': 'AI-Generated Browser Games',
    'numberOfItems': n,
    'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': g['name'], 'url': g['url']}
        for i, g in enumerate(games)
    ],
}
ld = json.dumps(item_list, indent=4, ensure_ascii=False).replace('\n', '\n    ')
src, k = re.subn(r'(<script type="application/ld\+json" id="ld-games">\n    ).*?(\n    </script>)',
                 lambda m: m.group(1) + ld + m.group(2), src, flags=re.S)
assert k == 1, 'game list <script id="ld-games"> not found'

for pattern, repl in [
    (r'(Free AI-generated browser games\. )\d+( games)', rf'\g<1>{n}\g<2>'),
    (r'(<p class="game-count"><span>)\d+(</span>)', rf'\g<1>{n}\g<2>'),
    (r'(<div class="stat-value" data-target=")\d+(" data-suffix="">0</div>\s*<div class="stat-label">Games Shipped)', rf'\g<1>{n}\g<2>'),
]:
    src, k = re.subn(pattern, repl, src)
    assert k == 1, f'pattern not found: {pattern}'

page.write_text(src, encoding='utf-8')
print(f'{n} games in the tiles, counts and game list now match')
