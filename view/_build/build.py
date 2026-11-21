"""Build pulido.art/view: one viewing room per series plus the index.

Usage: python3 view/_build/build.py   (run from the repo root)
Edit rooms.json to change a room, then rerun. site_meta.json holds title,
year, size, price and image proportions pulled from the main site.
"""
import json, re, html, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
NUM = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve']

meta = json.load(open(os.path.join(HERE, 'site_meta.json')))
cfg = json.load(open(os.path.join(HERE, 'rooms.json')))
tpl = open(os.path.join(HERE, 'template.html')).read()
warnings = []


def price(p):
    m = re.match(r'\$([\d.]+)K', p)
    return int(round(float(m.group(1)) * 1000)) if m else None


def work(wid, line):
    m = meta[wid]
    a, b = [int(x) for x in re.findall(r'\d+', m['size'])[:2]]
    portrait = m['ih'] > m['iw'] * 1.05
    square = abs(m['ih'] - m['iw']) <= m['iw'] * 0.05
    w, h = (min(a, b), max(a, b)) if portrait else (max(a, b), min(a, b))
    img_ratio = m['iw'] / m['ih']
    if abs(img_ratio - w / h) > 0.12 and not square:
        warnings.append('%s %s: listed %s but the image is %.2f:1' % (wid, m['t'], m['size'], img_ratio))
    return {'id': wid, 't': m['t'], 'y': m['y'], 'w': w, 'h': h, 'p': price(m['price']), 'line': line}


def years(ws):
    ys = sorted({w['y'] for w in ws})
    return str(ys[0]) if len(ys) == 1 else '%d–%d' % (ys[0], ys[-1])


rooms_out = []
for r in cfg['rooms']:
    ws = [work(i, l) for i, l in r['works']]
    n = len(ws)
    yr = years(ws)
    data = {'slug': r['slug'], 'until': cfg['until'], 'hero': r['hero'], 'years': yr, 'works': ws,
            'walls': [{'n': 'Wall ' + 'ABCDEFG'[k], 'ids': ids} for k, ids in enumerate(r['walls'])]}
    essay = '<div class="lbl">%s</div>\n    ' % html.escape(r['name'])
    essay += '\n    '.join('<p>%s</p>' % html.escape(p) for p in r['essay'])
    essay += '\n    <blockquote>&ldquo;%s&rdquo;</blockquote>\n    <cite class="lbl">Chas Pulido</cite>' % html.escape(r['quote'])
    page = (tpl.replace('{{NAME}}', html.escape(r['name']))
               .replace('{{H1}}', r['h1'])
               .replace('{{META}}', '%s paintings &middot; %s &middot; Acrylic on canvas' % (NUM[n].capitalize(), yr.replace('–', '&ndash;')))
               .replace('{{ESSAY}}', essay)
               .replace('{{HERO}}', r['hero'])
               .replace('{{COUNT_WORD}}', NUM[n])
               .replace('{{WALL_WORD}}', NUM[len(r['walls'])])
               .replace('{{DATA}}', json.dumps(data, ensure_ascii=False).replace('</', '<\\/')))
    os.makedirs(os.path.join(OUT, r['slug']), exist_ok=True)
    open(os.path.join(OUT, r['slug'], 'index.html'), 'w').write(page)
    big = sum(1 for w in ws if w['w'] >= 72 or w['h'] >= 72)
    rooms_out.append({'slug': r['slug'], 'name': r['name'], 'short': r['short'], 'hero': r['hero'], 'n': n, 'years': yr,
                      'thumbs': [w['id'] for w in ws][:5], 'from': min(w['p'] for w in ws if w['p']), 'to': max(w['p'] for w in ws if w['p'])})

idx = open(os.path.join(HERE, 'index_template.html')).read()
open(os.path.join(OUT, 'index.html'), 'w').write(idx.replace('{{ROOMS}}', json.dumps(rooms_out, ensure_ascii=False)))

print('built %d rooms: %s' % (len(rooms_out), ', '.join(r['slug'] for r in rooms_out)))
for w in warnings:
    print('check size:', w)
