#!/usr/bin/env python3
"""Generuje stronę profilową dla każdego artysty z _data/artists.json.

    python3 build.py           # same strony profilowe + lista ekipy w index.html
    python3 build.py --sync    # najpierw pobiera dane artystów z panelu InkRoute

Dane biograficzne pochodzą wyłącznie z ankiety artysty. Artyści bez ankiety
dostają stronę z nazwiskiem i pracami, bez wymyślonego opisu.

--sync ciągnie z panelu wyłącznie pola publiczne (kraj, miasto, style, języki,
Instagram, staż). Telefony, e-maile, daty urodzenia i notatki menedżera zostają
w panelu — na stronę nie trafiają. Do repozytorium dopisuje tylko tych artystów,
których już znamy: nowy człowiek bez zdjęć dałby połamane kafelki.
"""
import argparse
import html
import shutil
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.request

DATA_PATH = '_data/artists.json'
FACTS_PATH = '_data/public-facts.json'
INDEX_PATH = 'index.html'

# Adres panelu. Nadpisywalny zmienną środowiskową, żeby dało się celować w localhost.
PANEL_URL = os.environ.get('INKROUTE_URL', 'https://inkroute-q2pp.onrender.com')

# Ankiety zawierają dane osobowe i leżą poza repozytorium (.gitignore), więc
# w CI tego pliku po prostu nie ma. To nie jest awaria: panel jest źródłem
# prawdy, a zdjęcia leżą w repo — z tego da się zbudować całą stronę.
DATA = json.load(open(DATA_PATH, encoding='utf-8')) if os.path.exists(DATA_PATH) else []
DATA.sort(key=lambda a: a['name'].lower())

# Publiczny wyciąg z ankiet: style, rok startu, języki, miasto, Instagram.
# Panel jest źródłem prawdy, ale nie wie wszystkiego — czego nie poda, bierzemy
# stąd. Bez tego automatyczny build w CI kasowałby ze stron dane, których nigdzie
# indziej nie ma, łącznie z linkami do Instagrama.
FACTS = json.load(open(FACTS_PATH, encoding='utf-8')) if os.path.exists(FACTS_PATH) else {}


def apply_facts(entry):
    """Uzupełnia puste pola artysty wyciągiem z ankiet. Nie nadpisuje panelu."""
    for key, value in FACTS.get(entry['slug'], {}).items():
        if entry.get(key) in (None, '', []) and value not in (None, '', []):
            entry[key] = value
    return entry

# Kolejność jest kolejnością przycisków na stronie: EN, DE, FR, PL, RU, UA.
LANGS = ('en', 'de', 'fr', 'pl', 'ru', 'ua')

