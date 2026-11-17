---
name: site-review
description: Audyt strony lub aplikacji webowej w 6 obszarach (SEO i indeksacja, szybkość, marketing/CRO, design i dostępność, jakość kodu, zgodność PL/RODO) z jednym raportem, oceną 0–100, priorytetami i wskazaniem plik:linia w repo. Używaj, gdy użytkownik prosi o „audyt strony”, „review strony”, „sprawdź SEO / szybkość / design strony”, „oceń landing”, albo o website audit / site review / web app review — także dla localhost i projektu w repo.
---

# site-review

Jeden audyt strony w sześciu obszarach. Liczby (oceny, priorytety, scalanie) liczą skrypty — Ty zbierasz dowody, oceniasz jakościowo i piszesz streszczenie. Raport i rozmowa po polsku.

`SKILL_DIR` = katalog tego pliku. Wszystkie skrypty: `python3 "$SKILL_DIR/scripts/<plik>"` lub `bash "$SKILL_DIR/scripts/<plik>"`.

## Granice (zawsze)

- Audytuj tylko strony użytkownika albo takie, które ma prawo audytować. W razie wątpliwości zapytaj.
- v1 działa bez logowania: tylko strony publiczne i `localhost`. Gdy strona wymaga logowania, powiedz to i audytuj część publiczną.
- Nie wysyłaj formularzy, nie klikaj przycisków zmieniających dane, nie twórz kont.
- Crawl szanuje robots.txt, robi 1 s odstępu między żądaniami (domyślne w `scripts/fetch_basics.py`).
- `scripts/crux.py` wysyła adres do Google (PageSpeed Insights) — tylko dla publicznych adresów i tylko z `PSI_API_KEY`; zapisz to w notatkach Metodologii.
- Znalezisko bez dowodu nie obniża oceny — trafia do „Do weryfikacji”. Nigdy nie zgaduj `plik:linia`.
- Nie zmieniaj kodu użytkownika w trakcie audytu. Poprawki dopiero po raporcie i po zgodzie.

## 1. Wejście i flagi

Wywołania: `/site-review <url>`, `/site-review <ścieżka-repo>`, `/site-review <url> <ścieżka-repo>`, albo bez argumentów w katalogu projektu (= tryb repo).

| flaga | działanie |
|---|---|
| `--quick` | tylko strona główna, bez subagentów, moduły po kolei (~5 min) |
| `--pages N` | liczba stron (domyślnie 5, max 50) |
| `--only seo,speed,cro,design,code,pl` | tylko wybrane moduły; reszta = `pominięty` z powodem „flaga --only” |
| `--pl` / `--no-pl` | wymuś / wyłącz moduł PL (domyślnie: automatycznie) |
| `--recheck` | porównaj z ostatnim audytem w `.site-review/` |

Tryby:
- **Tylko URL** → moduł `code` = `pominięty` („brak repo”).
- **Tylko repo** → odczytaj `package.json` (`dev`/`start`, framework), zaproponuj użytkownikowi komendę uruchomienia serwera i port; po zgodzie uruchom go w tle i audytuj `http://localhost:<port>`. Bez zgody — tylko moduł `code`.
- **URL + repo** → pełny tryb z lokalizacją w kodzie.

## 2. Katalog przebiegu

`RUN` = `<repo>/.site-review/<YYYY-MM-DD-HHMM>/`; bez repo — `<scratchpad>/site-review/<YYYY-MM-DD-HHMM>/`. Utwórz `RUN/modules/`. Przy `--recheck` znajdź najnowszy wcześniejszy `.site-review/*/findings.json` → `PREV` (brak → powiedz, że to pierwszy audyt, i kontynuuj bez porównania).

## 3. Rozpoznanie (główny wątek, sekwencyjnie)

Kroki 2 i 4 trwają długo: uruchamiaj je z timeoutem narzędzia 600000 ms (albo w tle i poczekaj na koniec). Domyślny limit 2 min przerwie je w połowie.

1. `python3 "$SKILL_DIR/scripts/fetch_basics.py" URL --out RUN --pages N` (`--quick` → `--pages 1`). Adres bez `http(s)://` uzupełnij o `https://`.
   - Kod wyjścia 2 = strona nieosiągalna. Kod wyjścia 4 = strona startowa zwraca błąd HTTP (4xx/5xx, często blokada botów/WAF albo przerwa techniczna). W obu przypadkach pokaż użytkownikowi status i `basics.json.errors`. Nie oceniaj treści strony błędu jak strony właściwej.
   - Bez repo: zakończ bez raportu. Z repo: zaproponuj audyt samego kodu — wtedy seo, speed, cro, design i pl zapisz jako `pominięty` z powodem „strona startowa zwróciła <status>” i przejdź do modułu `code`.
