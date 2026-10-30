import random
import unittest
from unittest.mock import patch

from core import Progress, load_words, make_question, meaning_tokens, normalized, level_for_xp


class VocabularyTests(unittest.TestCase):
    def setUp(self):
        self.words = load_words()

    def test_sources_and_accents(self):
        self.assertEqual({p for w in self.words for p in w['source'].split(',')}, set('1234567') | {'ZIP'})
        self.assertEqual(normalized('ÁRBOL'), 'arbol')
        self.assertGreater(len(self.words), 400)

    def test_every_confirmed_word_has_four_fair_options(self):
        for word in self.words:
            if word['note'].startswith('REVIEW:'):
                continue
            q = make_question(self.words, [word], rng=random.Random(12))
            self.assertEqual(len(set(q['options'])), 4)
            self.assertEqual(q['options'].count(word['english']), 1)
            for answer in q['options']:
                if answer != word['english']:
                    self.assertFalse(meaning_tokens(answer) & meaning_tokens(word['english']))

    def test_review_words_excluded_and_empty_pool(self):
        flagged = [w for w in self.words if w['note'].startswith('REVIEW:')]
        self.assertTrue(flagged)
        with self.assertRaises(ValueError):
            make_question(self.words, flagged)
        with self.assertRaises(ValueError):
            make_question(self.words, [])

    def test_no_immediate_repeat(self):
        q = make_question(self.words)
        self.assertNotEqual(make_question(self.words, previous=q['word']['id'])['word']['id'], q['word']['id'])


class SessionProgressTests(unittest.TestCase):
    def test_score_idempotency_rerun_and_review(self):
        session = {}
        store = Progress(session)
        words = load_words()
        q = make_question(words)
        wrong = next(a for a in q['options'] if a != q['word']['english'])
        self.assertFalse(store.answer(q, wrong)['correct'])
        store.answer(q, q['word']['english'])
        self.assertEqual(store.stats(), {'xp': -5, 'total': 1, 'correct': 0})
        rerun = Progress(session)
        self.assertEqual(rerun.mistakes()[0]['misses'], 1)
        review = make_question(words, [q['word']])
        rerun.answer(review, review['word']['english'])
        self.assertEqual(rerun.stats()['xp'], 5)
        self.assertEqual(rerun.mistakes()[0]['resolved'], 1)
        self.assertEqual(rerun.mistakes()[0]['reviews'], 1)
        again = make_question(words, [q['word']])
        rerun.answer(again, next(a for a in again['options'] if a != again['word']['english']))
        self.assertEqual(rerun.mistakes()[0]['resolved'], 0)
        self.assertEqual(rerun.mistakes()[0]['misses'], 2)

    def test_invalid_answer_does_not_score(self):
        store = Progress({})
        with self.assertRaises(ValueError):
            store.answer(make_question(load_words()), 'not an option')
        self.assertEqual(store.stats()['total'], 0)

    def test_combo_bonus_reset_duplicate_and_rerun(self):
        session = {}
        store = Progress(session)
        for n in range(1, 7):
            q = make_question(load_words())
            result = store.answer(q, q['word']['english'])
            self.assertEqual(result['bonus'], 15 if n % 3 == 0 else 0)
            self.assertEqual(result['streak'], n)
            self.assertEqual(store.answer(q, q['word']['english']), result)
            store = Progress(session)
        self.assertEqual(store.stats()['xp'], 90)
        self.assertEqual(store.streak(), 6)
        q = make_question(load_words())
        store.answer(q, next(a for a in q['options'] if a != q['word']['english']))
        self.assertEqual(store.streak(), 0)
        self.assertEqual(store.stats()['xp'], 85)

    def test_independent_sessions_start_clean(self):
        first, second = Progress({}), Progress({})
        q = make_question(load_words())
        wrong = next(a for a in q['options'] if a != q['word']['english'])
        first.answer(q, wrong)
        self.assertEqual(second.stats(), {'xp': 0, 'total': 0, 'correct': 0})
        self.assertEqual(second.mistakes(), [])
        self.assertEqual(level_for_xp(second.stats()['xp']), 1)
        second.answer(q, q['word']['english'])
        self.assertEqual(first.stats()['xp'], -5)
        self.assertEqual(second.stats()['xp'], 10)
        self.assertEqual(first.streak(), 0)
        self.assertEqual(second.streak(), 1)
        self.assertEqual(second.mistakes(), [])
        self.assertEqual(Progress({}).stats()['xp'], 0)

    def test_progress_does_not_open_files_or_databases(self):
        q = make_question(load_words())
        with patch('builtins.open', side_effect=AssertionError('Unexpected file access')), \
             patch('sqlite3.connect', side_effect=AssertionError('Unexpected database access')):
            store = Progress({})
            result = store.answer(q, q['word']['english'])
            self.assertEqual(result['delta'], 10)
            self.assertEqual(store.stats()['xp'], 10)
            self.assertEqual(store.mistakes(), [])


if __name__ == '__main__':
    unittest.main()
