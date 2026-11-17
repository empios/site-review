# Moduł: Kod

## Instrukcja dla subagenta

Format wyniku i zasady wspólne (pola znaleziska, typy dowodu, problemy całej witryny, nowe identyfikatory): `references/module-format.md`.

Moduł działa tylko, gdy `context.json.repo` jest ustawione. Bez repo zapisz `{"module": "code", "depth": "pominięty", "reason": "brak repo", "findings": []}` i zakończ.

Wejście: repo, `context.json.framework`, znaleziska innych modułów (jeśli już są w `RUN/modules/`), `speed.json`.

1. To NIE jest pełny code review. Sprawdzasz tylko to, co wpływa na SEO, szybkość, bezpieczeństwo strony i zgodność — lista poniżej.
2. Delegacja: jeśli jest `security-review`, uruchom go na repo i weź tylko znaleziska dotyczące aplikacji webowej (nagłówki, sekrety, XSS). `engineering:code-review` użyj tylko na plikach z tras audytowanych stron (`route_map.route_to_files`). `modern-web-guidance` — jako źródło dobrych praktyk przy pisaniu `fix`.
3. Nie uruchamiaj builda ani instalacji zależności. Rozmiar bundla czytaj tylko z istniejącego wyniku (`.next/`, `dist/`, `build/`). `npm audit --omit=dev --json` uruchom tylko, gdy jest `package-lock.json` i `node_modules/` (nie modyfikuje plików).
4. Każde znalezisko ma `code_location` (`file` względem repo, `line`, `confidence`) — z bezpośredniego odczytu pliku albo z `locate_code.py`. Bez lokalizacji → bez `code_location`, nigdy zgadywane.
5. Głębokość: `pełny` z delegacją, `płytki` bez. Zapisz `RUN/modules/code.json`.

## Delegacja

- `security-review` — sekrety, nagłówki, podatności webowe.
- `engineering:code-review` — wybrane pliki tras, nie całe repo.
- `modern-web-guidance` — wzorce do poprawek.

## Checklista

| id | sprawdzenie | severity | impact | effort | dowód |
|---|---|---|---|---|---|
| `code-csr-only-seo-pages` | strony publiczne renderowane tylko w kliencie (np. `"use client"` na page + fetch w `useEffect`, SPA bez prerenderu) | high | 3 | L | file |
| `code-metadata-not-configured` | brak `metadata`/`generateMetadata` (Next), `<SEO>`/head w layoutach Astro/SvelteKit/Nuxt | medium | 2 | S | file |
| `code-img-not-optimized` | `<img>` zamiast komponentu obrazu frameworka dla dużych obrazów | low | 2 | M | file |
| `img-oversized` | plik w `public/`/`static/` > 500 KB użyty na stronie | medium | 3 | S | file |
| `code-bundle-large` | chunk startowy > 300 KB gzip w istniejącym buildzie | medium | 2 | L | file |
| `code-deps-vulnerable` | `npm audit` high/critical w zależnościach produkcyjnych | high | 2 | S | measurement |
| `code-deps-outdated` | framework ≥ 2 wersje główne za aktualną | low | 1 | L | file |
| `code-security-headers-missing` | brak CSP/HSTS/X-Content-Type-Options/Referrer-Policy w konfiguracji i w nagłówkach z basics.json | medium | 2 | S | http |
| `code-secret-in-client` | klucze API/sekrety w zmiennych publicznych (`NEXT_PUBLIC_`, `VITE_`, `PUBLIC_`) lub w kodzie klienta | critical | 3 | S | file |
| `code-console-logs` | `console.log` z danymi użytkownika w kodzie klienta | low | 1 | S | file |
