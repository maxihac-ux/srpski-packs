#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""№27 C4: гейт качества RU-полей контента паков (запуск в CI и локально).

Проверки по всем строкам (term/ex/dlg/qaq/qao) всех 4 уровневых паков:
  1) пустой RU-перевод; 2) латиница в RU (кроме белого списка цитат/размеров);
  3) цифры в RU; 4) мусорный суффикс «-hand»; 5) pymorphy3: токены, не прошедшие
  через словарь (FakeDictionary-угадывания) и не в tools/ru_whitelist.txt.

Вход:  python3 tools/ru_content_gate.py [--zips packs/*.zip | --dir tmp/work/content]
Выход: 0 — чисто; 1 — есть нарушения (список печатается).
Белый список: tools/ru_whitelist.txt (по одному токену в строке; токены «начинаются с»).
"""
import argparse, glob, io, json, os, re, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORD = re.compile(r'[а-яёА-ЯЁ-]+')
LAT = re.compile(r'[A-Za-z]')
DIG = re.compile(r'[0-9]')

def load_whitelist():
    p = os.path.join(ROOT, 'tools', 'ru_whitelist.txt')
    wl = set()
    if os.path.exists(p):
        for line in open(p, encoding='utf-8'):
            line = line.strip().lower()
            if line and not line.startswith('#'):
                wl.add(line)
    return wl

def whitelist_ok(tok, wl):
    low = tok.lower().strip('-')
    return any(low.startswith(w) for w in wl)

def rows_from_zip(zpath):
    z = zipfile.ZipFile(zpath)
    lv = re.search(r'sr-ru-(a[12]|b[12])-', zpath).group(1)
    out = []
    words = json.loads(z.read('content/words.json').decode('utf-8'))
    for w in words:
        out.append((lv, 'term', w['id'], (w.get('forms') or {}).get('cyrl') or '', w.get('translation') or ''))
        for i, e in enumerate(w.get('examples') or []):
            out.append((lv, 'ex', f"{w['id']}#{i}", (e.get('forms') or {}).get('cyrl') or '', e.get('translation') or ''))
    if 'content/qa.json' in z.namelist():
        for q in json.loads(z.read('content/qa.json').decode('utf-8')):
            out.append((lv, 'qaq', q['id'], q['q'].get('cyr') or '', q['q'].get('ru') or ''))
            for i, o in enumerate(q.get('options') or []):
                out.append((lv, 'qao', f"{q['id']}#{i}", o.get('sr') or '', o.get('ru') or ''))
    if 'content/dialogs.json' in z.namelist():
        dl = json.loads(z.read('content/dialogs.json').decode('utf-8'))
        items = dl if isinstance(dl, list) else dl.get('dialogs', [])
        for d in items:
            did = d.get('id') or ''
            for i, r in enumerate(d.get('lines') or d.get('replicas') or d.get('items') or []):
                sr = r.get('cyr') or r.get('sr') or (r.get('forms') or {}).get('cyrl') or ''
                out.append((lv, 'dlg', f"{did}#{i}", sr, r.get('ru') or r.get('translation') or ''))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--zips', default='packs/sr-ru-a*-*.zip,packs/sr-ru-b*-*.zip')
    ap.add_argument('--dir', help='вместо зипов: каталог с a1/a2/b1/b2/*.json (уже распакованные)')
    ap.add_argument('--no-morph', action='store_true', help='только структурные проверки')
    a = ap.parse_args()
    wl = load_whitelist()
    rows = []
    if a.dir:
        for lv in ('a1', 'a2', 'b1', 'b2'):
            zpath = os.path.join(a.dir, lv, '..')
            import json as _j
            for fn in ('words.json', 'qa.json', 'dialogs.json'):
                p = os.path.join(a.dir, lv, fn)
                if not os.path.exists(p):
                    continue
                d = _j.load(open(p, encoding='utf-8'))
                if fn == 'words.json':
                    for w in d:
                        rows.append((lv, 'term', w['id'], (w.get('forms') or {}).get('cyrl') or '', w.get('translation') or ''))
                        for i, e in enumerate(w.get('examples') or []):
                            rows.append((lv, 'ex', f"{w['id']}#{i}", (e.get('forms') or {}).get('cyrl') or '', e.get('translation') or ''))
                elif fn == 'qa.json':
                    for q in d:
                        rows.append((lv, 'qaq', q['id'], q['q'].get('cyr') or '', q['q'].get('ru') or ''))
                        for i, o in enumerate(q.get('options') or []):
                            rows.append((lv, 'qao', f"{q['id']}#{i}", o.get('sr') or '', o.get('ru') or ''))
                else:
                    items = d if isinstance(d, list) else d.get('dialogs', [])
                    for dd in items:
                        for i, r in enumerate(dd.get('lines') or dd.get('replicas') or dd.get('items') or []):
                            sr = r.get('cyr') or r.get('sr') or (r.get('forms') or {}).get('cyrl') or ''
                            rows.append((lv, 'dlg', f"{dd.get('id')}#{i}", sr, r.get('ru') or r.get('translation') or ''))
    else:
        zips = []
        for pat in a.zips.split(','):
            zips.extend(sorted(glob.glob(os.path.join(ROOT, pat.strip()))))
        for zp in zips:
            rows.extend(rows_from_zip(zp))
    print(f'строк: {len(rows)}')

    morph = None
    if not a.no_morph:
        try:
            import pymorphy3
            morph = pymorphy3.MorphAnalyzer()
        except ImportError:
            print('! pymorphy3 не установлен — морфологическая проверка пропущена')

    bad = []
    for lv, kind, rid, sr, ru in rows:
        if not ru.strip():
            bad.append((lv, kind, rid, 'empty_ru', ''))
        for ch in set(LAT.findall(ru)):
            if ch.isascii() and not whitelist_ok('lat_' + ru.strip(), wl):
                bad.append((lv, kind, rid, 'latin_in_ru', ru[:60]))
                break
        if DIG.search(ru):
            bad.append((lv, kind, rid, 'digits_in_ru', ru[:60]))
        if re.search(r'-hand\b', ru):
            bad.append((lv, kind, rid, 'hand_suffix', ru[:60]))
        if morph:
            for tok in WORD.findall(ru):
                low = tok.lower().strip('-')
                if not low or whitelist_ok(low, wl):
                    continue
                if '-' in low and all(whitelist_ok(x, wl) for x in low.split('-')):
                    continue
                ps = morph.parse(low)
                if ps and all(type(p.methods_stack[0][0]).__name__ != 'DictionaryAnalyzer' for p in ps):
                    bad.append((lv, kind, rid, 'ru_unknown_token', low))
    if bad:
        print('НАРУШЕНИЯ:', len(bad))
        for b in bad:
            print(' ', *b)
        sys.exit(1)
    print('RU-гейт: чисто ✓')

if __name__ == '__main__':
    main()