L = {
    'pl': {
        'eyebrow': 'Artysta', 'works': 'Prace', 'styles': 'Style', 'since': 'Tatuuje od',
        'city': 'Baza', 'langs': 'Języki', 'ig': 'Instagram', 'book': 'Umów się',
        'crew': 'Cała ekipa', 'prev': 'Poprzedni', 'next': 'Następny',
        'soon': 'Opis tego artysty przygotowujemy. Prace poniżej mówią za siebie, a termin ustalimy przez Instagram albo telefon.',
        'calc': 'Wycena', 'back': 'Wróć na stronę główną', 'years': 'lat w zawodzie',
    },
    'en': {
        'eyebrow': 'Artist', 'works': 'Work', 'styles': 'Styles', 'since': 'Tattooing since',
        'city': 'Based in', 'langs': 'Languages', 'ig': 'Instagram', 'book': 'Book a session',
        'crew': 'The whole crew', 'prev': 'Previous', 'next': 'Next',
        'soon': 'We are still writing this profile. The work below speaks for itself, and we can set a date over Instagram or by phone.',
        'calc': 'Quote', 'back': 'Back to the main page', 'years': 'years in the trade',
    },
    'ua': {
        'eyebrow': 'Майстер', 'works': 'Роботи', 'styles': 'Стилі', 'since': 'Татуює з',
        'city': 'База', 'langs': 'Мови', 'ig': 'Instagram', 'book': 'Записатись',
        'crew': 'Уся команда', 'prev': 'Попередній', 'next': 'Наступний',
        'soon': 'Опис цього майстра ще готуємо. Роботи нижче говорять самі за себе, а дату узгодимо в Instagram або телефоном.',
        'calc': 'Оцінка', 'back': 'На головну', 'years': 'років у професії',
    },
    'de': {
        'eyebrow': 'Künstler', 'works': 'Arbeiten', 'styles': 'Stile', 'since': 'Tätowiert seit',
        'city': 'Basis', 'langs': 'Sprachen', 'ig': 'Instagram', 'book': 'Termin buchen',
        'crew': 'Das ganze Team', 'prev': 'Zurück', 'next': 'Weiter',
        'soon': 'Dieses Profil schreiben wir noch. Die Arbeiten unten sprechen für sich, einen Termin machen wir über Instagram oder telefonisch aus.',
        'calc': 'Preis', 'back': 'Zurück zur Startseite', 'years': 'Jahre im Beruf',
    },
    'fr': {
        'eyebrow': 'Artiste', 'works': 'Travaux', 'styles': 'Styles', 'since': 'Tatoue depuis',
        'city': 'Base', 'langs': 'Langues', 'ig': 'Instagram', 'book': 'Prendre rendez-vous',
        'crew': 'Toute l’équipe', 'prev': 'Précédent', 'next': 'Suivant',
        'soon': 'Nous écrivons encore ce profil. Les travaux ci-dessous parlent d’eux-mêmes, et on fixera une date sur Instagram ou par téléphone.',
        'calc': 'Devis', 'back': 'Retour à l’accueil', 'years': 'ans de métier',
    },
    'ru': {
        'eyebrow': 'Мастер', 'works': 'Работы', 'styles': 'Стили', 'since': 'Бьёт с',
        'city': 'База', 'langs': 'Языки', 'ig': 'Instagram', 'book': 'Записаться',
        'crew': 'Вся команда', 'prev': 'Предыдущий', 'next': 'Следующий',
        'soon': 'Описание этого мастера ещё готовим. Работы ниже говорят сами за себя, а дату согласуем в Instagram или по телефону.',
        'calc': 'Оценка', 'back': 'На главную', 'years': 'лет в профессии',
    },
}

CURRENT_YEAR = 2026

# Nazwy stylów są międzynarodowe, więc ujednolicamy je niezależnie od języka ankiety.
STYLE_MAP = {
    'Реализм': 'Realism',
    'Графика': 'Graphic',
    'Реалистик графика': 'Realistic graphic',
    'Black work': 'Blackwork',
}


def esc(v):
    return html.escape(str(v), quote=True)


def facts_rows(a):
    """Only rows backed by the questionnaire. No invented content."""
    rows = []
    if a.get('styles'):
        rows.append(('styles', ', '.join(STYLE_MAP.get(x, x) for x in a['styles'])))
    if a.get('since'):
        years = CURRENT_YEAR - int(a['since'])
        rows.append(('since', f"{a['since']}|{years}"))
    where = ', '.join(x for x in (a.get('city'), a.get('country')) if x)
    if where:
        rows.append(('city', where))
    if a.get('langs'):
        rows.append(('langs', ' / '.join(a['langs'])))
    return rows


