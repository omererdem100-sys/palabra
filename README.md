# ¡Palabra!

**Live demo:** https://palabra.streamlit.app

A Spanish → English vocabulary practice app made with Python and Streamlit, based on seven handwritten Spanish–Turkish vocabulary photos. Warm Spain-inspired red and gold, gentle animation, responsive layouts, and reduced-motion support.

## Run locally

Python **3.12** is recommended (the version used for verification). From this project folder in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Open http://localhost:8501. Stop with Ctrl+C. On macOS/Linux use `.venv/bin/python` instead of `.venv\Scripts\python.exe`. If your default Python is a very new release and package installation fails, install Python 3.12 from python.org and use that executable to create the environment.

On Windows, after setup you can also double-click **start.bat**.

Dependencies must be downloaded once. After installation the app works locally; optional Google Fonts require internet and fall back to system fonts when unavailable.

## What is included

- **Sidebar:** Test, Words, My Mistakes, then direct links to Vocabulary, Sentence practice and Verb conjugation. Practice mode no longer appears as a dropdown on the main screen. Radio circles are visually hidden; keyboard navigation and focus styles are preserved.
- **Test:** three practice choices: Vocabulary, Sentence practice, and Verb conjugation. Four clickable answers reveal green/red with a left-to-right **0.8-second colour fill**. Motion is disabled when the device requests reduced motion.
- **XP and combos:** +10 XP for correct answers, −5 XP for mistakes, and **+15 extra XP on the 3rd, 6th, 9th… consecutive correct answer**. An incorrect answer resets the streak. The streak is shared across practice and review modes within one browser session only. XP can go below zero; levels start at 1 and advance every 100 nonnegative XP. Every new session starts at Level 1 with 0 XP and no mistakes.
- **Words:** 560 vocabulary entries plus a searchable library of **144,215 English–Spanish sentence pairs** (135,392 distinct Spanish sentences). Each library displays at most 100 items, sampled afresh on a new browser session or full page refresh. Widget interactions keep the sample stable; “Shuffle these 100” changes it on demand. Search covers the complete library, not just the displayed sample. Sentence search samples up to 100 from the first 2,000 matching results.
- **Grammar and context:** nouns show articles, adjectives show `adj.`, and vocabulary entries include Spanish/English example sentences. 498 vocabulary examples come from the corpus and 62 are AI-assisted authored usage examples where the exact word or expression was absent. Source credits accompany each example.
- **Verb conjugation:** 30 explicitly stored verbs × six subject forms × Present (Presente) and Past (Pretérito indefinido). Includes vosotros, stem changes, irregular verbs and accent marks. Usted shares the él/ella form; ustedes shares the ellos/ellas form. This small mode does not claim to conjugate every Spanish verb automatically.
- **My Mistakes:** session-only miss counts, last missed time, review practice, and resolved history. A correct answer resolves a word; a later wrong answer reopens it. Review has the same XP rules as Test.
- Session-local answer records and unique question tokens prevent reruns or repeated submissions from awarding XP twice. Questions avoid immediately repeating the previous word when the pool permits.
- Four uncertain entries are marked `REVIEW:` and excluded from quiz prompts and distractors until confirmed.

## Interface

Streamlit’s Deploy button, menu, header and footer are hidden with CSS. Answer buttons have warm borders, shadows, a 2px hover lift and a pressed state; the existing 0.8-second answer fill is retained.

## Edit or add words

Edit **data/vocabulary.tsv** in a text editor or spreadsheet and save it as UTF-8, tab-separated text. Keep the existing columns; the first five are required:

| spanish | english | category | source | note |
|---|---|---|---|---|
| la casa | house | Home | personal | |

Use one row per unique Spanish entry, including accents and articles. `source` can be `personal` for future additions. Begin `note` with `REVIEW:` for uncertain content. Reload the app after edits; existing questions retain their wording until you press Next word. At least four distinct English meanings are required. Distractors exclude overlapping meaning words and a small set of near-synonym families; this is a practical heuristic, not a full semantic language model. Review future additions for synonyms and context before using them in quizzes.

Also fill `pos` (for example `noun · f.`, `adj.`, or `verb`), `example_es`, `example_en`, `example_credit`, and optionally `source_credit`. Use your own checked usage sentence in both languages for new vocabulary. Corpus examples are contextual usages, and may illustrate another sense of a polysemous word. Future conjugation additions belong in `conjugation.py`, with all six forms and an appropriate bilingual context.

