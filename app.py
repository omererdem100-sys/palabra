import html
import random
import secrets
from pathlib import Path

import streamlit as st

from core import ROOT, Progress, load_words, make_question, normalized, level_for_xp
from corpus import Corpus, DEFAULT_CORPUS
import conjugation

st.set_page_config(page_title='¡Palabra! · A little Spanish, every day', page_icon='☀️', layout='wide')
st.markdown(f'<style>{(ROOT / "assets" / "style.css").read_text(encoding="utf-8")}</style>', unsafe_allow_html=True)


def esc(text):
    return html.escape(str(text))


try:
    words = load_words()
    @st.cache_resource
    def open_corpus(path, modified):
        return Corpus(Path(path))
    corpus = open_corpus(str(DEFAULT_CORPUS), DEFAULT_CORPUS.stat().st_mtime_ns) if DEFAULT_CORPUS.exists() else None
    if Progress.KEY not in st.session_state:
        # Discard stale quiz feedback when upgrading an already-open old app.
        for key in list(st.session_state):
            if key.startswith(('question_', 'result_')) or key == 'seen_reveals':
                del st.session_state[key]
    progress = Progress(st.session_state)
except (OSError, ValueError) as error:
    st.error(f'Could not open vocabulary or progress: {error}')
    st.stop()

stats = progress.stats()
xp = stats['xp']
level = level_for_xp(xp)
if st.session_state.get('navigation') == 'Collection':
    st.session_state['navigation'] = 'Test'
with st.sidebar:
    st.markdown('<div class="brand">¡Palabra<span>!</span></div><p class="eyebrow">YOUR DAILY DOSE OF SPANISH</p>', unsafe_allow_html=True)
    st.write('Small steps. New words. Big possibilities.')
    destination = st.radio('Explore', ['Test', 'Words', 'My Mistakes', 'Vocabulary',
                                     'Sentence practice', 'Verb conjugation'],
                           key='navigation', label_visibility='collapsed', width='stretch')
    practice_modes = ('Vocabulary', 'Sentence practice', 'Verb conjugation')
    if destination in practice_modes:
        st.session_state['practice_mode'] = destination
    practice_mode = st.session_state.get('practice_mode', 'Vocabulary')
    page = 'Test' if destination in practice_modes else destination
    st.divider()
    st.markdown(f'**Level {level} · Spanish explorer**')
    st.progress((max(0, xp) % 100) / 100)
    st.caption(f'{100 - max(0, xp) % 100} XP to your next level')
    streak = progress.streak()
    st.markdown(f'**🔥 {streak} correct in a row**')
    st.caption(f'{3 - streak % 3} more correct for +15 bonus XP. A mistake resets the streak.')
    st.markdown('**The daily recipe**  \nLearn a word. Take a chance. Try again.')
    st.caption('Your progress stays in this session only. A new tab or full page refresh starts fresh.')

st.markdown('<div class="topline">SPANISH → ENGLISH <span>A LITTLE SUN. A LITTLE SPANISH. ☀</span></div>', unsafe_allow_html=True)
left, right = st.columns([3, 1])
with left:
    title, subtitle = {
        'Test': ('One word closer.', 'A little practice today. A bigger world tomorrow.'),
        'Words': ('Your pocket of Spanish.', 'A fresh selection of 100. A whole language to explore.'),
        'My Mistakes': ('Every mistake is a beginning.', 'Give the tricky words another chance to stick.')
    }[page]
    st.markdown(f'<h1>{title}</h1><p class="subtitle">{subtitle}</p>', unsafe_allow_html=True)
with right:
    st.markdown(f'<div class="xp-card"><span>TOTAL EXPERIENCE</span><strong>{xp:,} <small>XP</small></strong></div>', unsafe_allow_html=True)

a, b, c = st.columns(3)
a.metric('Words to discover', len(words))
b.metric('Answers given', stats['total'])
c.metric('Accuracy', f"{round(100 * stats['correct'] / stats['total']) if stats['total'] else 0}%")
st.divider()
if corpus:
    st.caption(f'{len(words):,} vocabulary entries · {corpus.count:,} bilingual sentence pairs available')


def example(word):
    if word.get('example_es') and word.get('example_en'):
        st.markdown('#### In context')
        st.markdown(f'<div class="example-card"><p lang="es">{esc(word["example_es"])}</p>'
                    f'<p>{esc(word["example_en"])}</p></div>', unsafe_allow_html=True)
        with st.expander('Example source'):
            st.caption(word.get('example_credit', 'AI-assisted teaching example'))
            if 'tatoeba.org' in word.get('example_credit', ''):
                st.markdown('[Tatoeba](https://tatoeba.org) / [ManyThings](https://www.manythings.org/anki/) · [CC BY 2.0 FR](https://creativecommons.org/licenses/by/2.0/fr/)')


