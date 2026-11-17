# Moduł: SEO i indeksacja

## Instrukcja dla subagenta

Format wyniku i zasady wspólne (pola znaleziska, typy dowodu, problemy całej witryny, nowe identyfikatory): `references/module-format.md`.

Wejście (katalog przebiegu `RUN`): `context.json`, `basics.json` (statusy, nagłówki, robots, sitemap, meta każdej strony, surowe HTML w `raw/`), `render_diff.json`.

1. Jeśli `context.json` → `available_skills` zawiera pełny audyt SEO (`claude-seo`/`seo-audit` albo `squirrelscan`), użyj go na `context.url` i przetłumacz jego wyniki według `references/delegation.md`. Głębokość: `pełny`.
2. W przeciwnym razie przejdź checklistę poniżej. Głębokość: `płytki` (checklista nie zastępuje pełnego narzędzia SEO). `seo-ai-visibility` może ją uzupełnić, ale nie zmienia głębokości na `pełny`.
3. Zawsze dołącz znaleziska z `render_diff.json` → `findings` (są już w schemacie).
4. Zapisz `RUN/modules/seo.json`: `{"module": "seo", "depth": ..., "reason": ..., "findings": [...]}`.

Zasady: każde znalezisko ma `evidence.detail` z konkretem (nagłówek HTTP, fragment HTML, liczba znaków, adres); bez dowodu → nie zgłaszaj albo zostaw bez `evidence` (trafi do „Do weryfikacji”). Używaj `id` z `references/finding-ids.md`. Problem jednej strony → wpis z jej `url`; problem całej witryny → jeden wpis na stronie startowej (zasada w `references/module-format.md`). `fix` = konkretna zmiana, nie ogólnik. Gdy jest repo, dodaj `needles` dla lokalizacji (tekst title, H1, wartość meta) w polu `needles` — orkiestrator uruchomi `locate_code.py`.

## Delegacja

- `claude-seo` (`seo-audit`, `/seo audit <url>`) — pełny audyt SEO; preferowany.
- `squirrelscan` `audit-website` — wymaga CLI `squirrel`; dobre pokrycie reguł.
- `small-business:seo-ai-visibility` — tylko widoczność w AI (GEO), uzupełniająco.

## Checklista

Źródło danych w nawiasie. Severity / impact / effort to wartości domyślne — zmień, gdy kontekst to uzasadnia (np. `noindex` na stronie prywatnej to nie błąd).

| id | sprawdzenie | severity | impact | effort | dowód |
|---|---|---|---|---|---|
| `seo-status-error` | status ≠ 200 dla audytowanych stron (basics.pages[].status) | critical | 3 | S | http |
| `seo-redirect-chain` | `chain` dłuższy niż 2 adresy; sprawdź też wejście przez `http://` i wariant z/bez `www` (`curl -sIL`) | medium | 2 | S | http |
| `seo-https-missing` | start_url http bez przekierowania na https | high | 3 | S | http |
| `seo-mixed-content` | `http://` w src/href zasobów na stronie https (raw HTML) | medium | 2 | S | dom |
| `seo-robots-blocks` | robots.txt blokuje audytowane strony albo `/` | critical | 3 | S | http |
| `seo-noindex` | meta robots zawiera `noindex` na stronie publicznej | critical | 3 | S | dom |
| `seo-x-robots-noindex` | nagłówek `X-Robots-Tag: noindex` | critical | 3 | S | http |
| `seo-canonical-missing` | meta.canonical puste | high | 2 | S | dom |
| `seo-canonical-mismatch` | canonical wskazuje inną domenę/ścieżkę bez powodu | high | 2 | S | dom |
| `seo-sitemap-missing` | sitemap.status ≠ 200 i brak `Sitemap:` w robots | medium | 2 | S | http |
| `seo-sitemap-page-missing` | ważna strona spoza sitemap.urls | low | 1 | S | http |
| `seo-title-missing` | meta.title puste | high | 3 | S | dom |
| `seo-title-length` | długość title < 15 lub > 60 | low | 1 | S | dom |
| `seo-title-duplicate` | ten sam title na ≥ 2 stronach | medium | 2 | S | dom |
| `seo-description-missing` | brak description | medium | 2 | S | dom |
| `seo-description-length` | description < 50 lub > 160 | low | 1 | S | dom |
| `seo-h1-missing` | h1_count == 0 | medium | 2 | S | dom |
| `seo-h1-multiple` | h1_count > 1 | low | 1 | S | dom |
| `seo-lang-missing` | brak `lang` na `<html>` | medium | 2 | S | dom |
| `seo-hreflang-invalid` | hreflang bez wersji zwrotnej lub z błędnym kodem | medium | 2 | M | dom |
| `seo-schema-missing` | brak JSON-LD na stronie produktu/artykułu/firmy lokalnej | low | 2 | M | dom |
| `seo-og-missing` | brak og:title / og:description / og:image | low | 1 | S | dom |
| `seo-internal-links-broken` | linki z meta.links zwracające 4xx/5xx (sprawdź max 30, odstęp 1 s) | medium | 2 | S | http |
| `seo-content-js-only` | z render_diff.json | high | 3 | L | measurement |
| `seo-llms-txt-missing` | brak `/llms.txt` (tylko informacyjnie) | low | 1 | S | http |