2. Zrzuty dla każdej strony `i` z `basics.json.pages`: `bash "$SKILL_DIR/scripts/screenshots.sh" PAGE_URL RUN/shots/i` (pełne strony PNG, pierwsze ekrany `-fold.jpg` do raportu, `metrics.json` z prawdziwą szerokością widoku). Kod 3 = brak Chrome lub Node 22+ → zanotuj, design i CRO będą `płytki`.
3. `python3 "$SKILL_DIR/scripts/render_diff.py" START_URL --raw RUN/raw/page-0.html --out RUN` (tylko strona startowa).
4. `bash "$SKILL_DIR/scripts/lighthouse_runs.sh" START_URL RUN` (6 przebiegów, ~2–4 min, przy pierwszym uruchomieniu dłużej przez pobranie Lighthouse; nigdy równolegle z innymi pomiarami). Potem ZAWSZE `python3 "$SKILL_DIR/scripts/lh_median.py" RUN --url START_URL` — także gdy `lighthouse_runs.sh` zakończył się błędem: liczy medianę z udanych przebiegów albo oznacza szybkość jako `pominięty` z powodem.
5. Tylko dla publicznego adresu: `python3 "$SKILL_DIR/scripts/crux.py" START_URL --out RUN` (sam odmówi dla localhost i adresów prywatnych; bez klucza zapisze `available: false` — to normalne).
6. Repo: framework przez `route_map.detect_framework` (`python3 -c "import sys; sys.path.insert(0, '$SKILL_DIR/scripts'); import route_map; print(route_map.detect_framework('REPO'))"`).
7. Ustal `available_skills`: przejrzyj listę skilli dostępnych w tej sesji i wybierz pasujące do `references/delegation.md`. Ustal `tools`: czy masz przeglądarkę (wbudowaną, Chrome DevTools MCP, Playwright) i narzędzie Agent.
8. PL: `pl = basics.json.pl_detected`, chyba że `--pl` / `--no-pl`.
9. Zapisz `RUN/context.json`:
   `{"url", "repo", "framework", "pages", "pl", "available_skills", "tools", "flags", "date", "notes": []}`.

## 4. Moduły

| moduł | instrukcja | wynik |
|---|---|---|
| seo | `references/seo.md` | `RUN/modules/seo.json` |
| speed | `references/speed.md` | `RUN/modules/speed.json` |
| cro | `references/cro.md` | `RUN/modules/cro.json` |
| design | `references/design.md` | `RUN/modules/design.json` |
| code | `references/code.md` | `RUN/modules/code.json` |
| pl | `references/pl.md` (tylko gdy `pl`) | `RUN/modules/pl.json` |

Wspólne zasady modułów: `references/delegation.md` (kiedy i jak używać skilli specjalistycznych, jak tłumaczyć wyniki, głębokość), `references/finding-ids.md` (identyfikatory), schemat znaleziska w `scripts/findings.py`. Moduł wyłączony (`--only`, `--no-pl`, brak repo) → zapisz plik z `"depth": "pominięty"` i `reason`.

Uruchamianie:
- **Pełny tryb i masz narzędzie Agent:** jeden subagent na moduł, równolegle (Lighthouse jest już policzony). Prompt subagenta: ścieżki `SKILL_DIR`, `RUN`, `REPO`; „Przeczytaj `SKILL_DIR/references/<moduł>.md`, `SKILL_DIR/references/delegation.md` i `SKILL_DIR/references/finding-ids.md`. Wykonaj instrukcję modułu na danych w RUN. Zapisz wynik do `RUN/modules/<moduł>.json`. Nie zmieniaj plików poza RUN. Odpowiedz jednym zdaniem: liczba znalezisk i głębokość.”
- **`--quick` albo brak narzędzia Agent:** wykonaj moduły po kolei w głównym wątku, w tej samej kolejności co tabela.

Po zakończeniu sprawdź, że każdy oczekiwany plik modułu istnieje i jest poprawnym JSON. Brakujący → zapisz go jako `pominięty` z powodem „moduł nie zwrócił wyniku”.

## 5. Scalanie i lokalizacja w kodzie

1. `python3 "$SKILL_DIR/scripts/merge_findings.py" --run RUN [--repo REPO] [--prev PREV]`.
2. Jeśli `report.json.invalid` niepuste — popraw te znaleziska w plikach modułów (zwykle zły `impact`/`effort`/`id`) albo usuń je; nie ignoruj po cichu.
3. Gdy jest repo: dla każdego znaleziska z polem `needles` i bez `code_location` uruchom `python3 "$SKILL_DIR/scripts/locate_code.py" REPO --path <ścieżka z url> --needle ...` (zasady: `references/url-to-code.md`). Wynik ≠ `null` → wpisz jako `code_location` w pliku modułu.
4. Uruchom `scripts/merge_findings.py` ponownie (te same argumenty). To ostateczne `findings.json` i `report.json`.

## 6. Raport

1. Przeczytaj `RUN/report.json`. Napisz `RUN/summary.txt`: 4–5 zdań bez żargonu dla osoby nietechnicznej — jak wypada strona, co najbardziej szkodzi, 3 najważniejsze rzeczy do zrobienia (z „Zrób teraz”). Akapity oddzielaj pustą linią. Nie podawaj liczb, których nie ma w `report.json`.
2. Dopisz do `context.json.notes` to, co czytelnik musi wiedzieć o metodzie: moduły płytkie i co by je pogłębiło („doinstaluj claude-seo”, „dodaj PSI_API_KEY”), użycie PSI, brak Chrome itd.
3. `python3 "$SKILL_DIR/scripts/render_report.py" --run RUN --summary RUN/summary.txt` (szablon: `assets/report-template.html`).
4. Opublikuj `RUN/report.html` narzędziem Artifact, jeśli jest dostępne (ikona `chart`, opis: „Audyt <host> — SEO, szybkość, marketing, design, kod”). Bez tego narzędzia podaj ścieżkę do pliku.

Opis wag dla użytkownika: `references/scoring.md`.

## 7. Zakończenie

W odpowiedzi do użytkownika:
- wynik ogólny i oceny obszarów (jedna linia każdy, z głębokością),
- 3 quick wins z `report.json.quadrants["quick win"]` (tytuł + `plik:linia`, jeśli jest),
- przy `--recheck`: ile naprawionych / nadal / nowych,
- co było płytkie lub pominięte i dlaczego,
- link do raportu.

Zapytaj, czy naprawić te 3 quick wins — bez zgody nic nie zmieniaj. Jeśli `.site-review/` nie jest w `.gitignore` repo, zaproponuj dopisanie (nie dopisuj sam). Jeśli uruchomiłeś serwer deweloperski, zatrzymaj go albo zapytaj, czy zostawić.
