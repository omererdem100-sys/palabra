"""Import the user's ManyThings/Tatoeba ZIP, retaining per-pair attribution.

Usage: python scripts/import_corpus.py path/to/spa-eng.zip
Reads only spa.txt and _about.txt. Does not execute or extract ZIP content.
"""
import csv
import re
import sqlite3
import sys
from pathlib import Path
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import ROOT
from corpus import Corpus


def main(archive):
    path = ROOT / 'data' / 'sentences.sqlite3'
    if path.exists():
        raise SystemExit('Corpus already exists. Rename it before rebuilding.')
    with ZipFile(archive) as z:
        lines = z.read('spa.txt').decode('utf-8-sig').splitlines()
        (ROOT / 'data' / 'CORPUS_ABOUT.txt').write_bytes(z.read('_about.txt'))
    rows = []
    seen = set()
    for number, line in enumerate(lines, 1):
        fields = line.split('\t', 2)
        if len(fields) != 3 or not all(fields):
            raise ValueError(f'Malformed sentence row {number}')
        english, spanish, credit = fields
        if (spanish, english) not in seen:
            rows.append((spanish, english, credit))
            seen.add((spanish, english))
    with sqlite3.connect(path) as db:
        db.executescript('''
            CREATE TABLE sentences(id INTEGER PRIMARY KEY, spanish TEXT NOT NULL,
                english TEXT NOT NULL, credit TEXT NOT NULL);
            CREATE INDEX sentence_spanish ON sentences(spanish);
            CREATE VIRTUAL TABLE sentences_fts USING fts5(spanish,english,
                content='sentences',content_rowid='id',tokenize='unicode61 remove_diacritics 2');
        ''')
        db.executemany('INSERT INTO sentences(spanish,english,credit) VALUES(?,?,?)', rows)
        db.execute("INSERT INTO sentences_fts(sentences_fts) VALUES('rebuild')")
    print(f'Imported {len(rows):,} unique pairs from {len(lines):,} rows.')
    enrich_vocabulary()


# Reviewed single-word alignments. Imperatives such as Ve = Go are deliberately
# not imported as infinitive vocabulary. Corpus provenance is added below.
ADDITIONS = [
    ('hola', 'hello', 'Expressions', 'interj.'),
    ('gracias', 'thank you', 'Expressions', 'interj.'),
    ('el fuego', 'fire', 'Nature', 'noun · m.'),
    ('el incendio', 'fire / blaze', 'Everyday', 'noun · m.'),
    ('la ayuda', 'help', 'Everyday', 'noun · f.'),
    ('el auxilio', 'assistance / help', 'Everyday', 'noun · m.'),
    ('exhalar', 'to exhale', 'Verbs', 'verb'),
    ('inhalar', 'to inhale', 'Verbs', 'verb'),
    ('genial', 'great / brilliant', 'Descriptions', 'adj.'),
    ('fantástico', 'fantastic', 'Descriptions', 'adj.'),
    ('ridículo', 'ridiculous', 'Descriptions', 'adj.'),
    ('felicidades', 'congratulations', 'Expressions', 'interj.'),
]

