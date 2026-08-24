# BRO TO BRO Tattoo Art Studio

Strona studia tatuażu z Szczecina. Statyczny HTML, bez frameworka i bez backendu.

**Live:** https://rostyslavescaperoomsupplier-arch.github.io/bro-to-bro/

## Struktura

```
index.html                 strona główna
artysta-<slug>.html        35 stron profilowych, generowanych przez build.py
assets/site.css            wspólne style
assets/artists/<slug>/     profile.jpg + work1..3.jpg
assets/logo-*.png|jpg      logo, mark i wordmark wycięte z oryginału
build.py                   generator stron profilowych
opensearch.xml             wyszukiwarka witryny dla przeglądarki
_data/                     NIE w repo, patrz niżej
```

## Uruchomienie i budowanie

```bash
python3 -m http.server 8731      # podgląd na http://127.0.0.1:8731
python3 build.py                 # 35 stron profilowych + lista ekipy w index.html
python3 build.py --sync          # najpierw pobiera dane artystów z panelu InkRoute
```

`build.py` czyta `_data/artists.json`. Po zmianie danych artysty trzeba go
uruchomić ponownie, inaczej strona profilowa zostanie stara.

Lista ekipy w `index.html` też jest generowana — siedzi między znacznikami
`ARTISTS:START` / `ARTISTS:END` i ręcznie się jej nie edytuje.

`--sync` celuje w produkcyjny panel. Na inny adres:
`INKROUTE_URL=http://localhost:3000 python3 build.py --sync`.
Gdy panel nie odpowiada, build leci dalej na starych danych — tylko o tym mówi.

## Co jest interaktywne

| Element | Gdzie | Co robi |
|---|---|---|
| Języki PL / EN / UA | wszędzie | cała treść plus dane dynamiczne, wybór trzymany w `localStorage` |
| Wyszukiwarka ekipy | Ekipa | filtruje 35 kart na żywo po nazwisku |
| Karty artystów | Ekipa | wchodzą na stronę profilową artysty |
| Galeria | Prace | 105 prac, doładowywanie po 24 |
| Lightbox | Prace, profile | strzałki, Esc, licznik, przejście na profil autora |
| Konfigurator | Wycena | klikalna sylwetka na 14 stref, rozmiar, styl, kolor, detal |
| Wycena na żywo | Wycena | widełki, czas pracy, liczba sesji, poziom bólu strefy |
| Kreator zapisów | Zapisy | 4 kroki z walidacją, gotowa wiadomość do skopiowania |
| Oś gojenia | Gojenie | suwak 1-30 dni, 5 etapów, listy rób i nie rób |
| `?q=` | adres strony | wyszukiwarka witryny, jedno trafienie prowadzi wprost na profil |

## Wyszukiwarka w przeglądarce

`opensearch.xml` sprawia, że Chrome sam dodaje stronę do wyszukiwarek witryn.
Wpisz adres strony w pasku, naciśnij Tab i szukaj po nazwisku artysty.
Można też ustawić ręcznie w `chrome://settings/searchEngines`, adres:

```
https://rostyslavescaperoomsupplier-arch.github.io/bro-to-bro/?q=%s
```

## Dane artystów

Zdjęcia i dane pochodzą z firmowego Dysku (`Artists`) oraz z ankiety artysty.
Do repo trafiają wyłącznie zdjęcia profilowe i po trzy prace na osobę.

**Poza repo, katalog `_data/` jest w `.gitignore`:** ankieta zawiera dane
osobowe 52 osób (adresy, telefony, daty urodzenia, komunikatory) i nie może
trafić do publicznego repozytorium.

Na stronę idą tylko pola publiczne: pseudonim, style, rok rozpoczęcia pracy,
miasto, języki, Instagram.

### Stan biogramów

22 z 35 artystów ma dane z ankiety. Pozostałych 13 ma stronę z nazwiskiem
i pracami, bez wymyślonego opisu, bo w ankiecie po prostu ich nie ma:

Aleksandr Gusev, Anna Onishchuk, Daniil Korniienko, Krystsina Butskevich,
Kseniia Zhigulskaia, Maksym Sysoniuk, Maksym Verbov, Mikita Karabka,
Oleksandr Voznyi, Ramy Hanna, Sabina Nikitina, Savva Kozakov, Vladyslav Trofimov.

