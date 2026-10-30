"""A deliberately bounded set of reviewed indicative forms, not guessed rules."""
import random
import uuid

PEOPLE = ['yo', 'tú', 'él / ella / usted', 'nosotros / nosotras', 'vosotros / vosotras', 'ellos / ellas / ustedes']
EN_PEOPLE = ['I', 'You', 'He', 'We', 'You', 'They']
# verb, English base, third person, past, Spanish context, English context,
# six present forms, six preterite forms
ROWS = [
    ('hablar','speak','speaks','spoke','español','Spanish','hablo hablas habla hablamos habláis hablan','hablé hablaste habló hablamos hablasteis hablaron'),
    ('comer','eat','eats','ate','pan','bread','como comes come comemos coméis comen','comí comiste comió comimos comisteis comieron'),
    ('vivir','live','lives','lived','en Madrid','in Madrid','vivo vives vive vivimos vivís viven','viví viviste vivió vivimos vivisteis vivieron'),
    ('ser','be','is','was','estudiante','a student','soy eres es somos sois son','fui fuiste fue fuimos fuisteis fueron'),
    ('estar','be','is','was','en casa','at home','estoy estás está estamos estáis están','estuve estuviste estuvo estuvimos estuvisteis estuvieron'),
    ('ir','go','goes','went','al parque','to the park','voy vas va vamos vais van','fui fuiste fue fuimos fuisteis fueron'),
    ('tener','have','has','had','tiempo','time','tengo tienes tiene tenemos tenéis tienen','tuve tuviste tuvo tuvimos tuvisteis tuvieron'),
    ('hacer','do','does','did','la tarea','the homework','hago haces hace hacemos hacéis hacen','hice hiciste hizo hicimos hicisteis hicieron'),
    ('poder','be able to','is able to','was able to','venir','come','puedo puedes puede podemos podéis pueden','pude pudiste pudo pudimos pudisteis pudieron'),
    ('querer','want','wants','wanted','aprender','to learn','quiero quieres quiere queremos queréis quieren','quise quisiste quiso quisimos quisisteis quisieron'),
    ('poner','put','puts','put','el libro aquí','the book here','pongo pones pone ponemos ponéis ponen','puse pusiste puso pusimos pusisteis pusieron'),
    ('venir','come','comes','came','a clase','to class','vengo vienes viene venimos venís vienen','vine viniste vino vinimos vinisteis vinieron'),
    ('decir','say','says','said','la verdad','the truth','digo dices dice decimos decís dicen','dije dijiste dijo dijimos dijisteis dijeron'),
    ('dar','give','gives','gave','un regalo','a gift','doy das da damos dais dan','di diste dio dimos disteis dieron'),
    ('ver','see','sees','saw','el mar','the sea','veo ves ve vemos veis ven','vi viste vio vimos visteis vieron'),
    ('salir','leave','leaves','left','de casa','home','salgo sales sale salimos salís salen','salí saliste salió salimos salisteis salieron'),
    ('dormir','sleep','sleeps','slept','bien','well','duermo duermes duerme dormimos dormís duermen','dormí dormiste durmió dormimos dormisteis durmieron'),
    ('pedir','ask','asks','asked','ayuda','for help','pido pides pide pedimos pedís piden','pedí pediste pidió pedimos pedisteis pidieron'),
    ('leer','read','reads','read','el periódico','the newspaper','leo lees lee leemos leéis leen','leí leíste leyó leímos leísteis leyeron'),
    ('escribir','write','writes','wrote','una carta','a letter','escribo escribes escribe escribimos escribís escriben','escribí escribiste escribió escribimos escribisteis escribieron'),
    ('comprar','buy','buys','bought','fruta','fruit','compro compras compra compramos compráis compran','compré compraste compró compramos comprasteis compraron'),
    ('estudiar','study','studies','studied','español','Spanish','estudio estudias estudia estudiamos estudiáis estudian','estudié estudiaste estudió estudiamos estudiasteis estudiaron'),
    ('trabajar','work','works','worked','en Madrid','in Madrid','trabajo trabajas trabaja trabajamos trabajáis trabajan','trabajé trabajaste trabajó trabajamos trabajasteis trabajaron'),
    ('jugar','play','plays','played','al tenis','tennis','juego juegas juega jugamos jugáis juegan','jugué jugaste jugó jugamos jugasteis jugaron'),
    ('buscar','look','looks','looked','el libro','for the book','busco buscas busca buscamos buscáis buscan','busqué buscaste buscó buscamos buscasteis buscaron'),
    ('llegar','arrive','arrives','arrived','temprano','early','llego llegas llega llegamos llegáis llegan','llegué llegaste llegó llegamos llegasteis llegaron'),
    ('empezar','start','starts','started','la clase','the class','empiezo empiezas empieza empezamos empezáis empiezan','empecé empezaste empezó empezamos empezasteis empezaron'),
    ('sentir','feel','feels','felt','alegría','joy','siento sientes siente sentimos sentís sienten','sentí sentiste sintió sentimos sentisteis sintieron'),
    ('traer','bring','brings','brought','agua','water','traigo traes trae traemos traéis traen','traje trajiste trajo trajimos trajisteis trajeron'),
    ('oír','hear','hears','heard','música','music','oigo oyes oye oímos oís oyen','oí oíste oyó oímos oísteis oyeron'),
]
VERBS = {row[0]: row for row in ROWS}
TENSES = ['Present (Presente)', 'Past (Pretérito indefinido)']