def page(a, prev, nxt):
    slug = a['slug']
    name = esc(a['name'])
    rows = facts_rows(a)

    dl = []
    for key, val in rows:
        if key == 'since':
            year, years = val.split('|')
            value_html = (f'<span class="mono">{year}</span> '
                          f'<small><span class="mono">{years}</span> '
                          f'<span data-i18n="years">{esc(L["pl"]["years"])}</span></small>')
        else:
            value_html = esc(val)
        dl.append(f'      <dt data-i18n="{key}">{esc(L["pl"][key])}</dt>\n'
                  f'      <dd>{value_html}</dd>')
    facts = ('    <dl class="facts">\n' + '\n'.join(dl) + '\n    </dl>')  if dl else \
            f'    <p class="lead prof-soon" data-i18n="soon">{esc(L["pl"]["soon"])}</p>'

    ig = ''
    if a.get('ig'):
        h = esc(a['ig'])
        ig = (f'\n        <a class="btn btn-ghost" href="https://www.instagram.com/{h}/" '
              f'target="_blank" rel="noopener">'
              f'<i class="ph ph-instagram-logo" aria-hidden="true"></i>@{h}</a>')

    nick = f'\n      <p class="prof-nick mono">{esc(a["nick"])}</p>' if a.get('nick') else ''

    tiles = '\n'.join(
        f'        <figure class="tile" role="button" tabindex="0" data-idx="{i-1}">'
        f'<img loading="lazy" decoding="async" src="assets/artists/{slug}/work{i}.jpg" '
        f'alt="Tatuaż, autor {name}"></figure>'
        for i in (1, 2, 3))

    labels = json.dumps({k: L[k] for k in LANGS}, ensure_ascii=False)

    return f'''<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} | BRO TO BRO Tattoo Art Studio Szczecin</title>
<meta name="description" content="{name} - artysta w studiu BRO TO BRO w Szczecinie. Prace, style i zapisy.">
<meta name="theme-color" content="#0b0b0c">
<meta property="og:title" content="{name} | BRO TO BRO Tattoo">
<meta property="og:image" content="assets/artists/{slug}/profile.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,300..900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css">
<link rel="stylesheet" href="assets/site.css">
<link rel="icon" href="assets/logo-mark.png">
</head>
<body>
<div class="grain" aria-hidden="true"></div>

<header class="topbar stuck">
  <div class="shell">
    <a class="brand" href="index.html" aria-label="BRO TO BRO Tattoo Art Studio">
      <img src="assets/logo-mark.png" alt="" width="606" height="616">
      <span>Bro to Bro<small>TATTOO ART STUDIO</small></span>
    </a>
    <nav class="navlinks prof-links">
      <a href="index.html#artysci" data-i18n="crew">{esc(L['pl']['crew'])}</a>
      <a href="index.html#kalkulator" data-i18n="calc">{esc(L['pl']['calc'])}</a>
      <a href="index.html#zapisy" data-i18n="book">{esc(L['pl']['book'])}</a>
    </nav>
    <div class="navtools">
      <div class="lang" role="group" aria-label="Language">
        <button type="button" data-lang="en" aria-pressed="false">EN</button>
        <button type="button" data-lang="de" aria-pressed="false">DE</button>
        <button type="button" data-lang="fr" aria-pressed="false">FR</button>
        <button type="button" data-lang="pl" aria-pressed="true">PL</button>
        <button type="button" data-lang="ru" aria-pressed="false">RU</button>
        <button type="button" data-lang="ua" aria-pressed="false">UA</button>
      </div>
    </div>
  </div>
</header>

<main>
<section class="prof">
  <div class="shell prof-grid">
    <figure class="prof-photo">
      <img src="assets/artists/{slug}/profile.jpg" alt="{name}" width="720" height="720" fetchpriority="high">
    </figure>
    <div class="prof-info">
      <p class="eyebrow" data-i18n="eyebrow">{esc(L['pl']['eyebrow'])}</p>
      <h1 class="display">{name}</h1>{nick}
{facts}
      <div class="prof-cta">
        <a class="btn btn-primary" href="index.html#zapisy"><i class="ph ph-paper-plane-tilt" aria-hidden="true"></i><span data-i18n="book">{esc(L['pl']['book'])}</span></a>{ig}
      </div>
    </div>
  </div>
</section>

<section class="prof-works">
  <div class="shell">
    <h2 class="display" data-i18n="works">{esc(L['pl']['works'])}</h2>
    <div class="gal prof-gal" id="gal">
{tiles}
    </div>

    <nav class="prof-nav">
      <a class="btn btn-ghost btn-sm" href="artysta-{prev['slug']}.html"><i class="ph ph-arrow-left" aria-hidden="true"></i>{esc(prev['name'])}</a>
      <a class="btn btn-ghost btn-sm" href="index.html#artysci" data-i18n="crew">{esc(L['pl']['crew'])}</a>
      <a class="btn btn-ghost btn-sm" href="artysta-{nxt['slug']}.html">{esc(nxt['name'])}<i class="ph ph-arrow-right" aria-hidden="true"></i></a>
    </nav>
  </div>
</section>

<div class="lb" id="lb" hidden role="dialog" aria-modal="true" aria-label="Podgląd pracy">
  <button class="lb-close" id="lbClose" aria-label="Zamknij"><i class="ph ph-x" aria-hidden="true"></i></button>
  <button class="lb-nav lb-prev" id="lbPrev" aria-label="Poprzednia"><i class="ph ph-caret-left" aria-hidden="true"></i></button>
  <figure class="lb-fig">
    <img id="lbImg" alt="" src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==">
    <figcaption id="lbCap"></figcaption>
  </figure>
  <button class="lb-nav lb-next" id="lbNext" aria-label="Następna"><i class="ph ph-caret-right" aria-hidden="true"></i></button>
</div>
</main>

<footer>
  <div class="shell">
    <div class="foot-brand">
      <img src="assets/logo-wordmark.png" alt="Bro to Bro Tattoo Art Studio" width="630" height="218" loading="lazy">
      <p><a href="index.html" data-i18n="back">{esc(L['pl']['back'])}</a></p>
    </div>
    <div class="foot-social">
      <a href="https://www.instagram.com/brotobrotattoo/" target="_blank" rel="noopener" aria-label="Instagram"><i class="ph ph-instagram-logo" aria-hidden="true"></i></a>
      <a href="tel:+48579128368" aria-label="Telefon"><i class="ph ph-phone" aria-hidden="true"></i></a>
    </div>
  </div>
</footer>

<script>
(function(){{
'use strict';
const L = {labels};
const NAME = {json.dumps(a['name'], ensure_ascii=False)};
const SRC = [1,2,3].map(function(i){{ return 'assets/artists/{slug}/work'+i+'.jpg'; }});

function applyLang(lang){{
  if(!L[lang]) lang='pl';
  document.documentElement.lang = lang === 'ua' ? 'uk' : lang;
  document.querySelectorAll('[data-i18n]').forEach(function(el){{
    const v = L[lang][el.getAttribute('data-i18n')];
    if(v) el.textContent = v;
  }});
  document.querySelectorAll('.lang button').forEach(function(b){{
    b.setAttribute('aria-pressed', String(b.dataset.lang === lang));
  }});
  try{{ localStorage.setItem('b2b-lang', lang); }}catch(e){{}}
}}
document.querySelectorAll('.lang button').forEach(function(b){{
  b.addEventListener('click', function(){{ applyLang(b.dataset.lang); }});
}});
let saved='pl';
try{{ saved = localStorage.getItem('b2b-lang') || 'pl'; }}catch(e){{}}
applyLang(saved);

/* lightbox */
const lb=document.getElementById('lb'), img=document.getElementById('lbImg'), cap=document.getElementById('lbCap');
let idx=0, opener=null;
function show(i){{
  idx=(i+SRC.length)%SRC.length;
  img.src=SRC[idx]; img.alt=NAME;
  cap.innerHTML='<b>'+NAME+'</b> &nbsp; '+(idx+1)+' / '+SRC.length;
}}
function open(i,el){{ opener=el; lb.hidden=false; document.body.style.overflow='hidden'; show(i); document.getElementById('lbClose').focus(); }}
function close(){{ lb.hidden=true; document.body.style.overflow=''; if(opener) opener.focus(); }}
document.getElementById('gal').addEventListener('click', function(e){{
  const f=e.target.closest('.tile'); if(f) open(+f.dataset.idx, f);
}});
document.getElementById('gal').addEventListener('keydown', function(e){{
  const f=e.target.closest('.tile'); if(!f) return;
  if(e.key==='Enter'||e.key===' '){{ e.preventDefault(); open(+f.dataset.idx, f); }}
}});
document.getElementById('lbClose').addEventListener('click', close);
document.getElementById('lbPrev').addEventListener('click', function(){{ show(idx-1); }});
document.getElementById('lbNext').addEventListener('click', function(){{ show(idx+1); }});
lb.addEventListener('click', function(e){{ if(e.target===lb) close(); }});
document.addEventListener('keydown', function(e){{
  if(lb.hidden) return;
  if(e.key==='Escape') close();
  else if(e.key==='ArrowLeft') show(idx-1);
  else if(e.key==='ArrowRight') show(idx+1);
}});
}})();
</script>
</body>
</html>
'''