AUTHORED = {
    'la uva': ('Esta uva es dulce.', 'This grape is sweet.'),
    'la fresa': ('La fresa está en el plato.', 'The strawberry is on the plate.'),
    'la zanahoria': ('Corto la zanahoria para la sopa.', 'I cut the carrot for the soup.'),
    'la nata': ('Añade la nata al café.', 'Add the cream to the coffee.'),
    'la ternera': ('Hoy comemos ternera con arroz.', 'Today we are eating veal with rice.'),
    'las fritas': ('Las fritas están calientes.', 'The fries are hot.'),
    'la mostaza': ('Me gusta la mostaza en el bocadillo.', 'I like mustard in the sandwich.'),
    'el pan tostado': ('Como pan tostado con mantequilla.', 'I eat toast with butter.'),
    'el mozo': ('El mozo trae la cuenta.', 'The waiter brings the bill.'),
    'la propina': ('Dejamos una propina al camarero.', 'We leave a tip for the waiter.'),
    'la servilleta': ('La servilleta está junto al plato.', 'The napkin is next to the plate.'),
    'el oficio': ('Aprendió el oficio de carpintero.', 'He learned the trade of carpentry.'),
    'la sábana': ('La sábana está limpia.', 'The bedsheet is clean.'),
    'la época': ('Fue una época de grandes cambios.', 'It was a period of great changes.'),
    'estupendo': ('El viaje fue estupendo.', 'The trip was wonderful.'),
    'la alcoba': ('La alcoba tiene una ventana.', 'The bedroom has a window.'),
    'grueso': ('Este libro es muy grueso.', 'This book is very thick.'),
    'amplio': ('El apartamento es amplio.', 'The apartment is spacious.'),
    'antiguo': ('Este edificio es muy antiguo.', 'This building is very old.'),
    'servir': ('Voy a servir la cena.', 'I am going to serve dinner.'),
    'marcar': ('Debes marcar el número correcto.', 'You must dial the correct number.'),
    'peligrar': ('Su vida puede peligrar.', 'His life may be in danger.'),
    'pisar': ('No debes pisar el césped.', 'You must not step on the grass.'),
    'suponer': ('No debemos suponer que todo está bien.', 'We must not suppose that everything is fine.'),
    'fino': ('Este tejido es muy fino.', 'This fabric is very fine.'),
    'el avión': ('El avión llega a las diez.', 'The aeroplane arrives at ten.'),
    'cómico': ('El personaje es cómico.', 'The character is comical.'),
    'el cine': ('Vamos al cine esta tarde.', 'We are going to the cinema this afternoon.'),
    'acordar': ('Debemos acordar una fecha.', 'We must agree on a date.'),
    'bañar': ('Voy a bañar al perro.', 'I am going to bathe the dog.'),
    'callar': ('No puedes callar a todo el mundo.', 'You cannot silence everyone.'),
    'desear': ('Es normal desear una vida tranquila.', 'It is normal to wish for a quiet life.'),
    'disculpar': ('Espero que puedas disculpar mi error.', 'I hope you can excuse my mistake.'),
    'divertir': ('El payaso quiere divertir a los niños.', 'The clown wants to entertain the children.'),
    'el hambre': ('El hambre afecta a muchas personas.', 'Hunger affects many people.'),
    'la gana': ('No me da la gana de salir.', 'I do not feel like going out.'),
    'el auxilio': ('Pidió el auxilio de un médico.', 'He asked for a doctor’s help.'),
    'las tapas': ('Pedimos unas tapas para compartir.', 'We ordered some tapas to share.'),
    'la cereza': ('La cereza está madura.', 'The cherry is ripe.'),
    'la ciruela': ('Esta ciruela es muy dulce.', 'This plum is very sweet.'),
    'la judía': ('La judía es una legumbre.', 'The bean is a legume.'),
    'la mazorca': ('Comemos una mazorca de maíz.', 'We are eating an ear of corn.'),
    'el champiñón': ('Corto el champiñón con un cuchillo.', 'I cut the button mushroom with a knife.'),
    'el guisante': ('El guisante es pequeño y verde.', 'The pea is small and green.'),
    'la patata': ('La patata está en la cocina.', 'The potato is in the kitchen.'),
    'la tortilla': ('Preparo una tortilla de patatas.', 'I am making a Spanish potato omelette.'),
    'es otro cuento': ('Eso es otro cuento.', 'That is another story.'),
    'estar ubicado': ('El hotel debe estar ubicado cerca del centro.', 'The hotel must be located near the centre.'),
    'ser seguro': ('Este puente debe ser seguro.', 'This bridge must be safe.'),
    'tomar asiento': ('Puede tomar asiento aquí.', 'You may take a seat here.'),
    'gozar': ('Todos tienen derecho a gozar de buena salud.', 'Everyone has the right to enjoy good health.'),
    'manchar': ('No quiero manchar la camisa.', 'I do not want to stain the shirt.'),
    'penar': ('La ley puede penar ese delito con una multa.', 'The law can punish that offence with a fine.'),
    'preferir': ('Es normal preferir una opción más fácil.', 'It is normal to prefer an easier option.'),
    'valer': ('Este cuadro puede valer mucho dinero.', 'This painting may be worth a lot of money.'),
    'estrenar': ('Hoy voy a estrenar mis zapatos nuevos.', 'Today I am going to wear my new shoes for the first time.'),
    'trabajoso': ('Es un proceso lento y trabajoso.', 'It is a slow and laborious process.'),
    'menos mal': ('Menos mal que llegaste a tiempo.', 'Thank goodness you arrived on time.'),
    'la legumbre': ('La lenteja es una legumbre.', 'The lentil is a pulse.'),
    'el gabán': ('Me pongo el gabán antes de salir.', 'I put on my overcoat before going out.'),
    'exhalar': ('Debes exhalar lentamente.', 'You should exhale slowly.'),
    'inhalar': ('Es importante inhalar aire limpio.', 'It is important to inhale clean air.'),
}


