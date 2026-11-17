# site-review — projekt skilla do audytu stron i aplikacji webowych

Data: 2026-11-17 · Status: zatwierdzony (2026-11-17)

**Decyzje v1 (zatwierdzone przez użytkownika):**
- Zakres: tylko strony publiczne i lokalny serwer deweloperski (`localhost`). Obszary za logowaniem — poza v1, osobny krok później.
- Odbiorca skilla: tylko użytkownik. Skill osobisty w `~/.claude/skills/site-review/`, raport po polsku, moduł PL domyślnie włączony dla polskich stron. Publikacja (angielski, plugin) — v2.

## 1. Po co

Dziś audyt strony z poziomu Claude Code to 4–5 osobnych skilli (SEO, Lighthouse, CRO, design, code review), każdy z innym formatem, skalą i duplikatami. Żaden nie łączy problemu widocznego pod URL-em z miejscem w kodzie, który go powoduje. `site-review` to jeden punkt wejścia: ocenia stronę/apkę w sześciu obszarach, deleguje do najlepszego dostępnego narzędzia, a wyniki skleja w jeden raport z jedną skalą, wspólnymi priorytetami i wskazaniem `plik:linia`.

Główny odbiorca: deweloper właściciel projektu (lista poprawek do zrobienia w repo). Drugi odbiorca: osoba nietechniczna (klient, szef) — dostaje streszczenie na górze raportu. *(decyzja Claude — użytkownik nie wskazał odbiorcy)*

## 2. Cele, nie-cele, anty-cele

**Cele**
- Jeden audyt w 6 obszarach: SEO i indeksacja, szybkość, marketing/CRO, design i dostępność, jakość kodu, (opcjonalnie) moduł PL.
- Działa od razu na gołej instalacji (wbudowane checklisty), lepiej z doinstalowanymi skillami specjalistycznymi.
- Każde znalezisko ma dowód i — gdy jest repo — lokalizację w kodzie.
- Jedna skala 0–100 na obszar + lista „quick wins” (wpływ × wysiłek).
- Raport jako udostępnialna strona (Artifact) + plik `findings.json` do ponownego audytu.
- Tryb ponownego sprawdzenia: co naprawione, co zostało, co nowe.

**Nie-cele (v1)**
- Automatyczne poprawianie kodu. Po raporcie skill może *zaproponować* naprawę top pozycji, ale robi to dopiero po zgodzie użytkownika, zwykłym trybem pracy.
- Audyt obszarów za logowaniem (v1 sprawdza tylko strony publiczne i `localhost`).
- Crawl całych dużych serwisów (tysiące URL-i), analiza backlinków, analiza konkurencji, śledzenie pozycji w Google.
- Zastępowanie Google Search Console / analityki — skill nie ma dostępu do danych ruchu, chyba że użytkownik da klucz (np. PageSpeed Insights API dla danych CrUX).

**Anty-cele (porażka, nawet jeśli „działa”)**
- Znaleziska wymyślone z samego HTML-a, bez pomiaru — jedno fałszywe znalezisko podważa cały raport.
- Raport-śmietnik: 150 pozycji bez hierarchii. Ma być krótka lista tego, co warto zrobić teraz.
- Ogólniki („dodaj więcej wartościowej treści”, „popraw UX”) bez konkretnego miejsca i konkretnej zmiany.
- Niestabilna ocena: ten sam serwis bez zmian dostaje wyraźnie inny wynik przy kolejnym uruchomieniu.

## 3. Ograniczenia

- Środowisko: Claude Code (CLI i desktop). Narzędzia przeglądarki mogą być różne: wbudowana przeglądarka aplikacji, Chrome DevTools MCP, Playwright MCP albo żadne (wtedy tylko `curl` + Lighthouse CLI, design i CRO płytko).
- Lighthouse przez `npx lighthouse` wymaga Node i Chrome/Chromium na maszynie.
- Użytkownik ma lokalnie: `design:design-critique`, `design:accessibility-review`, `engineering:code-review`, `security-review`, `modern-web-guidance`, `frontend-design`, `humanizer-polish`. Nie ma: claude-seo, web-quality-skills, marketingskills, squirrelscan.
- Bezpieczeństwo: audyt tylko stron, które użytkownik posiada lub ma prawo audytować. Bez wypełniania i wysyłania formularzy, bez logowania poza lokalnym/stagingowym środowiskiem z danymi testowymi, crawl z limitem tempa i z poszanowaniem `robots.txt`.
- Wysyłanie URL-a do zewnętrznych API (PageSpeed Insights) tylko dla publicznych adresów; skill mówi o tym w raporcie.