def norm_name(value):
    """Klucz dopasowania: bez znaków diakrytycznych, bez interpunkcji, bez wielkości liter."""
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()


def name_tokens(value):
    return set(norm_name(value).split())


def same_person(panel_tokens, site_tokens):
    """
    Dopasowanie po tokenach, nie po całym łańcuchu: w repozytorium artyści bywają
    zapisani razem z pseudonimem („MAKSIM BANADYSEU MaxMarker"), a panel trzyma
    imię i nazwisko osobno. Porównanie całych napisów takich osób nie łączy.

    Wymagane są **co najmniej dwa wspólne tokeny** i pełne zawieranie jednego
    zbioru w drugim. Słabsze dopasowanie już raz podłączyło cudzą ankietę
    (Maksym Sysoniuk dostał ankietę MAKSIMA BANADYSEU), a samo nazwisko nie
    wystarcza: w składzie są Nikita i Stanislav Miasnykov.
    """
    if len(panel_tokens) < 2 or len(site_tokens) < 2:
        return False
    return panel_tokens <= site_tokens or site_tokens <= panel_tokens


def fetch_panel_artists():
    url = PANEL_URL.rstrip('/') + '/api/public/artists'
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    # Panel na darmowym planie zasypia; zimny start potrafi zająć pół minuty.
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode('utf-8'))


