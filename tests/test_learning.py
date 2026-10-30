import random
import unittest

from core import ROOT, load_words
from corpus import Corpus
import conjugation


class LearningTests(unittest.TestCase):
    def test_corpus_count_credits_and_search(self):
        corpus = Corpus()
        self.assertEqual(corpus.count, 144215)
        sample = corpus.sample(seed=42)
        self.assertEqual(len(sample), 100)
        self.assertEqual(sample, corpus.sample(seed=42))
        self.assertNotEqual(sample, corpus.sample(seed=43))
        self.assertTrue(all('tatoeba.org' in row['source'] for row in sample))
        for entry in sample[:3]:
            self.assertEqual(corpus.get(entry['id']), entry)
        self.assertTrue(corpus.sample(search='árbol'))
        # Operator-like input is searched as a literal word, not FTS syntax.
        self.assertEqual(corpus.sample(search='***'), [])
        self.assertTrue(corpus.sample(search='" OR *'))

    def test_sentence_question_unique_answers(self):
        corpus = Corpus()
        for _ in range(20):
            q = corpus.question()
            self.assertEqual(len(set(q['options'])), 4)
            self.assertEqual(q['options'].count(q['word']['english']), 1)
            self.assertEqual(q['word']['example_es'], q['word']['spanish'])

    def test_all_words_have_context_and_types(self):
        for word in load_words():
            self.assertTrue(word['example_es'], word['spanish'])
            self.assertTrue(word['example_en'], word['spanish'])
            self.assertTrue(word['example_credit'], word['spanish'])
            self.assertNotIn('appears in my notes', word['example_en'])
            if word['category'] == 'Descriptions':
                self.assertIn('adj.', word['pos'])
            if word['pos'].startswith('noun'):
                self.assertTrue(word['spanish'].startswith(('el ', 'la ', 'los ', 'las ')))
        lookup = {w['spanish']: w for w in load_words()}
        self.assertEqual(lookup['el agua']['pos'], 'noun · f.')
        self.assertNotIn('ha pescado', lookup['el pescado']['example_es'])
        self.assertIn('pescado', lookup['el pescado']['example_es'].lower())

    def test_all_conjugations_and_examples(self):
        for verb in conjugation.VERBS:
            for tense in ('present', 'past'):
                for person in range(6):
                    q = conjugation.question(tense, verb, person=person)
                    self.assertEqual(len(set(q['options'])), 4)
                    word = q['word']
                    self.assertIn(word['english'], word['example_es'].split())
                    self.assertEqual(conjugation.resolve(word['id']), word)
        self.assertEqual(conjugation.entry('ser','present',0)['english'], 'soy')
        self.assertEqual(conjugation.entry('dormir','past',2)['english'], 'durmió')
        self.assertEqual(conjugation.entry('jugar','past',0)['english'], 'jugué')
        self.assertEqual(conjugation.entry('leer','past',5)['english'], 'leyeron')
        self.assertIsNone(conjugation.resolve('conj:unknown:present:9'))


if __name__ == '__main__':
    unittest.main()