## 4. Podejścia (rozważone)

| | Podejście | Zysk | Koszt |
|---|---|---|---|
| **A (wybrane)** | Orkiestrator + subagent na moduł; deleguje do zainstalowanego skilla specjalistycznego, a gdy go brak, używa własnej, krótszej checklisty i oznacza moduł jako „płytki” | Działa od razu, rośnie z ekosystemem, jedna skala i format | Utrzymanie checklist zapasowych; mapowanie wyników z obcych skilli na wspólny schemat |
| B | Cienki router: odpala zainstalowane skille po kolei i skleja raporty | Najmniej pracy | U użytkownika brak skilli SEO/speed/CRO → dziś połowa audytu znika |
| C | Wszystko własne: reguły, crawler, skrypty | Pełna kontrola i deterministyczność | Duplikuje claude-seo i spółkę, najwięcej utrzymania, ryzyko słabszej kopii |

Użytkownik wybrał **A**.

## 5. Projekt

### 5.1 Wejście i tryby

Wywołanie: `/site-review <url>`, `/site-review <ścieżka-repo>`, `/site-review <url> <ścieżka-repo>` lub bez argumentów w katalogu projektu.

- **Tylko URL** → moduły 1–4 (+PL); moduł kodu pominięty i opisany jako pominięty.
- **Tylko repo** → skill wykrywa framework i komendę dev (`package.json`), proponuje uruchomienie serwera lokalnego i audytuje `localhost`; plus moduł kodu.
- **URL + repo** → pełny tryb z mapowaniem znalezisk na kod.

Flagi:
- `--quick` — sama strona główna, bez subagentów, ~5 min. Domyślnie: **pełny**.
- `--pages N` — liczba podstron (domyślnie 5: strona główna + najważniejsze z nawigacji i sitemapy; max 50).
- `--only seo,speed,...` — wybrane moduły.
- `--pl` / `--no-pl` — wymuszenie modułu PL (domyślnie automatycznie, gdy `lang="pl"` lub domena `.pl`).
- `--recheck` — porównanie z poprzednim `findings.json`.

### 5.2 Przebieg

1. **Rozpoznanie** (orkiestrator): pobranie strony głównej, `robots.txt`, `sitemap.xml`, nagłówków HTTP; wybór podstron; wykrycie frameworka w repo; sprawdzenie, które skille specjalistyczne i narzędzia przeglądarki są dostępne w sesji. Wynik: `context.json` (URL-e, framework, mapa tras → pliki, dostępne narzędzia).
2. **Moduły równolegle**: jeden subagent na moduł, każdy dostaje `context.json` i zwraca listę znalezisk w schemacie z 5.4.
3. **Scalanie**: deduplikacja (ten sam problem z kilku modułów → jedno znalezisko z wieloma tagami), weryfikacja dowodów, mapowanie na kod, ocena, priorytety.
4. **Raport**: Artifact HTML + `findings.json`.
5. **Na koniec**: propozycja naprawy 3 najlepszych quick wins (wymaga zgody).

### 5.3 Moduły

Każdy moduł ma: *delegację* (skill specjalistyczny, jeśli jest) i *fallback* (checklista w `references/<moduł>.md`, ~20–40 kluczowych punktów). Moduł raportuje głębokość: **pełny** (delegacja lub pełny pomiar), **płytki** (fallback/brak narzędzi), **pominięty** (z powodem).