def sync_from_panel(dry_run=False):
    """Wciąga publiczne pola z panelu do _data/artists.json. Zwraca liczbę zmian."""
    try:
        payload = fetch_panel_artists()
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        print(f'Nie udało się pobrać danych z panelu ({exc}). Buduję ze starych danych.')
        return None

    remote = payload.get('items', [])
    for r in remote:
        full = ' '.join(x for x in (r.get('firstName'), r.get('lastName')) if x)
        r['_tokens'] = name_tokens(full)

    changed, matched = 0, set()
    for a in DATA:
        site_tokens = name_tokens(a['name'])
        hits = [r for r in remote if same_person(r['_tokens'], site_tokens)]
        # Dwuznaczność zostawiamy człowiekowi: lepiej nie dopasować niż podłączyć cudze dane.
        if len(hits) != 1:
            if len(hits) > 1:
                names = ', '.join(' '.join(x for x in (h.get('firstName'), h.get('lastName')) if x) for h in hits)
                print(f'  Niejednoznaczne dopasowanie dla „{a["name"]}": {names} — pomijam')
            continue
        r = hits[0]
        matched.add(id(r))
        # Zdjęcia dociągamy tylko brakujące: te, które już leżą w repo, zostają.
        pull_photos(a, r)
        apply_facts(a)

        # Imię też bierzemy z panelu. Bez tego build lokalny (z ankietami, gdzie
        # nazwiska bywają KAPSEM) i build w CI (tylko panel) dawałyby inne pliki
        # i przepisywałyby się nawzajem w nieskończoność.
        pname = ' '.join(x for x in (r.get('firstName'), r.get('lastName')) if x).strip()
        pnick = (r.get('nickname') or '').strip()
        display = f'{pname} {pnick}'.strip() if pnick and a['slug'] != slugify(pname) else pname
        if display and a['name'] != display:
            print(f'  {a["name"]}: name: -> {display!r}')
            if not dry_run:
                a['name'] = display
            changed += 1
        # Nadpisujemy tylko to, co panel faktycznie wie — pusta wartość nie kasuje ankiety.
        fields = {
            'country': r.get('country'),
            'countryCode': r.get('countryCode'),
            'city': r.get('city'),
            'ig': (r.get('instagram') or '').lstrip('@') or None,
            'since': r.get('startedYear'),
            'styles': r.get('styles') or None,
            'langs': [x.upper() for x in (r.get('languages') or [])] or None,
        }
        for key, value in fields.items():
            if value in (None, '', []):
                continue
            old = a.get(key)
            if old == value:
                continue
            # Nadpisania pokazujemy zawsze. Panel bywa wypełniony ubożej niż ankieta
            # i po cichu zubożyłby profil — decyzja, czy tak ma być, należy do człowieka.
            if old not in (None, '', []):
                print(f'  {a["name"]}: {key}: {old!r} -> {value!r}')
            if not dry_run:
                a[key] = value
            changed += 1

    # Nowi ludzie z panelu: dopisujemy ich do repozytorium razem ze zdjęciami.
    # Bez zdjęć strona profilowa byłaby połamana, więc taki artysta czeka,
    # aż menedżer wgra portret i prace w panelu.
    for r in remote:
        if id(r) in matched:
            continue
        name = ' '.join(x for x in (r.get('firstName'), r.get('lastName')) if x).strip()
        if not name:
            continue
        nick = (r.get('nickname') or '').strip()
        slug = resolve_slug(name, nick)
        if not slug:
            continue
        # Nazwa na stronie: tak, jak zapisano ją w katalogu ze zdjęciami, żeby
        # ludzie znani z pseudonimu nie zmienili nagle podpisu.
        display = f'{name} {nick}'.strip() if nick and slug != slugify(name) else name
        entry = {'name': display, 'slug': slug, 'works': 3, 'confidence': 'none'}
        for key, value in (('country', r.get('country')), ('countryCode', r.get('countryCode')),
                           ('city', r.get('city')), ('since', r.get('startedYear')),
                           ('styles', r.get('styles') or None),
                           ('langs', [x.upper() for x in (r.get('languages') or [])] or None),
                           ('ig', (r.get('instagram') or '').lstrip('@') or None)):
            if value not in (None, '', []):
                entry[key] = value
        pulled = pull_photos(entry, r)
        if not has_photos(slug):
            print(f'  Nowy w panelu, ale brak kompletu zdjęć: {display} '
                  f'(portret + 3 prace, pobrano {pulled})')
            continue
        DATA.append(apply_facts(entry))
        matched.add(id(r))
        changed += 1
        print(f'  Nowy artysta z panelu: {display}')

    unknown = [r for r in remote if id(r) not in matched]
    matched_site = {a['slug'] for a in DATA
                    if any(same_person(r['_tokens'], name_tokens(a['name'])) for r in remote)}
    missing = [a['name'] for a in DATA if a['slug'] not in matched_site]
    for r in remote:
        r.pop('_tokens', None)

    # Plik z ankietami zapisujemy tylko wtedy, gdy już istnieje: w CI katalogu
    # _data nie ma i tworzenie go tam nie ma sensu — i tak nie trafi do repo.
    if not dry_run and os.path.isdir(os.path.dirname(DATA_PATH)):
        with open(DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(DATA, f, ensure_ascii=False, indent=1)
            f.write('\n')

    print(f'Panel: {len(remote)} artystów, dopasowano {len(remote) - len(unknown)}, zmian pól: {changed}')
    if unknown:
        names = ', '.join(' '.join(x for x in (r.get('firstName'), r.get('lastName')) if x) for r in unknown)
        print(f'  W panelu, ale nie ma ich w repozytorium (brak zdjęć — dodaj ręcznie): {names}')
    if missing:
        print(f'  Na stronie, ale panel ich nie zna ({len(missing)}): {", ".join(missing)}')
    return matched_site


def slugify(name):
    """Adres strony artysty. Musi być stabilny: zmiana slug to zerwane linki."""
    text = unicodedata.normalize('NFKD', str(name or ''))
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.replace('\u0142', 'l').replace('\u0141', 'L')
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', text.lower())).strip('-')


def resolve_slug(name, nick):
    """
    Adres strony artysty. Najpierw szukamy katalogu, który już jest w repo:
    zmiana sluga to zerwane linki i zdjęcia szukane pod złą ścieżką.

    W panelu „nickname" bywa nazwą z Instagrama, a katalog nazywa się po samym
    imieniu i nazwisku — dlatego sprawdzamy oba warianty.
    """
    candidates = ([slugify(f'{name} {nick}')] if nick else []) + [slugify(name)]
    for cand in candidates:
        if cand and os.path.isdir(os.path.join('assets', 'artists', cand)):
            return cand
    return candidates[-1]


def fetch_photo(url):
    req = urllib.request.Request(PANEL_URL.rstrip('/') + url, headers={'Accept': 'image/*'})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read()


def pull_photos(artist, remote):
    """
    Ściąga zdjęcia z panelu do repozytorium: portret i trzy prace.

    Pliki lądują w repo na stałe — strona ma działać, gdy panel śpi albo go nie ma.
    Zdjęcie, które już leży na dysku, zostawiamy: panel jest źródłem prawdy dla
    danych, ale nie każe co build ściągać po kilkanaście megabajtów od nowa.
    """
    folder = os.path.join('assets', 'artists', artist['slug'])
    wanted = [('profile.jpg', remote.get('profilePhoto'))]
    for i, url in enumerate(remote.get('workPhotos') or [], start=1):
        if i > 3:
            break
        wanted.append((f'work{i}.jpg', url))

    pulled = 0
    for filename, url in wanted:
        if not url:
            continue
        target = os.path.join(folder, filename)
        if os.path.exists(target):
            continue
        try:
            blob = fetch_photo(url)
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f'  Nie udało się pobrać {filename} dla {artist["name"]}: {exc}')
            continue
        os.makedirs(folder, exist_ok=True)
        with open(target, 'wb') as f:
            f.write(blob)
        pulled += 1
    return pulled