def review_question(pool, previous=None):
    word = random.choice([w for w in pool if w['id'] != previous] or pool)
    if word['id'].startswith('conj:'):
        return conjugation.question(word['tense'], word['verb'], person=word['person'])
    if word['id'].startswith('sentence:'):
        return corpus.question_for(word)
    candidates = words
    candidates = [w for w in candidates if w['spanish'] != word['spanish']] + [word]
    return make_question(candidates, pool=[word])


def quiz(mode, pool, factory=None):
    key = f'question_{mode}'
    result_key = f'result_{mode}'
    if not pool and key not in st.session_state:
        st.success('All caught up! Your review list is clear. Keep exploring in Test.')
        return
    if key not in st.session_state:
        try:
            st.session_state[key] = factory(None) if factory else make_question(words, pool=pool)
        except ValueError as error:
            st.info(str(error))
            return
    q = st.session_state[key]
    result = st.session_state.get(result_key)
    is_form = q['word']['id'].startswith('conj:')
    is_sentence = q['word']['id'].startswith('sentence:')
    heading = 'Mistake review' if mode == 'review' else 'Verb practice' if is_form else 'Sentence practice' if is_sentence else 'Vocabulary practice'
    direction = 'SUBJECT → VERB FORM' if is_form else 'SPANISH → ENGLISH'
    card_class = 'sentence' if is_sentence else 'form' if is_form else 'word'
    st.markdown(f'<div class="quiz-card {card_class}"><div class="eyebrow">{esc(heading.upper())} · {direction}</div>'
                f'<h2 lang="es">{esc(q["word"]["spanish"])}</h2><p>{esc(q["word"].get("pos", ""))} · '
                f'{"Choose the correct conjugation." if q["word"]["id"].startswith("conj:") else "Choose the English meaning."}</p></div>', unsafe_allow_html=True)
    if result:
        for i in range(0, 4, 2):
            cols = st.columns(2)
            for j in range(2):
                answer = q['options'][i+j]
                kind = 'correct' if answer == q['word']['english'] else 'wrong' if answer == result['chosen'] else 'neutral'
                symbol = '✓' if kind == 'correct' else '✕' if kind == 'wrong' else '·'
                animate = 'reveal' if q['token'] not in st.session_state.get('seen_reveals', set()) else ''
                cols[j].markdown(f'<div class="answer {kind} {animate}"><span>{symbol} &nbsp; {esc(answer)}</span></div>', unsafe_allow_html=True)
        st.session_state.setdefault('seen_reveals', set()).add(q['token'])
        if result['correct']:
            bonus = result.get('bonus', 0)
            st.success(f'Correct! +{result["delta"]} XP.' + (f' 🔥 {result["streak"]} in a row: +{bonus} combo bonus included!' if bonus else ' Another word in your pocket.'))
        else:
            st.error(f'Not quite. −5 XP. The answer is: {q["word"]["english"]}. Saved to My Mistakes.')
        if q['word']['note']:
            st.info(q['word']['note'])
        example(q['word'])
        if st.button('Next word →', type='primary', key=f'next_{mode}', width='stretch'):
            previous = q['word']['id']
            del st.session_state[key]
            del st.session_state[result_key]
            if pool:
                st.session_state[key] = factory(previous) if factory else make_question(words, pool=pool, previous=previous)
            st.rerun()
    else:
        for i in range(0, 4, 2):
            cols = st.columns(2)
            for j in range(2):
                answer = q['options'][i+j]
                if cols[j].button(answer, key=f'{q["token"]}_{i+j}', width='stretch'):
                    st.session_state[result_key] = progress.answer(q, answer)
                    st.rerun()
    st.caption('Correct +10 XP · Incorrect −5 XP · Every 3 consecutive correct: +15 bonus XP')