1. **SEO i indeksacja** — delegacja: claude-seo (`seo-audit`), squirrelscan. Fallback: kody odpowiedzi i przekierowania, `robots.txt`, `noindex` (meta i `X-Robots-Tag`), canonical, sitemap (czy zawiera audytowane strony, czy zwraca 200), title/description/H1, hreflang, dane strukturalne, OG/Twitter, linkowanie wewnętrzne, **różnica HTML surowy vs wyrenderowany** (treść widoczna tylko po JS), `llms.txt` jako informacja.
2. **Szybkość** — delegacja: web-quality-skills, Lighthouse MCP. Fallback: `npx lighthouse` mobile + desktop (dane laboratoryjne); CrUX przez PageSpeed Insights API, jeśli jest klucz (dane terenowe, p75). Raport zawsze rozróżnia lab vs field. Mediana z 3 przebiegów dla stabilności.
3. **Marketing / CRO** — delegacja: marketingskills (`page-cro` / `cro`). Fallback: propozycja wartości nad zgięciem, jeden główny CTA, sygnały zaufania (opinie, logotypy, dane kontaktowe), tarcie w formularzach (liczba pól — bez wysyłania), spójność komunikatu z title/description, obecność analityki (GA4/GTM/pixel w ruchu sieciowym), podgląd udostępnienia (OG image).
4. **Design i dostępność** — delegacja: `design:design-critique`, `design:accessibility-review`, web-design-guidelines. Wejście: zrzuty ekranu 375 / 768 / 1440 px (+ dark mode, jeśli strona go wspiera), drzewo dostępności, wynik axe-core (przez Lighthouse lub `@axe-core/cli`). Oceny: hierarchia, czytelność, spójność, kontrast, wielkość celów dotykowych, focus, przewijanie poziome na mobile, błędy konsoli.
5. **Kod** (tylko z repo) — delegacja: `security-review`, `engineering:code-review` w trybie audytu wybranych obszarów, `modern-web-guidance`. Fallback i zakres: strategia renderowania (SSR/SSG/CSR) vs wymagania SEO, konfiguracja metadanych we frameworku, obsługa obrazów (format, rozmiary, lazy), rozmiar bundla (tylko z istniejącego wyniku builda, np. `.next/`, `dist/` — skill sam nie uruchamia builda; *decyzja Claude*), nagłówki bezpieczeństwa w konfiguracji, `npm audit` / przestarzałe zależności, sekrety w kodzie klienta. Nie jest to pełny code review całego repo.
6. **Moduł PL** (opcjonalny) — baner cookies i **czy tracking startuje przed zgodą** (ruch sieciowy przed kliknięciem), link do polityki prywatności, klauzula informacyjna RODO przy formularzach, dane firmy (NIP/KRS dla e-commerce), polskie SEO (odmiana fraz w title/H1, `lang`, hreflang `pl`), jakość polskiego tekstu (opcjonalnie `humanizer-polish` do wykrycia „AI-owego” brzmienia). Moduł jest informacyjny, nie jest poradą prawną — raport to mówi.

### 5.4 Schemat znaleziska

```json
{
  "id": "seo-canonical-missing",
  "module": "seo",
  "tags": ["seo", "code"],
  "severity": "critical | high | medium | low",
  "title": "Brak canonical na podstronach produktów",
  "url": "https://example.com/produkt/x",
  "evidence": { "type": "http | dom | screenshot | measurement | file", "detail": "...", "path": "evidence/seo-canonical-missing.png" },
  "code_location": { "file": "app/produkt/[slug]/page.tsx", "line": 12, "confidence": "pewne | prawdopodobne" },
  "fix": "Konkretna zmiana do wprowadzenia",
  "impact": 1,
  "effort": "S | M | L",
  "source": "claude-seo | fallback | lighthouse | ...",
  "confidence": "potwierdzone | do weryfikacji"
}
```

**Reguła dowodu:** znalezisko bez dowodu nie trafia do listy głównej — ląduje w sekcji „Do weryfikacji”. Dowód to: odpowiedź HTTP, fragment DOM, zrzut ekranu, pomiar albo `plik:linia`.

### 5.5 Mapowanie URL → kod

Orkiestrator buduje mapę tras na etapie rozpoznania: konwencje frameworka (Next.js `app/` i `pages/`, Astro, SvelteKit, Nuxt, Remix, Vite + React Router — odczyt definicji tras), a potem dla konkretnego znaleziska szuka w repo charakterystycznych ciągów (tekst nagłówka, wartość meta, nazwa klasy, nazwa pliku obrazka). Pewność „pewne”, gdy trasa i ciąg pokrywają się jednoznacznie; „prawdopodobne” z listą do 3 kandydatów w przeciwnym razie. Brak trafienia → bez lokalizacji, nigdy zgadywanej.

