"""Indexed, attributed sentence pairs; no sentence-to-word guessing."""
import random
import re
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path

from core import ROOT, normalized

DEFAULT_CORPUS = ROOT / 'data' / 'sentences.sqlite3'


def tokens(text):
    return re.findall(r'[^\W\d_]+', text.casefold(), flags=re.UNICODE)


class Corpus:
    def __init__(self, path=DEFAULT_CORPUS):
        self.path = Path(path).resolve()
        with self.connect() as db:
            self.count = db.execute('SELECT COUNT(*) FROM sentences').fetchone()[0]

    def connect(self):
        return closing(sqlite3.connect(f'{self.path.as_uri()}?mode=ro', uri=True))

    @staticmethod
    def entry(row):
        return {'id': f'sentence:{row[0]}', 'spanish': row[1], 'english': row[2],
                'source': row[3], 'category': 'Sentences', 'note': '', 'pos': 'sentence',
                'example_es': row[1], 'example_en': row[2], 'example_credit': row[3]}

    def sample(self, limit=100, seed=None, search=''):
        rng = random.Random(seed)
        with self.connect() as db:
            if search.strip():
                # FTS uses literal tokens, never executes user-provided FTS syntax.
                terms = re.findall(r'[^\W_]+', search, flags=re.UNICODE)
                if not terms:
                    return []
                query = ' AND '.join('"' + t + '"' for t in terms)
                rows = db.execute('''SELECT s.id,s.spanish,s.english,s.credit FROM sentences_fts f
                    JOIN sentences s ON s.id=f.rowid WHERE sentences_fts MATCH ? LIMIT 2000''', (query,)).fetchall()
                rng.shuffle(rows)
                return [self.entry(r) for r in rows[:limit]]
            ids = rng.sample(range(1, self.count + 1), min(limit, self.count))
            rows = db.execute(f'SELECT id,spanish,english,credit FROM sentences WHERE id IN ({",".join("?" for _ in ids)})', ids).fetchall()
        rng.shuffle(rows)
        return [self.entry(r) for r in rows]

    def get(self, entry_id):
        if not entry_id.startswith('sentence:'):
            return None
        with self.connect() as db:
            row = db.execute('SELECT id,spanish,english,credit FROM sentences WHERE id=?', (entry_id.split(':')[1],)).fetchone()
        return self.entry(row) if row else None

    def question(self, previous=None):
        entries = self.sample(150)
        # Keep alternative translations for the same Spanish prompt out of options.
        unique = {}
        for entry in entries:
            unique.setdefault(normalized(entry['spanish']), entry)
        pool = list(unique.values())
        chosen = random.choice([w for w in pool if w['id'] != previous] or pool)
        return self.question_for(chosen, pool)

    def question_for(self, word, candidates=None):
        from difflib import SequenceMatcher
        candidates = candidates or self.sample(200)
        options = [word['english']]
        # Reject near-identical English translations and duplicate Spanish prompts.
        # The corpus is sentence-aligned; it is never treated as a word dictionary.
        for other in candidates:
            if normalized(other['spanish']) == normalized(word['spanish']):
                continue
            if any(SequenceMatcher(None, normalized(other['english']), normalized(a)).ratio() > .72 for a in options):
                continue
            options.append(other['english'])
            if len(options) == 4:
                break
        if len(options) < 4:
            raise ValueError('Not enough distinct sentence translations. Try again.')
        random.shuffle(options)
        return {'token': str(uuid.uuid4()), 'word': word, 'options': options}

    def example(self, spanish, english='', pos=''):
        phrase = re.sub(r'^(el|la|los|las) ', '', spanish)
        terms = tokens(phrase)
        if not terms:
            return None
        query = '"' + ' '.join(terms) + '"'
        with self.connect() as db:
            rows = db.execute('''SELECT s.spanish,s.english,s.credit FROM sentences_fts f
                JOIN sentences s ON s.id=f.rowid WHERE sentences_fts MATCH ?
                ORDER BY LENGTH(s.spanish) LIMIT 100''', (query,)).fetchall()
        # Exact phrase match with word boundaries; accents are not discarded here.
        pattern = r'(?<!\w)' + re.escape(phrase) + r'(?!\w)'
        if pos.startswith('noun'):
            # A participle such as ha pescado is not an example of el pescado.
            pattern = r'\b(?:el|la|los|las|un|una|unos|unas|este|esta|estos|estas|ese|esa|mi|tu|su|al|del)\s+' + re.escape(phrase) + r'(?!\w)'
        elif pos.startswith('adj.'):
            pattern = r'\b(?:es|soy|eres|somos|sois|son|está|estoy|estás|estamos|estáis|están|era|eran|fue|parece|parecen|ser|estar)\s+(?:(?:muy|tan|más|menos|bastante|demasiado|un poco)\s+)?' + re.escape(phrase) + r'(?!\w)'
        meaning = set(tokens(re.sub(r'\([^)]*\)', '', english))) - {'to','a','the','of','in','on','for','or','be','as','with','someone','something'}
        for row in rows:
            translated = set(tokens(row[1]))
            if (re.search(pattern, row[0], re.I) and len(tokens(row[0])) >= 3
                    and (not meaning or meaning & translated)):
                return row
        return None
