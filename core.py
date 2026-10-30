"""Vocabulary, fair questions, and session-local learner progress."""
import csv
import random
import re
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def level_for_xp(xp):
    return max(0, xp) // 100 + 1


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.casefold())
                   if unicodedata.category(c) != 'Mn')


def load_words(path=ROOT / 'data' / 'vocabulary.tsv'):
    with Path(path).open(encoding='utf-8', newline='') as handle:
        words = list(csv.DictReader(handle, delimiter='\t'))
    seen = set()
    for word in words:
        for field in ('spanish', 'english', 'category', 'source', 'note'):
            if field not in word or word[field] is None:
                raise ValueError(f'Missing field {field}')
        # Preserve the IDs used by earlier releases when supplying noun articles.
        word['id'] = {'el norte': 'norte', 'el sur': 'sur'}.get(word['spanish'], word['spanish'])
        if not word['spanish'] or not word['english'] or word['id'] in seen:
            raise ValueError(f'Empty or duplicate entry: {word}')
        seen.add(word['id'])
        word.setdefault('pos', 'expression')
        word.setdefault('example_es', '')
        word.setdefault('example_en', '')
        word.setdefault('example_credit', '')
    return words


# Avoid near-synonyms as distractors as well as overlapping answer text.
FAMILIES = [
    {'beautiful', 'lovely', 'handsome', 'good-looking'},
    {'happy', 'cheerful', 'pleased'}, {'wonderful', 'excellent'},
    {'delicious', 'tasty'}, {'healthy', 'wholesome'},
    {'understand', 'comprehend'}, {'begin', 'start'},
    {'end', 'finish'}, {'respond', 'answer'}, {'happen', 'occur'},
    {'walk', 'move'}, {'throw', 'launch'}, {'try', 'attempt'},
    {'enjoy', 'pleasure'}, {'calm', 'peaceful', 'quiet'},
]


def meaning_tokens(text):
    tokens = set(re.findall(r'[a-z-]+', normalized(text))) - {
        'to', 'a', 'an', 'the', 'of', 'in', 'on', 'or', 'for', 'be', 'someone', 'spain'}
    for i, family in enumerate(FAMILIES):
        if tokens & family:
            tokens.add(f'family{i}')
    return tokens


def make_question(words, pool=None, previous=None, rng=None):
    rng = rng or random
    eligible = [w for w in (words if pool is None else pool) if not w['note'].startswith('REVIEW:')]
    candidates = [w for w in eligible if w['id'] != previous] or eligible
    if not candidates:
        raise ValueError('No confirmed words available for this practice.')
    word = rng.choice(candidates)
    used = meaning_tokens(word['english'])
    alternatives = list(words)
    rng.shuffle(alternatives)
    options = [word['english']]
    for other in alternatives:
        tokens = meaning_tokens(other['english'])
        if other['id'] == word['id'] or other['note'].startswith('REVIEW:') or tokens & used:
            continue
        options.append(other['english'])
        used |= tokens
        if len(options) == 4:
            break
    if len(options) != 4:
        raise ValueError('At least four distinct, non-overlapping meanings are required.')
    rng.shuffle(options)
    return {'token': str(uuid.uuid4()), 'word': word, 'options': options}


class Progress:
    """A view of one learner's Streamlit session mapping; never reads/writes files.

    Pass st.session_state in the app, or a separate plain dict in each unit test.
    This object must not be global or stored in st.cache_resource/st.cache_data.
    """
    KEY = 'learning_progress'

    def __init__(self, session):
        self.session = session
        if self.KEY not in session:
            session[self.KEY] = {
                'stats': {'xp': 0, 'total': 0, 'correct': 0},
                'streak': 0, 'answers': {}, 'mistakes': {},
            }

    @property
    def state(self):
        return self.session[self.KEY]

    def answer(self, question, choice):
        if choice not in question['options']:
            raise ValueError('Answer is not an available option.')
        state = self.state
        token = question['token']
        if token in state['answers']:
            return dict(state['answers'][token])
        correct = choice == question['word']['english']
        streak = state['streak'] + 1 if correct else 0
        bonus = 15 if correct and streak % 3 == 0 else 0
        delta = 10 + bonus if correct else -5
        result = {'chosen': choice, 'correct': correct, 'delta': delta,
                  'bonus': bonus, 'streak': streak}
        word_id = question['word']['id']
        mistakes = state['mistakes']
        if correct:
            if word_id in mistakes:
                mistakes[word_id]['reviews'] += 1
                mistakes[word_id]['resolved'] = 1
        else:
            if word_id not in mistakes:
                mistakes[word_id] = {'word': word_id, 'misses': 0, 'reviews': 0, 'resolved': 0}
            mistakes[word_id]['misses'] += 1
            mistakes[word_id]['resolved'] = 0
            mistakes[word_id]['last_missed'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
        state['stats']['xp'] += delta
        state['stats']['total'] += 1
        state['stats']['correct'] += int(correct)
        state['streak'] = streak
        state['answers'][token] = result
        # Explicit reassignment also works with Streamlit session-state wrappers.
        self.session[self.KEY] = state
        return dict(result)

    def streak(self):
        return self.state['streak']

    def stats(self):
        return dict(self.state['stats'])

    def mistakes(self):
        rows = sorted(self.state['mistakes'].values(),
                      key=lambda row: row['last_missed'], reverse=True)
        return [dict(row) for row in sorted(rows, key=lambda row: (row['resolved'], -row['misses']))]