def has_photos(slug):
    folder = os.path.join('assets', 'artists', slug)
    return all(os.path.exists(os.path.join(folder, f))
               for f in ('profile.jpg', 'work1.jpg', 'work2.jpg', 'work3.jpg'))


def gone_stub():
    '''
    Strona artysty, którego nie ma już w składzie.

    Nie kasujemy pliku, tylko go nadpisujemy: Render publikuje statykę
    przyrostowo i **nie usuwa** z CDN plików, które zniknęły z repozytorium —
    skasowana strona dalej otwierała się pod starym adresem. Nadpisanie działa
    zawsze, bo ścieżka zostaje w deployu.

    Odwiedzający trafia do ekipy, wyszukiwarki dostają noindex i canonical.
    '''
    return '''<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="index.html">
<meta http-equiv="refresh" content="0; url=index.html#artysci">
<title>BRO TO BRO Tattoo Art Studio Szczecin</title>
<link rel="icon" href="assets/logo-mark.png">
<style>html,body{margin:0;height:100%;background:#0b0b0c;color:#918d86;
font:400 15px/1.5 'Archivo',system-ui,sans-serif;display:grid;place-items:center}
a{color:#fff}</style>
</head>
<body>
<p>Ten artysta nie jest już w składzie. <a href="index.html#artysci">Zobacz ekipę</a>.</p>
<script>location.replace('index.html#artysci');</script>
</body>
</html>
'''