def enrich_vocabulary():
    corpus = Corpus()
    path = ROOT / 'data' / 'vocabulary.tsv'
    with path.open(encoding='utf-8', newline='') as f:
        words = list(csv.DictReader(f, delimiter='\t'))
    existing = {w['spanish'] for w in words}
    for spanish, english, category, pos in ADDITIONS:
        if spanish not in existing:
            bare = re.sub(r'^(el|la) ', '', spanish)
            matches = corpus.sample(search=bare, limit=1)
            words.append(dict(spanish=spanish, english=english, category=category,
                              source='ZIP', note='Reviewed single-word corpus alignment; dictionary form normalized.',
                              pos=pos, source_credit=matches[0]['source'] if matches else 'Tatoeba / ManyThings'))
    missing = []
    for word in words:
        word.setdefault('source_credit', '')
        if word['spanish'] in ('norte', 'sur'):
            word['spanish'] = 'el ' + word['spanish']
        spanish = word['spanish']
        if not word.get('pos'):
            if spanish.startswith(('el ', 'los ')):
                word['pos'] = 'noun · f.' if spanish in ('el agua', 'el hambre') else 'noun · m.'
            elif spanish.startswith(('la ', 'las ')):
                word['pos'] = 'noun · f.'
            elif word['category'] == 'Descriptions':
                word['pos'] = 'adj.'
            elif word['category'] == 'Verbs':
                word['pos'] = 'verb'
            else:
                word['pos'] = 'expression'
        word['pos'] = {
            'el azúcar': 'noun · m./f.', 'mejor': 'adj. / adv.',
            'primero': 'adj. / adv.', 'todo': 'pron. / adj.',
            'tal': 'det. / pron.', 'bastante': 'adv. / det.',
            'demasiado': 'adv. / adj.', 'nunca': 'adv.', 'ya': 'adv.',
            'todavía': 'adv.', 'después': 'adv.', 'nadie': 'pron.',
            'aquí': 'adv.', 'acá': 'adv.', 'allí': 'adv.', 'allá': 'adv.',
            'lentamente': 'adv.', 'afortunadamente': 'adv.', 'completamente': 'adv.',
            'el norte': 'noun · m.', 'el sur': 'noun · m.'
        }.get(spanish, word['pos'])
        example = corpus.example(spanish, word['english'], word['pos'])
        if example:
            word['example_es'], word['example_en'], word['example_credit'] = example
        else:
            missing.append(spanish)
            # A safe, transparent bilingual teaching frame where no exact-token
            # corpus example exists. Replaced with authored usage below.
            word['example_es'] = f'La expresión «{spanish}» aparece en mis apuntes.'
            word['example_en'] = f'The expression “{spanish}” appears in my notes.'
            word['example_credit'] = 'AI-assisted teaching example (not from the corpus)'
            if spanish in AUTHORED:
                word['example_es'], word['example_en'] = AUTHORED[spanish]
    fields = ['spanish', 'english', 'category', 'source', 'note', 'pos',
              'example_es', 'example_en', 'example_credit', 'source_credit']
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fields, delimiter='\t')
        writer.writeheader()
        writer.writerows(words)
    print('No exact corpus usage:', repr(missing))
    print('Vocabulary entries:', len(words))


if __name__ == '__main__':
    main(sys.argv[1])