if page == 'Test':
    if practice_mode == 'Vocabulary':
        quiz('practice', words)
    elif practice_mode == 'Sentence practice':
        if corpus:
            st.caption('Translate whole sentences from the uploaded corpus. Alternative translations may exist.')
            quiz('sentences', [True], factory=lambda previous: corpus.question(previous))
        else:
            st.info('Import the sentence corpus to use this mode. See README.md.')
    else:
        tense_col, verb_col = st.columns(2)
        tense_label = tense_col.selectbox('Tense', conjugation.TENSES)
        verb_label = verb_col.selectbox('Verb', ['Surprise me'] + list(conjugation.VERBS))
        tense = 'present' if tense_label == conjugation.TENSES[0] else 'past'
        verb = None if verb_label == 'Surprise me' else verb_label
        st.caption('30 verbs · 6 subject forms · Spain’s vosotros included. Choose the form for the displayed subject.')
        quiz(f'conjugation_{tense}_{verb_label}', [True], factory=lambda previous: conjugation.question(tense, verb, previous))
    st.markdown('<div class="footer-note">LITTLE BY LITTLE &nbsp; / &nbsp; It becomes yours.</div>', unsafe_allow_html=True)
elif page == 'Words':
    library = st.selectbox('Library', ['Vocabulary', 'Sentence library'] if corpus else ['Vocabulary'])
    search = st.text_input('Find a word', placeholder='Search Spanish or English…')
    st.session_state.setdefault('browse_seed', secrets.randbits(64))
    seed = st.session_state['browse_seed']
    if st.button('Shuffle these 100'):
        st.session_state['browse_seed'] = secrets.randbits(64)
        st.rerun()
    categories = ['All categories'] + sorted({w['category'] for w in words})
    x, y = st.columns(2)
    category = x.selectbox('Category', categories)
    flagged = y.checkbox('Only entries needing review')
    found = [w for w in words if (normalized(search) in normalized(w['spanish'] + ' ' + w['english']))
             and (category == 'All categories' or category == w['category'])
             and (not flagged or w['note'].startswith('REVIEW:'))]
    if library == 'Sentence library':
        found = corpus.sample(limit=100, seed=seed, search=search)
        st.caption('Up to 100 sentence pairs · Search covers the full corpus · Categories apply to vocabulary only.')
    else:
        matches = len(found)
        found = random.Random(seed).sample(found, min(100, len(found)))
        st.caption(f'Showing {len(found)} of {matches} matches · Search covers all vocabulary · Refresh for a new sample.')
    st.dataframe([{'Spanish': w['spanish'], 'English': w['english'], 'Category': w['category'],
                   'Type': w.get('pos', ''), 'Source': w['source'], 'Notes': w['note']} for w in found],
                 hide_index=True, width='stretch')
    if found:
        selected = st.selectbox('See a word in context', range(len(found)), format_func=lambda i: found[i]['spanish'])
        example(found[selected])
    st.download_button('Download vocabulary (TSV)', (ROOT / 'data' / 'vocabulary.tsv').read_bytes(),
                       file_name='palabra-vocabulary.tsv', mime='text/tab-separated-values')
    with st.expander('Add your own words'):
        st.write('Edit data/vocabulary.tsv in a text editor or spreadsheet. Add a row with Spanish, English, category, source and note columns, separated by tabs. Save as UTF-8 and reload this page. Use a unique Spanish entry. Start a note with REVIEW: to keep an uncertain word out of quizzes.')
elif page == 'My Mistakes':
    mistakes = progress.mistakes()
    lookup = {w['id']: w for w in words}
    for m in mistakes:
        if m['word'] not in lookup:
            extra = conjugation.resolve(m['word']) if m['word'].startswith('conj:') else corpus.get(m['word']) if corpus else None
            if extra:
                lookup[m['word']] = extra
    active = [lookup[m['word']] for m in mistakes if not m['resolved'] and m['word'] in lookup
              and not lookup[m['word']]['note'].startswith('REVIEW:')]
    st.markdown(f'### {len(active)} words ready for another try')
    st.caption('A correct answer resolves a word; a later mistake puts it back. Your history stays available during this session.')
    review = st.toggle('Review my missed words')
    if review:
        quiz('review', active, factory=lambda previous: review_question(active, previous))
    else:
        if not mistakes:
            st.info('A fresh start. Missed words will appear here after your first quiz mistake.')
        else:
            st.dataframe([{'Spanish': lookup.get(m['word'], {}).get('spanish', m['word']), 'English / form': lookup.get(m['word'], {}).get('english', 'Removed from vocabulary'),
                           'Times missed': m['misses'], 'Successful reviews': m['reviews'],
                           'Status': 'Reviewed' if m['resolved'] else 'Needs practice', 'Last missed (UTC)': m['last_missed']}
                          for m in mistakes], hide_index=True, width='stretch')

if corpus:
    st.caption('Sentence data: Tatoeba contributors via ManyThings.org · CC BY 2.0 FR. Individual credits appear with each example and corpus row. Corpus translations may contain errors.')