Repeated entries from the photos are merged, with all source numbers retained. Related forms such as adjective `dulce` and noun `el dulce` remain separate. See **TRANSCRIPTION.md** for source mapping and decisions. The original photos are in **sources/** for checking.

## Uploaded corpus

The provided **spa-eng.zip contains sentence translations, not 144,000 dictionary headwords**. All 144,215 pairs are stored locally in `data/sentences.sqlite3`, indexed for search and available in Sentence practice and the Sentence library. They are not split into guessed word-to-word translations. Twelve reviewed single-word alignments have been added to the original vocabulary, with noun articles or infinitive forms normalized.

The corpus is from [Tatoeba](https://tatoeba.org) via [ManyThings](https://www.manythings.org/anki/), dated 2026-02-13, licensed [CC BY 2.0 France](https://creativecommons.org/licenses/by/2.0/fr/). Original sentence IDs and contributor names are retained with every pair and shown in the UI. The original supplied notice is preserved in `data/CORPUS_ABOUT.txt`. See **DATA_SOURCES.md**. Corpus translations can contain mistakes and alternate valid renderings; sentence distractors filter similar text but cannot guarantee semantic equivalence detection.

The database is already included, so no import or extra download is necessary. To rebuild from the original ZIP, first rename the existing corpus database as a backup, then run:

```powershell
.\.venv\Scripts\python.exe scripts/import_corpus.py "C:\path\to\spa-eng.zip"
```

The importer reads only the expected text files and retains all pair credits. It also enriches vocabulary examples; back up your custom vocabulary edits before rerunning enrichment.

## Independent sessions — no saved learner data

XP, answer history, combo streaks and mistakes live exclusively in **st.session_state**. Each browser tab/new session starts at **Level 1, 0 XP and an empty mistake list**. Interacting with widgets and switching practice modes reruns the script while retaining that session's progress. A full page refresh, a new tab/session, or a server restart starts fresh; progress is intentionally not permanent. There is no account or cross-device synchronization.

`Progress(st.session_state)` is instantiated for the current session on every script run. It must never be made global or cached. `Progress` accepts a mapping (a plain dict in unit tests) and performs no file or database operations. Independent sessions do not share mutable learner state. Repeated submissions of the same question token cannot score twice within a session.

Old `data/progress.sqlite3` files and the old `PALABRA_DB` setting are **ignored**. No personal progress files are created, loaded, or included in the downloadable project. Existing old files may remain on your computer but have no effect on this version. The only bundled SQLite database is `data/sentences.sqlite3`: shared **read-only learning content**, not user progress. The optional corpus import script writes learning data only when explicitly run.

The repository's `.gitignore` excludes old learner databases and generated archives. Only the static sentence corpus is allowlisted. Displayed mistake timestamps are UTC.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The 17 tests cover vocabulary and source validity, answer choices, uncertain-entry exclusion, non-repetition, XP/combos/reset, session isolation, no learner-file/database access, corpus count/search/attribution, all 360 conjugation prompts, example coverage, the 100-item browser, sidebar navigation, the full learning/review flows across all three practice modes. Core tests use separate plain dictionaries; integration tests use separate Streamlit sessions. They verify new-session defaults and that two live sessions cannot affect each other. The CSS animation duration is additionally checked in the browser.

## Project map

- `app.py`: English Streamlit interface and quiz interaction
- `core.py`: vocabulary validation, question generation, session-local progress
- `corpus.py`: indexed local sentence sampling, search, and attributed examples
- `conjugation.py`: present/preterite practice tables and bilingual contexts
- `scripts/import_corpus.py`: reproducible ZIP importer and vocabulary enrichment
- `assets/style.css`: styling and motion
- `data/vocabulary.tsv`: editable learning content
- `data/sentences.sqlite3`: included 144,215-pair corpus (not learner progress)
- `sources/photo-1.jpeg` … `photo-7.jpeg`: original notebook photos
- `.streamlit/config.toml`: theme and server defaults
- `tests/`: standard-library unit tests and Streamlit AppTest integration tests
- `requirements.txt`: application dependency

## Deploying online

GitHub Pages cannot run Streamlit apps. To publish this app, push the repository to GitHub, then deploy it on [Streamlit Community Cloud](https://share.streamlit.io): choose the repository, branch `main`, main file `app.py`, and Python 3.12 under Advanced settings. Make sure `data/sentences.sqlite3` is committed (it is allowlisted in `.gitignore`).

## About

Created as an AI-assisted learning project: the requirements and vocabulary come from the author's own handwritten notes, and the implementation was generated with AI assistance and then reviewed.

## License

The source code is released under the [MIT License](LICENSE). The sentence corpus in `data/sentences.sqlite3` comes from Tatoeba and remains under [CC BY 2.0 FR](https://creativecommons.org/licenses/by/2.0/fr/); see DATA_SOURCES.md.
