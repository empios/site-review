# Moduł: Szybkość

## Instrukcja dla subagenta

Wejście: `RUN/speed.json` (mediany Lighthouse mobile/desktop, gotowe znaleziska progowe, `lh_scores`), surowe raporty `RUN/lh-*.json`, `RUN/crux.json` (dane od prawdziwych użytkowników, jeśli był klucz), `basics.json` (nagłówki).

1. Weź `speed.json` → `findings` bez zmian (progi liczy kod, nie model).
2. Jeśli `speed.json.depth == "pominięty"`, zapisz moduł jako `pominięty` z tym samym `reason` i zakończ.
3. Z raportu mediany mobile (`lh-mobile-*.json`) odczytaj audyty z checklisty (`lh:<id>` to klucz w `audits`; w Lighthouse 13 większość diagnostyk to audyty `*-insight`, liczby są w `details`) i dodaj znaleziska z liczbami jako dowód.
4. Jeśli `crux.json.available`, porównaj p75 z progami (LCP 2500/4000 ms, INP 200/500 ms, CLS 0.1/0.25) i dodaj `speed-field-poor` dla kategorii słabej. W raporcie zawsze rozróżniaj dane laboratoryjne (Lighthouse) i terenowe (CrUX).
5. Zapisz `RUN/modules/speed.json`. Głębokość: `pełny`, gdy Lighthouse się udał (z delegacją lub bez).

Zasady jak w module SEO: dowód z liczbą, `id` z katalogu, konkretna poprawka. Nie uruchamiaj Lighthouse równolegle z innymi pomiarami.

## Delegacja

- `web-quality-skills` (`web-quality-audit`, Addy Osmani) — interpretacja wyników Lighthouse i Core Web Vitals.
- Lighthouse MCP (np. `lighthouse-mcp-server`) — jeśli jest, może zastąpić `lighthouse_runs.sh`; wynik i tak przelicz przez `lh_median.py`.

## Checklista

| id | sprawdzenie (audyt Lighthouse 13: `lh:<id>` = klucz w `audits`) | severity | impact | effort | dowód |
|---|---|---|---|---|---|
| `speed-lcp-<form>` | z speed.json | wg progu | 3 | M | measurement |
| `speed-cls-<form>` | z speed.json | wg progu | 2 | M | measurement |
| `speed-tbt-<form>` | z speed.json | wg progu | 2 | M | measurement |
| `speed-field-poor` | crux.json, kategoria słaba | high | 3 | M | measurement |
| `speed-ttfb-slow` | `lh:server-response-time` > 800 ms albo `lh:document-latency-insight` wskazuje wolny serwer | medium | 2 | M | measurement |
| `speed-render-blocking` | `lh:render-blocking-insight` z oszczędnością > 300 ms | medium | 2 | S | measurement |
| `speed-js-heavy` | `lh:total-byte-weight` (JS > 500 KB) lub `lh:bootup-time` > 2 s | medium | 2 | L | measurement |
| `speed-unused-js` | `lh:unused-javascript` z oszczędnością > 150 KB | medium | 2 | M | measurement |
| `img-oversized` | `lh:image-delivery-insight` z oszczędnością > 100 KB dla obrazu | medium | 3 | S | measurement |
| `img-legacy-format` | `lh:image-delivery-insight` wskazuje format (WebP/AVIF) jako źródło oszczędności | low | 2 | S | measurement |
| `img-no-dimensions` | `lh:unsized-images` niepuste | low | 2 | S | dom |
| `font-blocking` | `lh:font-display-insight` niepuste | low | 1 | S | measurement |
| `speed-no-compression` | `lh:document-latency-insight` zgłasza brak kompresji | medium | 2 | S | http |
| `speed-no-cache-headers` | `lh:cache-insight`, > 10 zasobów | low | 1 | S | http |
| `speed-third-party-heavy` | `lh:third-parties-insight`, blokowanie > 250 ms | medium | 2 | M | measurement |
