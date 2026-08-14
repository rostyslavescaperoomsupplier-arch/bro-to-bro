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
python3 build.py                 # przegenerowanie 35 stron profilowych
```

`build.py` czyta `_data/artists.json`. Po zmianie danych artysty trzeba go
uruchomić ponownie, inaczej strona profilowa zostanie stara.

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