Do uzupełnienia jest `_data/bio-do-uzupelnienia.csv`.

## Zgłoszenia klienta — co zrobione

Pełna lista (13 punktów, głównie panel InkRoute) leży w `~/inkroute/docs/08-backlog.md`.
Serwisu dotyczyły trzy i wszystkie są zrobione.

**Synchronizacja artystów z panelem.** `python3 build.py --sync` pobiera dane z panelu
(`/api/public/artists`), aktualizuje `_data/artists.json`, a potem przegenerowuje 35 stron
profilowych **oraz** listę ekipy w `index.html` — ta ostatnia siedzi teraz między znacznikami
`ARTISTS:START` / `ARTISTS:END` i ręcznie się jej nie edytuje.

Z panelu przychodzą wyłącznie pola publiczne: imię, pseudonim, kraj, miasto, style, języki,
rok startu, Instagram. Dwa bezpieczniki: na stronę trafiają tylko artyści z włączoną w panelu
flagą „Publikuje się na stronie" (domyślnie wyłączona), a `--sync` **nie dodaje nowych osób** —
nowy artysta bez zdjęć dałby połamane kafelki. Zamiast tego wypisuje, kogo brakuje po której
stronie.

Bez `--sync` `build.py` działa jak dotąd, offline, na danych z repozytorium.

**Artyści wg krajów.** Nad siatką ekipy jest rząd krajów, a sama siatka grupuje się
nagłówkami. Kraju nie ma jeszcze u nikogo — dopóki tak jest, rząd krajów się nie pokazuje
i strona wygląda jak wcześniej. Klient ma przysłać, kto z jakiego kraju; wtedy włączy się samo.

**Rosyjski i kolejność języków.** „GE" to niemiecki, który już był. Doszedł RU (pełne 150
kluczy w `index.html`, nazwy części ciała, przewodnik po gojeniu, 37 kluczy w `giveaway.html`,
profile w `build.py`), kolejność to teraz EN, DE, FR, PL, RU, UA. Ukraiński **został jako
szósty** — klient nie odpowiedział, a usunięcie wyrzuciłoby gotowe tłumaczenia. Gdyby miał
zniknąć: `data-lang="ua"` w `index.html`, `giveaway.html` i szablonie `build.py`, plus `LANGS`.

`screen.html`, `regulamin.html` i `prywatnosc.html` to cienkie ramki na panel, własnego
przełącznika języków nie mają — nie było tam czego zmieniać.

## Do sprawdzenia przed rozgłaszaniem strony

- **Skład ekipy.** Na Instagramie studio pisze o 27 artystach, na Dysku jest 36
  folderów. Warto potwierdzić, kto jest aktualnie w składzie, zanim strona
  pójdzie w świat.
- **Stawki w konfiguratorze.** Ustawione na 350 zł za godzinę przy minimum
  400 zł, to wartości przykładowe. Zmiana w `assets/site.css` nie wystarczy,
  stawki siedzą w `index.html` w sekcji `4. configurator`.
- **Zaliczka i okno 48 godzin** w FAQ to typowa praktyka, nie potwierdzona
  reguła studia.
- **Adres.** Wpisany Grizzly Barber Shop, ul. Mickiewicza 36A. Stara wizytówka
  w Mapach Google (Księcia Bogusława X 14) ma status zamkniętej na stałe
  i wymaga aktualizacji, inaczej klienci pojadą pod zły budynek.
- **Skan paszportu** leży w udostępnionym folderze na Dysku, w katalogu jednego
  z artystów. Warto go stamtąd usunąć.

## Skąd wzięte fakty

- Instagram [@brotobrotattoo](https://www.instagram.com/brotobrotattoo/):
  96 konwentów rocznie, 37 nagród, bazy Szczecin, Konstanz, Paryż
- TikTok [@brotobro.tattoo](https://www.tiktok.com/@brotobro.tattoo): darmowa konsultacja
- Facebook [@arttattoobro](https://www.facebook.com/arttattoobro/): usługi studia
- [INKsearch](https://pl.inksearch.co/studio/brotobro-tattoo-studio): style, języki obsługi
- Google Maps: ocena 4,8 z 72 opinii, telefon 579 128 368
