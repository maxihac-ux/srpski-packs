#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""№27 C4: гейт качества RU-полей контента паков (запуск в CI и локально).

Проверки по всем строкам (term/ex/dlg/qaq/qao) всех 4 уровневых паков:
  1) пустой RU-перевод; 2) латиница в RU (кроме белого списка цитат/размеров);
  3) цифры в RU; 4) мусорный суффикс «-hand»; 4а) буквы не кириллицы/латиницы (иероглифы и т.п.); 5) pymorphy3: токены, не прошедшие
  через словарь (FakeDictionary-угадывания) и не в tools/ru_whitelist.txt.

Вход:  python3 tools/ru_content_gate.py [--zips packs/*.zip | --dir tmp/work/content]
       (по умолчанию берётся ТОЛЬКО самая свежая версия каждого из a1/a2/b1/b2;
       аудио-, delta- и старые zip пропускаются)
       --baseline tools/ru_gate_baseline.txt — известные нарушения не валят гейт (только новые)
Выход: 0 — чисто; 1 — есть нарушения (список печатается); 2 — не хватает pymorphy3
       (используйте --no-morph, если морфологическая проверка не нужна).
Белый список: tools/ru_whitelist.txt (по одному токену в строке; токены «начинаются с»).
Латиница в RU: разрешена только строкам, начинающимся с записи «lat_<строка>» из белого
списка. Голый префикс «lat_» ничего не разрешает (аудит 2026-11-24: раньше он делал
проверку латиницы всегда «зелёной»).
"""
import argparse, glob, io, json, os, re, sys, unicodedata, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORD = re.compile(r'[а-яёА-ЯЁ-]+')
LAT = re.compile(r'[A-Za-z]')
DIG = re.compile(r'[0-9]')

def foreign_letters(text):
    """Буквы не кириллицы и не латиницы (иероглифы, арабица, греческий…).
    Аудит 25.11: в b2 2.0.5 остался перевод «Эгоизм часто разрушает最美的关系。» —
    проверка латиницы его не видела."""
    out = []
    for ch in text:
        if ch.isalpha():
            nm = unicodedata.name(ch, '')
            if not (nm.startswith('CYRILLIC') or nm.startswith('LATIN')):
                out.append(ch)
    return out

def load_whitelist():
    p = os.path.join(ROOT, 'tools', 'ru_whitelist.txt')
    wl = set()
    if os.path.exists(p):
        for line in open(p, encoding='utf-8'):
            line = line.strip().lower()
            if line and not line.startswith('#'):
                wl.add(line)
    return wl

LAT_PREFIX = 'lat_'

def whitelist_ok(tok, wl):
    low = tok.lower().strip('-')
    # записи «lat_…» относятся только к проверке латиницы, не к словам
    return any(low.startswith(w) for w in wl if not w.startswith(LAT_PREFIX))

def lat_ok(ru, wl):
    """Строка с латиницей разрешена, если для неё есть запись lat_<начало строки>.
    Пустой «хвост» (голый lat_) не считается разрешением."""
    key = LAT_PREFIX + ru.strip().lower()
    return any(key.startswith(w) for w in wl
               if w.startswith(LAT_PREFIX) and len(w) > len(LAT_PREFIX))

def build_rows(lv, words, qa, dialogs):
    """Единый построитель строк (term/ex/qaq/qao/dlg) для zip- и dir-режима."""
    out = []
    for w in words or []:
        out.append((lv, 'term', w['id'], (w.get('forms') or {}).get('cyrl') or '', w.get('translation') or ''))
        for i, e in enumerate(w.get('examples') or []):
            out.append((lv, 'ex', f"{w['id']}#{i}", (e.get('forms') or {}).get('cyrl') or '', e.get('translation') or ''))
    for q in qa or []:
        out.append((lv, 'qaq', q['id'], q['q'].get('cyr') or '', q['q'].get('ru') or ''))
        for i, o in enumerate(q.get('options') or []):
            out.append((lv, 'qao', f"{q['id']}#{i}", o.get('sr') or '', o.get('ru') or ''))
    if dialogs is not None:
        items = dialogs if isinstance(dialogs, list) else dialogs.get('dialogs', [])
        for d in items:
            did = d.get('id') or ''
            for i, r in enumerate(d.get('lines') or d.get('replicas') or d.get('items') or []):
                sr = r.get('cyr') or r.get('sr') or (r.get('forms') or {}).get('cyrl') or ''
                out.append((lv, 'dlg', f"{did}#{i}", sr, r.get('ru') or r.get('translation') or ''))
    return out

ZIP_RE = re.compile(r'^sr-ru-(a1|a2|b1|b2)-(\d+)\.(\d+)\.(\d+)\.zip$')

def current_content_zips(paths):
    """Из списка путей оставить по одному, самому свежему zip на уровень a1/a2/b1/b2.
    Аудио-, delta-, qa- и прочие zip, не подходящие под шаблон, пропускаются."""
    best = {}
    for zp in paths:
        m = ZIP_RE.match(os.path.basename(zp))
        if not m:
            continue
        ver = tuple(int(x) for x in m.groups()[1:])
        if m.group(1) not in best or ver > best[m.group(1)][0]:
            best[m.group(1)] = (ver, zp)
    return [best[lv][1] for lv in ('a1', 'a2', 'b1', 'b2') if lv in best]

def rows_from_zip(zpath):
    m = ZIP_RE.match(os.path.basename(zpath))
    if not m:
        raise SystemExit(f'не похоже на контент-пак уровня: {zpath}')
    lv = m.group(1)
    with zipfile.ZipFile(zpath) as z:
        names = set(z.namelist())
        if 'content/words.json' not in names:
            raise SystemExit(f'в {zpath} нет content/words.json')
        def load(n):
            return json.loads(z.read(n).decode('utf-8')) if n in names else None
        return build_rows(lv, load('content/words.json'), load('content/qa.json'),
                          load('content/dialogs.json'))

def rows_from_dir(base):
    out = []
    for lv in ('a1', 'a2', 'b1', 'b2'):
        def load(fn):
            p = os.path.join(base, lv, fn)
            if not os.path.exists(p):
                return None
            with open(p, encoding='utf-8') as f:
                return json.load(f)
        out.extend(build_rows(lv, load('words.json'), load('qa.json'), load('dialogs.json')))
    return out

def check_rows(rows, wl, morph=None):
    """Список нарушений (lv, kind, rid, code, detail) по строкам контента."""
    bad = []
    for lv, kind, rid, sr, ru in rows:
        if not ru.strip():
            bad.append((lv, kind, rid, 'empty_ru', ''))
        if LAT.search(ru) and not lat_ok(ru, wl):
            bad.append((lv, kind, rid, 'latin_in_ru', ru[:60]))
        if foreign_letters(ru):
            bad.append((lv, kind, rid, 'foreign_script_in_ru', ru[:60]))
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
    return bad

def violation_key(v):
    """Ключ нарушения для baseline: «уровень вид id код [токен]» (без текста строки)."""
    lv, kind, rid, code, detail = v
    return ' '.join([lv, kind, rid, code] + ([detail] if code == 'ru_unknown_token' else []))

def load_baseline(path):
    keys = set()
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                keys.add(' '.join(line.split()))
    return keys

def split_by_baseline(bad, baseline):
    """(новые, известные, устаревшие_ключи): гейт падает только на новых."""
    seen = {violation_key(v) for v in bad}
    new = [v for v in bad if violation_key(v) not in baseline]
    known = [v for v in bad if violation_key(v) in baseline]
    stale = sorted(baseline - seen)
    return new, known, stale

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--zips', default='packs/sr-ru-*.zip',
                    help='маски через запятую; из найденного берётся самая свежая версия каждого уровня')
    ap.add_argument('--dir', help='вместо зипов: каталог с a1/a2/b1/b2/*.json (уже распакованные)')
    ap.add_argument('--no-morph', action='store_true', help='только структурные проверки')
    ap.add_argument('--baseline', help='файл известных нарушений («уровень вид id код [токен]»): '
                    'гейт падает только на НОВЫХ; устаревшие записи (исправлено — удалите) '
                    'печатаются предупреждением')
    a = ap.parse_args()
    wl = load_whitelist()
    rows = []
    if a.dir:
        rows = rows_from_dir(a.dir)
    else:
        found = []
        for pat in a.zips.split(','):
            found.extend(sorted(glob.glob(os.path.join(ROOT, pat.strip()))))
        zips = current_content_zips(found)
        if not zips:
            raise SystemExit('не найдено ни одного контент-пака sr-ru-(a1|a2|b1|b2)-X.Y.Z.zip')
        print('паки:', ', '.join(os.path.basename(z) for z in zips))
        for zp in zips:
            rows.extend(rows_from_zip(zp))
    print(f'строк: {len(rows)}')

    # №29.3: у каждого слова — хотя бы один пример (проверка возвращена при
    # слиянии копий гейта №63: она жила только в CI-копии bazits_fch)
    words_by_lv = {}
    if a.dir:
        for lv in ('a1', 'a2', 'b1', 'b2'):
            p = os.path.join(a.dir, lv, 'words.json')
            if os.path.exists(p):
                with open(p, encoding='utf-8') as f:
                    words_by_lv[lv] = json.load(f)
    else:
        for zp in zips:
            m = ZIP_RE.match(os.path.basename(zp))
            if not m:
                continue
            with zipfile.ZipFile(zp) as z:
                if 'content/words.json' in z.namelist():
                    words_by_lv[m.group(1)] = json.loads(z.read('content/words.json').decode('utf-8'))
    ex_bad = check_examples(words_by_lv)

    morph = None
    if not a.no_morph:
        try:
            import pymorphy3
            morph = pymorphy3.MorphAnalyzer()
        except ImportError:
            print('! pymorphy3 не установлен: pip install pymorphy3 (или запустите с --no-morph)')
            sys.exit(2)

    bad = check_rows(rows, wl, morph)
    all_bad = bad + ex_bad
    if a.baseline:
        base = load_baseline(a.baseline)
        all_bad, known, stale = split_by_baseline(all_bad, base)
        if known:
            print(f'известные нарушения (baseline): {len(known)}')
            for v in known:
                print('  ~', *v)
        for k in stale:
            print(f'! устаревшая запись baseline (в паках уже исправлено — удалите): {k}')
    if all_bad:
        print('НАРУШЕНИЯ:', len(all_bad))
        for b in all_bad:
            print(' ', *b)
        sys.exit(1)
    print('RU-гейт: чисто ✓')


def check_examples(words_by_lv):
    """№29.3: у каждого слова — хотя бы один пример. words_by_lv: {level: [word]}."""
    bad = []
    total = 0
    for lv in ('a1', 'a2', 'b1', 'b2'):
        for w in words_by_lv.get(lv) or []:
            total += 1
            if not (w.get('examples') or []):
                bad.append((lv, 'term', w.get('id') or '?', 'no_examples', w.get('term') or ''))
    print(f'покрытие примерами: {total - len(bad)}/{total} слов')
    return bad

if __name__ == '__main__':
    main()
