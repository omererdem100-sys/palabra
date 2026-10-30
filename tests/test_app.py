"""Each AppTest instance represents a separate learner session."""
import unittest

from streamlit.testing.v1 import AppTest

from core import ROOT, Progress


class AppTests(unittest.TestCase):
    def test_two_live_sessions_have_independent_progress(self):
        first = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=20).run()
        second = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=20).run()
        self.assertEqual(Progress(first.session_state).stats()['xp'], 0)
        self.assertEqual(Progress(second.session_state).stats()['xp'], 0)
        q = first.session_state['question_practice']
        wrong = next(a for a in q['options'] if a != q['word']['english'])
        next(b for b in first.button if b.label == wrong).click().run()
        self.assertEqual(Progress(first.session_state).stats()['xp'], -5)
        self.assertEqual(Progress(second.session_state).mistakes(), [])
        self.assertEqual(Progress(second.session_state).stats()['xp'], 0)
        q = second.session_state['question_practice']
        next(b for b in second.button if b.label == q['word']['english']).click().run()
        first.run()
        self.assertFalse(first.exception)
        self.assertFalse(second.exception)
        self.assertEqual(Progress(first.session_state).stats()['xp'], -5)
        self.assertEqual(Progress(second.session_state).stats()['xp'], 10)
        self.assertEqual(Progress(first.session_state).streak(), 0)
        self.assertEqual(Progress(second.session_state).streak(), 1)

    def test_full_learning_flow(self):
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=20).run()
        self.assertFalse(app.exception)
        q = app.session_state['question_practice']
        wrong = next(a for a in q['options'] if a != q['word']['english'])
        next(b for b in app.button if b.label == wrong).click().run()
        self.assertFalse(app.exception)
        self.assertTrue(app.error)
        self.assertEqual(Progress(app.session_state).stats()['xp'], -5)
        app.run()
        self.assertEqual(Progress(app.session_state).stats()['total'], 1)
        app.radio[0].set_value('My Mistakes').run()
        self.assertFalse(app.exception)
        app.toggle[0].set_value(True).run()
        review = app.session_state['question_review']
        next(b for b in app.button if b.label == review['word']['english']).click().run()
        self.assertTrue(app.success)
        self.assertEqual(Progress(app.session_state).stats()['xp'], 5)
        next(b for b in app.button if b.label == 'Next word →').click().run()
        self.assertFalse(app.exception)
        self.assertNotIn('question_review', app.session_state)
        app.radio[0].set_value('Words').run()
        app.text_input[0].set_value('ARBOL').run()
        self.assertEqual(len(app.dataframe[0].value), 1)
        self.assertFalse(app.exception)
        fresh = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=20).run()
        self.assertFalse(fresh.exception)
        self.assertEqual(Progress(fresh.session_state).stats()['xp'], 0)
        self.assertEqual(Progress(fresh.session_state).mistakes(), [])
        self.assertEqual(Progress(app.session_state).stats()['xp'], 5)

    def test_extended_modes_browse_limit_examples_and_combo(self):
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=20).run()
        for index in range(3):
            q = app.session_state['question_practice']
            next(b for b in app.button if b.label == q['word']['english']).click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any('In context' in m.value for m in app.markdown))
            if index < 2:
                next(b for b in app.button if b.label == 'Next word →').click().run()
        self.assertEqual(Progress(app.session_state).stats()['xp'], 45)
        self.assertIn('combo bonus', app.success[0].value)
        app.radio[0].set_value('Sentence practice').run()
        q = app.session_state['question_sentences']
        next(b for b in app.button if b.label == q['word']['english']).click().run()
        self.assertFalse(app.exception)
        app.radio[0].set_value('Verb conjugation').run()
        next(s for s in app.selectbox if s.label == 'Tense').select('Past (Pretérito indefinido)').run()
        q = app.session_state['question_conjugation_past_Surprise me']
        wrong = next(a for a in q['options'] if a != q['word']['english'])
        next(b for b in app.button if b.label == wrong).click().run()
        app.radio[0].set_value('My Mistakes').run()
        app.toggle[0].set_value(True).run()
        q = app.session_state['question_review']
        self.assertTrue(q['word']['id'].startswith('conj:'))
        next(b for b in app.button if b.label == q['word']['english']).click().run()
        self.assertFalse(app.exception)

    def test_sidebar_modes_and_browsing(self):
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=20).run()
        self.assertEqual(app.sidebar.radio[0].options,
                         ['Test', 'Words', 'My Mistakes', 'Vocabulary',
                          'Sentence practice', 'Verb conjugation'])
        self.assertFalse(any(s.label == 'Practice mode' for s in app.selectbox))
        app.radio[0].set_value('Verb conjugation').run()
        self.assertTrue(any(s.label == 'Tense' for s in app.selectbox))
        app.radio[0].set_value('Test').run()
        self.assertTrue(any(s.label == 'Tense' for s in app.selectbox))
        app.radio[0].set_value('Vocabulary').run()
        self.assertTrue('question_practice' in app.session_state)
        app.radio[0].set_value('Words').run()
        self.assertEqual(len(app.dataframe[0].value), 100)
        first = app.dataframe[0].value['Spanish'].tolist()
        next(b for b in app.button if b.label == 'Shuffle these 100').click().run()
        self.assertNotEqual(first, app.dataframe[0].value['Spanish'].tolist())
        next(s for s in app.selectbox if s.label == 'Library').select('Sentence library').run()
        self.assertEqual(len(app.dataframe[0].value), 100)
        app.text_input[0].set_value('árbol').run()
        self.assertTrue(len(app.dataframe[0].value))
        self.assertFalse(app.exception)


if __name__ == '__main__':
    unittest.main()