def artists_block():
    """Lista ekipy dla index.html. Kraj wchodzi tylko wtedy, gdy jest znany."""
    rows = []
    for a in DATA:
        parts = [f'n:{json.dumps(a["name"], ensure_ascii=False)}',
                 f's:{json.dumps(a["slug"], ensure_ascii=False)}']
        if a.get('countryCode'):
            parts.append(f'c:{json.dumps(a["countryCode"], ensure_ascii=False)}')
            parts.append(f'cn:{json.dumps(a.get("country") or a["countryCode"], ensure_ascii=False)}')
        rows.append('  {' + ','.join(parts) + '}')
    return 'const ARTISTS=[\n' + ',\n'.join(rows) + '\n];'


def write_index_artists():
    """Podmienia listę ekipy w index.html między znacznikami ARTISTS:START/END."""
    with open(INDEX_PATH, encoding='utf-8') as f:
        page = f.read()

    start = '/* ARTISTS:START — generowane przez build.py, nie edytować ręcznie */\n'
    end = '\n/* ARTISTS:END */'
    i = page.find(start)
    j = page.find(end, i)
    if i < 0 or j < 0:
        print('index.html: brak znaczników ARTISTS:START/END, listy ekipy nie ruszam')
        return False

    updated = page[:i + len(start)] + artists_block() + page[j:]
    if updated == page:
        return False
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write(updated)
    return True


