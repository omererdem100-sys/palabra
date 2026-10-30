# Data sources and changes

## Notebook vocabulary

The seven user-provided photos supply the original 548 entries. See TRANSCRIPTION.md. English translations, spelling corrections and categories are AI-assisted editorial work. Noun articles and word-type labels are normalized; el agua and el hambre remain feminine despite taking el before a stressed a. El norte and el sur now include their articles; their historical progress identifiers are preserved.

## Uploaded spa-eng.zip

Imported **144,215 sentence pairs** from `spa.txt`; **135,392 distinct Spanish sentences**. No duplicate pairs were found. Alternate English translations for the same Spanish sentence remain in the library. The data is sentence aligned, not a bilingual headword dictionary. The corpus is searchable and included in sentence practice; twelve clear, reviewed single-word alignments were normalized into dictionary entries, giving 560 vocabulary entries total.

Source: [ManyThings bilingual sentence pairs](https://www.manythings.org/anki/), based on [Tatoeba](https://tatoeba.org). Supplied file date: 2026-02-13. Original notice: `data/CORPUS_ABOUT.txt`.

License: [Creative Commons Attribution 2.0 France](https://creativecommons.org/licenses/by/2.0/fr/). Each imported pair retains the original attribution text, including contributor names and sentence IDs. Those credits are included in corpus rows and example sources in the app. Source sentences themselves are preserved without textual modification. Sampling, indexing, selection as examples, grammatical labels and separate dictionary headword normalization are application additions.

Use Tatoeba sentence IDs in the credit to inspect original sentences at `https://tatoeba.org/en/sentences/show/ID`. The upstream dataset warns that translations may contain errors. It does not guarantee unique English translations, word-level alignments, or part-of-speech annotations.

## Examples and grammar

Every current vocabulary entry has a Spanish/English usage example. Exact-token corpus matches supply 498 examples; 62 entries lacking a suitable match use separately labelled AI-assisted teaching examples in `scripts/import_corpus.py`. Examples can illustrate a contextual sense beyond the primary glossary meaning.

Conjugation practice uses 30 explicitly stored verbs and all six person groups in two indicative tenses (360 prompts). The tables include common irregular, stem-changing and spelling-changing forms; they do not attempt to infer forms for all dictionary verbs. Subject labels group usted with él/ella and ustedes with ellos/ellas; bilingual examples choose él and ellos as representative subjects.

References consulted: [Present indicative forms](https://www.spanishdict.com/guide/spanish-present-tense-forms), [irregular present forms](https://www.spanishdict.com/guide/spanish-irregular-present-tense), and [irregular verb overview](https://www.spanishdict.com/guide/irregular-verbs-in-spanish). The app's teaching examples and conjugation data are separately authored rather than reproduced reference examples.
