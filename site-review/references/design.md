# Moduł: Design i dostępność

## Instrukcja dla subagenta

Format wyniku i zasady wspólne (pola znaleziska, typy dowodu, problemy całej witryny, nowe identyfikatory): `references/module-format.md`.

Wejście: zrzuty `RUN/shots/<n>/shot-375.png`, `shot-768.png`, `shot-1440.png` (cała strona), `shot-375-fold.jpg`, `shot-1440-fold.jpg` (pierwszy ekran), raporty `RUN/lh-*.json` (kategoria accessibility = axe-core), `basics.json`, surowe HTML.

1. Dostępność: z pliku mediany (`speed.json` → `median_run_file.mobile`; Lighthouse jest tylko dla strony startowej, podstrony sprawdź w DOM/przeglądarce) weź nieudane audyty accessibility (`lh:color-contrast`, `lh:image-alt`, `lh:label`, `lh:heading-order`, `lh:target-size`, `lh:html-has-lang`) — to dowody typu `measurement` z listą elementów.
2. Układ mobilny: `RUN/shots/<n>/metrics.json` ma prawdziwe wymiary z emulacji telefonu. `innerWidth` > 375 przy 375 → `design-viewport-missing`; `horizontalScroll: true` → `design-horizontal-scroll` (dowód: `measurement` z liczbami). Design: oceń zrzuty. Jeśli są skille z sekcji Delegacja, przekaż im zrzuty i adres. Gdy w sesji jest przeglądarka (wbudowana, Chrome DevTools MCP lub Playwright), sprawdź też: przewijanie poziome przy 375 px (`document.documentElement.scrollWidth > innerWidth`), błędy konsoli, widoczny focus po naciśnięciu Tab, tryb ciemny przez emulację `prefers-color-scheme: dark` (zrzut `RUN/shots/<n>/shot-375-dark.png` robi już `screenshots.sh`; jeśli strona jest ciemna domyślnie, zanotuj, że jasnego motywu nie testowano).
Zrzuty pełnostronicowe są robione po przewinięciu strony i z `prefers-reduced-motion: reduce`. `metrics.json.invisibleElements` > 0 albo pusty zrzut → oceniaj na `-fold.jpg` i w przeglądarce i zanotuj to w `reason`. Jeśli przeglądarka w sesji jest ukryta, animacje mogą stać — mierz stan elementów, nie wygląd klatki.
3. Głębokość: `pełny`, gdy były zrzuty + Lighthouse + delegacja lub przeglądarka; `płytki`, gdy tylko część; `pominięty`, gdy brak zrzutów i Lighthouse.
4. Zapisz `RUN/modules/design.json`.

Zasady: dowód = zrzut (ścieżka względem `RUN`; do `evidence.path` wybieraj `-fold.jpg`, gdy problem jest w pierwszym ekranie — pełnostronicowe PNG są za duże, by osadzić je w raporcie) z opisem miejsca („przycisk Kup w prawym górnym rogu przy 375 px”) albo element z audytu Lighthouse. Oceniaj czytelność, hierarchię i spójność, a nie gust. Nie zgłaszaj „mogłoby być ładniej”.

## Delegacja

- `design:design-critique` — krytyka hierarchii, układu i spójności na zrzutach.
- `design:accessibility-review` — przegląd WCAG 2.1 AA.
- `web-design-guidelines` — reguły UI (focus, formularze, typografia, dotyk).
- `frontend-design` — tylko do propozycji poprawek, nie do oceny.

## Checklista

| id | sprawdzenie | severity | impact | effort | dowód |
|---|---|---|---|---|---|
| `a11y-img-alt-missing` | `lh:image-alt` lub `<img>` bez `alt` w HTML | medium | 2 | S | measurement |
| `a11y-contrast-low` | `lh:color-contrast` | medium | 2 | S | measurement |
| `a11y-tap-target-small` | `lh:target-size` | medium | 2 | S | measurement |
| `a11y-focus-invisible` | brak widocznego focusu po Tab | medium | 2 | S | screenshot |
| `a11y-label-missing` | `lh:label` | medium | 2 | S | measurement |
| `a11y-heading-order` | `lh:heading-order` | low | 1 | S | measurement |
| `seo-lang-missing` | `lh:html-has-lang` / `lh:html-lang-valid` | medium | 2 | S | measurement |
| `design-viewport-missing` | `metrics.json`: innerWidth > 375 przy 375 px albo `lh:viewport-insight` | high | 3 | S | measurement |
| `design-horizontal-scroll` | `metrics.json`: horizontalScroll przy 375 px | high | 3 | S | measurement |
| `design-hierarchy-unclear` | brak jednego wyraźnego punktu uwagi w pierwszym ekranie | medium | 2 | M | screenshot |
| `design-typography-readability` | tekst < 16 px na mobile, linie > 90 znaków | medium | 2 | S | screenshot |
| `design-inconsistent-spacing` | różne odstępy lub style tych samych komponentów (nagłówki, przyciski, karty) między stronami | low | 1 | M | screenshot |
| `design-layout-shift-visible` | skoki układu widoczne na zrzutach lub CLS > 0.1 | medium | 2 | M | screenshot |
| `design-console-errors` | błędy JS w konsoli | medium | 2 | M | measurement |
| `design-dark-mode-broken` | nieczytelne elementy w trybie ciemnym | low | 1 | M | screenshot |
| `img-no-dimensions` | `lh:unsized-images` niepuste | low | 2 | S | dom |
