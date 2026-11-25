# -*- coding: utf-8 -*-
"""Юнит-тесты RU-гейта (запуск: python3 -I -m unittest discover -s tools -p 'test_*.py')."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ru_content_gate as g  # noqa: E402

WL = {'чевап', 'lat_hvala', 'lat_'}


class WhitelistTests(unittest.TestCase):
    def test_bare_lat_prefix_allows_nothing(self):
        # регрессия аудита 24.11: запись «lat_» раньше делала проверку латиницы всегда «зелёной»
        self.assertFalse(g.lat_ok('Профessor написал', {'lat_'}))

    def test_exact_lat_entry_allows_string(self):
        self.assertTrue(g.lat_ok('hvala lepo', WL))
        self.assertFalse(g.lat_ok('molim', WL))

    def test_lat_entries_do_not_whitelist_words(self):
        self.assertFalse(g.whitelist_ok('lat_hvala', WL))
        self.assertTrue(g.whitelist_ok('чевапчичи', WL))


class ZipSelectionTests(unittest.TestCase):
    def test_only_latest_content_zip_per_level(self):
        paths = [
            'packs/sr-ru-a1-2.0.9.zip', 'packs/sr-ru-a1-2.0.10.zip',
            'packs/sr-ru-a1-audio-f-1.0.6.zip', 'packs/sr-ru-a1-2.0.9-to-2.0.10.delta.zip',
            'packs/sr-ru-b2-2.0.5.zip', 'packs/sr-ru-base-2.1.5.zip', 'packs/sr-ru-qa-a2-1-1.0.0.zip',
        ]
        self.assertEqual(g.current_content_zips(paths),
                         ['packs/sr-ru-a1-2.0.10.zip', 'packs/sr-ru-b2-2.0.5.zip'])


def row(ru, rid='w1#0'):
    return ('a1', 'ex', rid, 'x', ru)


class CheckRowsTests(unittest.TestCase):
    def test_clean_row(self):
        self.assertEqual(g.check_rows([row('Это чистая строка.')], WL), [])

    def test_detects_each_class(self):
        codes = {v[3] for v in g.check_rows([
            row('', 'e'), row('Профessor', 'l'), row('Дом 5', 'd'), row('слово-hand', 'h')], WL)}
        self.assertEqual(codes, {'empty_ru', 'latin_in_ru', 'digits_in_ru', 'hand_suffix'})

    def test_whitelisted_latin_string_passes(self):
        self.assertEqual(g.check_rows([row('hvala')], WL), [])

    def test_foreign_script_detected(self):
        # регрессия: иероглифы в b2 2.0.5 (w4193) гейт не видел
        bad = g.check_rows([row('Эгоизм часто разрушает最美的关系。', 'w4193#0')], WL)
        self.assertEqual([v[3] for v in bad], ['foreign_script_in_ru'])

    def test_cyrillic_latin_and_punctuation_are_not_foreign(self):
        self.assertEqual(g.foreign_letters('Это — «строка», ёжик; hvala! č ž'), [])
        self.assertEqual(g.foreign_letters('日本'), ['日', '本'])


class BaselineTests(unittest.TestCase):
    def test_new_known_stale(self):
        bad = [('b1', 'ex', 'w1#0', 'latin_in_ru', 'x'), ('b2', 'ex', 'w2#0', 'latin_in_ru', 'y')]
        base = {'b1 ex w1#0 latin_in_ru', 'b1 ex w9#0 latin_in_ru'}
        new, known, stale = g.split_by_baseline(bad, base)
        self.assertEqual([v[2] for v in new], ['w2#0'])
        self.assertEqual([v[2] for v in known], ['w1#0'])
        self.assertEqual(stale, ['b1 ex w9#0 latin_in_ru'])

    def test_unknown_token_key_includes_token(self):
        v = ('a1', 'term', 'w3', 'ru_unknown_token', 'оффер')
        self.assertEqual(g.violation_key(v), 'a1 term w3 ru_unknown_token оффер')

    def test_load_baseline_ignores_comments(self):
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write('# коммент\n\nb1  ex w1#0 latin_in_ru\n')
        try:
            self.assertEqual(g.load_baseline(f.name), {'b1 ex w1#0 latin_in_ru'})
        finally:
            os.unlink(f.name)


if __name__ == '__main__':
    unittest.main()