### 5.6 Ocena i priorytety

- Ocena modułu: `100 − Σ kar` (critical 25, high 10, medium 4, low 1), minimum 0. Wagi są w jednym pliku konfiguracyjnym.
- Wynik ogólny: średnia modułów z wagami (SEO 25, szybkość 20, CRO 20, design 20, kod 15; PL poza średnią — osobny znaczek zgodności). Moduły pominięte wyłączone ze średniej; płytkie oznaczone w raporcie.
- Tam, gdzie narzędzie ma własną ocenę (np. Lighthouse Performance), raport pokazuje ją obok, nie miesza.
- Priorytet: `impact (1–3) × waga wysiłku (S=3, M=2, L=1)`. Top 10 = „Zrób teraz”; macierz quick wins / duże projekty / drobiazgi.
- Stabilność: ten sam zestaw reguł i wag przy każdym uruchomieniu; pomiary szybkości jako mediana z 3.

### 5.7 Raport

Artifact HTML (jedna strona), kolejność:
1. **Streszczenie** — 4–5 zdań językiem nietechnicznym, wynik ogólny, 3 najważniejsze rzeczy.
2. **Karty ocen** — 6 modułów, ocena, głębokość (pełny/płytki/pominięty), źródło.
3. **Zrób teraz** — top 10 z priorytetu, każde z `plik:linia` i konkretną poprawką.
4. **Szczegóły per moduł** — rozwijane listy znalezisk z dowodami (zrzuty ekranu inline).
5. **Do weryfikacji** — znaleziska bez twardego dowodu.
6. **Metodologia** — co sprawdzono, czym, czego nie (i jak to odblokować: „doinstaluj claude-seo”, „dodaj klucz PSI”).

Język raportu: język rozmowy (domyślnie polski). Pliki robocze w `.site-review/<data>/` w katalogu projektu (lub w scratchpadzie, gdy brak repo): `context.json`, `findings.json`, `evidence/`. `--recheck` czyta najnowszy `findings.json` i oznacza: naprawione / nadal / nowe. Skill nie zmienia `.gitignore` sam — w raporcie podpowiada dopisanie `.site-review/`. *(decyzja Claude)*

Budżet czasu *(decyzja Claude)*: `--quick` ok. 5 min, pełny tryb z 5 podstronami ok. 15–25 min. Subagenty modułów odpalane równolegle; Lighthouse sekwencyjnie (równoległe przebiegi zakłamują pomiar).

### 5.8 Struktura plików skilla

```
site-review/
  SKILL.md                 # orkiestracja, tryby, reguły dowodu, scalanie
  references/
    seo.md  speed.md  cro.md  design.md  code.md  pl.md   # checklisty fallback
    delegation.md          # mapa: moduł → skille specjalistyczne + jak tłumaczyć ich wyniki na schemat
    scoring.md             # wagi i reguły oceny
    url-to-code.md         # konwencje tras per framework
  scripts/
    fetch_basics.sh        # nagłówki, robots, sitemap, surowy HTML
    lighthouse_runs.sh     # 3 przebiegi, mediana
    merge_findings.py      # deduplikacja, ocena, priorytety, diff dla --recheck
  assets/
    report-template.html   # szablon raportu
```

Instalacja v1: skill osobisty w `~/.claude/skills/site-review/`. *(decyzja Claude)*

## 6. Zostawione budującemu

- Dokładna treść checklist fallback (punkt wyjścia: research z 17.11.2026 — claude-seo, web-quality-skills, page-cro, web-design-guidelines).
- Implementacja skryptów i szablonu raportu, wygląd raportu.
- Dobór progów (np. kiedy obraz jest „za duży”), dopracowanie wag po pierwszych testach.
- Sposób wykrywania dostępnych skilli i narzędzi w sesji.
- Testy: 3 strony referencyjne (dobra, średnia, zła) do sprawdzenia stabilności oceny.