def entry(verb, tense, person):
    row = VERBS[verb]
    present = tense == 'present'
    form = row[6 if present else 7].split()[person]
    subject = ['Yo', 'Tú', 'Él', 'Nosotros', 'Vosotros', 'Ellos'][person]
    es_context = row[4]
    en_context = row[5]
    if verb == 'ser' and person >= 3:
        es_context, en_context = 'estudiantes', 'students'
    if row[1] in ('be', 'be able to'):
        be = (['am','are','is','are','are','are'] if present else ['was','were','was','were','were','were'])[person]
        en_form = be + (' able to' if verb == 'poder' else '')
    else:
        en_form = row[2] if present and person == 2 else row[1] if present else row[3]
    label = 'Presente' if present else 'Pretérito indefinido'
    return {'id': f'conj:{verb}:{tense}:{person}',
            'spanish': f'{PEOPLE[person]} · {verb}', 'english': form,
            'category': 'Conjugation', 'pos': f'verb · {label}', 'source': 'Reviewed conjugation table',
            'note': 'Usted uses the él/ella form; ustedes uses the ellos/ellas form. Vosotros is used in Spain.',
            'example_es': f'{subject} {form} {es_context}.',
            'example_en': f'{EN_PEOPLE[person]} {en_form} {en_context}.',
            'example_credit': 'AI-assisted teaching example', 'verb': verb, 'tense': tense, 'person': person}


def resolve(entry_id):
    try:
        prefix, verb, tense, person = entry_id.split(':')
        if prefix != 'conj' or tense not in ('present','past') or not 0 <= int(person) < 6:
            return None
        return entry(verb, tense, int(person))
    except (ValueError, KeyError):
        return None


def question(tense='present', verb=None, previous=None, rng=None, person=None):
    rng = rng or random
    choices = [entry(v, tense, p) for v in ([verb] if verb else VERBS) for p in ([person] if person is not None else range(6))]
    chosen = rng.choice([w for w in choices if w['id'] != previous] or choices)
    row = VERBS[chosen['verb']]
    forms = set(row[6 if tense == 'present' else 7].split()) - {chosen['english']}
    options = rng.sample(sorted(forms), 3) + [chosen['english']]
    rng.shuffle(options)
    return {'token': str(uuid.uuid4()), 'word': chosen, 'options': options}