def main():
    """Zwraca kod wyjścia: 0 gdy zbudowano, 1 gdy nie było z czego."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sync', action='store_true',
                        help='pobierz publiczne dane artystów z panelu InkRoute')
    parser.add_argument('--dry-run', action='store_true',
                        help='pokaż, co zmieniłby --sync, ale niczego nie zapisuj')
    args = parser.parse_args()

    if args.dry_run:
        sync_from_panel(dry_run=True)
        print('(--dry-run: nic nie zapisano)')
        return 0

    if args.sync:
        published = sync_from_panel()
        # Bez ankiet w repo (CI) i bez odpowiedzi panelu nie ma z czego budować.
        # Lepiej wyjść błędem i zostawić stronę taką, jaka jest, niż wygenerować
        # pustą listę i zdjąć z serwisu całą ekipę.
        if not DATA:
            print('Brak danych: panel nie odpowiedział, a lokalnych ankiet nie ma. Nic nie zmieniam.')
            return 1
        DATA.sort(key=lambda a: a['name'].lower())
        # Panel jest źródłem prawdy także co do składu: kogo tam zarchiwizowano,
        # tego nie ma i tutaj. Pusta odpowiedź to awaria, a nie zwolnienie całej
        # ekipy — wtedy zostawiamy skład z repozytorium.
        if published:
            dropped = [a for a in DATA if a['slug'] not in published]
            if dropped:
                for a in dropped:
                    with open(f"artysta-{a['slug']}.html", 'w', encoding='utf-8') as f:
                        f.write(gone_stub())
                names = ', '.join(a['name'] for a in dropped)
                print(f'Poza składem wg panelu ({len(dropped)}), strony przekierowane: {names}')
                DATA[:] = [a for a in DATA if a['slug'] in published]

    n = len(DATA)
    for i, a in enumerate(DATA):
        prev = DATA[(i - 1) % n]
        nxt = DATA[(i + 1) % n]
        out = f"artysta-{a['slug']}.html"
        with open(out, 'w', encoding='utf-8') as f:
            f.write(page(a, prev, nxt))
    withbio = sum(1 for a in DATA if a.get('confidence') == 'high')
    print(f'{n} stron profilowych, w tym {withbio} z danymi z ankiety')

    with_country = sum(1 for a in DATA if a.get('countryCode'))
    if write_index_artists():
        print(f'index.html: lista ekipy odświeżona, z krajem {with_country} z {n}')
    if not with_country:
        print('Kraje artystów puste — sekcja krajów na stronie się nie pokaże (czekamy na dane).')
    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
