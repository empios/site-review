# site-review — plan implementacji

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Osobisty skill Claude Code `site-review`, który audytuje stronę/apkę webową w 6 obszarach i oddaje jeden raport HTML z oceną, priorytetami i lokalizacją problemów w kodzie.

**Architecture:** `SKILL.md` orkiestruje: rozpoznanie skryptami → subagent na moduł (delegacja do zainstalowanych skilli lub checklista fallback) → każdy moduł zapisuje JSON znalezisk → deterministyczne skrypty Pythona walidują, deduplikują, oceniają, liczą priorytety i renderują raport. Cała logika liczbowa jest w kodzie (stabilność ocen), osąd jakościowy w modelu.

**Tech Stack:** Python 3 (tylko biblioteka standardowa, testy `unittest`), Bash, Chrome headless, Lighthouse CLI przez `npx` (wersja przypięta), Markdown dla SKILL.md i checklist.

**Spec:** `docs/2026-11-17-site-review-design.md`

## Global Constraints

- Źródło skilla: `/Users/pawelwlodarczyk/Documents/review-website/site-review/`; instalacja przez symlink `~/.claude/skills/site-review` → ten katalog.
- Python: tylko stdlib, bez `pip install`. Testy: `python3 -m unittest discover -s tests -v` z katalogu głównego projektu.
- Kary: critical 25, high 10, medium 4, low 1; ocena modułu = max(0, 100 − Σ kar).
- Wagi oceny ogólnej: seo 25, speed 20, cro 20, design 20, code 15; `pl` poza średnią; moduły pominięte poza średnią.
- Priorytet = impact (1–3) × waga wysiłku (S=3, M=2, L=1); „Zrób teraz” = top 10.
- Lighthouse: 3 przebiegi sekwencyjnie, mediana; mobile i desktop.
- Zakres v1: tylko strony publiczne i `localhost`; bez logowania, bez wysyłania formularzy; crawl z poszanowaniem `robots.txt`, 1 s odstępu między żądaniami, User-Agent `site-review/0.1`.
- `--pages` domyślnie 5, max 50. `--quick` = tylko strona główna, bez subagentów.
- Pliki robocze: `.site-review/<YYYY-MM-DD-HHMM>/` w katalogu audytowanego projektu (gdy brak repo — w scratchpadzie sesji).
- Raport i komunikaty po polsku. Moduł PL domyślnie włączony, gdy `lang` zaczyna się od `pl` lub domena kończy się na `.pl`.
- Znalezisko bez dowodu → `confidence: "do weryfikacji"`, nie liczy się do ocen; `code_location` nigdy zgadywane.
- Statusy głębokości modułu: `pełny`, `płytki`, `pominięty`.

## Review Focus

1. Treść strony z HTML/skryptami w title, alt, tekście → raport musi to escapować (raport to publikowany Artifact). Test w Task 8.
2. Strona nieosiągalna, 4xx/5xx, pętla przekierowań, timeout → `fetch_basics` zapisuje błąd zamiast się wysypać; orkiestrator oznacza moduły jako pominięte z powodem. Test w Task 4.
3. `robots.txt` blokuje podstrony albo brak sitemapy → wybór podstron z linków nawigacji, strony zablokowane nie są pobierane. Test w Task 4.
4. Lighthouse pada w części przebiegów (brak Chrome, timeout) → mediana z udanych; 0 udanych → moduł speed `pominięty` z powodem. Test w Task 6.
5. Monorepo / nieznany framework / brak trafienia trasy → brak `code_location`, a nie zgadywanie. Test w Task 7.

---

### Task 1: Szkielet projektu i test struktury

**Files:**
- Create: `.gitignore` (`.site-review/`, `__pycache__/`, `*.pyc`, `.DS_Store`)
- Create: `site-review/SKILL.md` (sam frontmatter + nagłówek; treść w Task 10)
- Create: `site-review/scripts/__init__.py` (pusty)
- Create: `tests/__init__.py`, `tests/helpers.py` (dodaje `site-review/scripts` do `sys.path`; stała `FIXTURES = tests/fixtures`)
- Test: `tests/test_layout.py`

**Interfaces:**
- Produces: `tests/helpers.py` z `SCRIPTS: Path`, `FIXTURES: Path`; importowany przez wszystkie testy jako `from tests.helpers import FIXTURES`.

- [ ] **Step 1: `git init` w katalogu projektu, gałąź `main`.**
- [ ] **Step 2: Write the failing test** `tests/test_layout.py::test_skill_frontmatter` — czyta `site-review/SKILL.md`, asercje: zaczyna się od `---`, zawiera `name: site-review`, zawiera linię `description:` o długości ≤ 1024 znaków.
- [ ] **Step 3: Run** `python3 -m unittest tests.test_layout -v` → FAIL (brak pliku).
- [ ] **Step 4: Create** pliki z listy. Opis w frontmatterze: po polsku i angielsku, triggery: „audyt strony”, „review strony”, „sprawdź SEO / szybkość / design strony”, „website audit”, „site review”.
- [ ] **Step 5: Run** test → PASS.
- [ ] **Step 6: Commit** `chore: scaffold site-review skill`.

---

### Task 2: Schemat znalezisk, reguła dowodu, deduplikacja

**Files:**
- Create: `site-review/scripts/findings.py`
- Test: `tests/test_findings.py`

**Interfaces:**
- Produces:
  - `SEVERITIES = ("critical", "high", "medium", "low")` (kolejność = ranga)
  - `MODULES = ("seo", "speed", "cro", "design", "code", "pl")`
  - `validate(f: dict) -> list[str]` — błędy; wymagane: `id, module, severity, title, fix, impact (int 1–3), effort (S|M|L), source`; `module ∈ MODULES`, `severity ∈ SEVERITIES`.
  - `apply_evidence_rule(f: dict, repo: str | None) -> dict` — kopia; `confidence = "do weryfikacji"` gdy brak `evidence` lub puste `evidence.detail`, w przeciwnym razie `"potwierdzone"`; usuwa `code_location`, gdy `repo is None`, plik `repo/file` nie istnieje albo `line < 1`.
  - `dedupe(findings: list[dict]) -> list[dict]` — klucz `(id, url)`; scalenie: `tags` = posortowana suma, `severity` = najwyższa, `source` = posortowane unikalne źródła złączone `+`, `evidence` i `module` z najpoważniejszego wpisu.

- [ ] **Step 1: Write failing tests:**
  - `test_validate_ok` — kompletne znalezisko → `[]`.
  - `test_validate_bad_impact` — `impact: 5` → lista zawiera błąd z `"impact"`.
  - `test_evidence_missing_marks_unverified` — brak `evidence` → `confidence == "do weryfikacji"`.
  - `test_code_location_dropped_without_repo` → klucza `code_location` brak.
  - `test_code_location_dropped_when_file_missing` (repo = `tempfile.TemporaryDirectory`, plik nie istnieje) → brak klucza.
  - `test_code_location_kept_when_file_exists` (plik utworzony, `line: 3`) → klucz jest.
  - `test_dedupe_merges_tags_and_max_severity` — dwa wpisy `id="img-oversized"`, ten sam `url`, moduły `speed`/`design`, severity `medium`/`high` → 1 wpis, `severity == "high"`, `tags == ["design", "speed"]`, `source == "fallback+lighthouse"`.
- [ ] **Step 2: Run** `python3 -m unittest tests.test_findings -v` → FAIL.
- [ ] **Step 3: Implement** funkcje z Interfaces w `findings.py`.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: findings schema, evidence rule, dedupe`.

---

### Task 3: Ocena, priorytety, ponowny audyt, CLI scalania

**Files:**
- Create: `site-review/scripts/scoring.py`, `site-review/scripts/recheck.py`, `site-review/scripts/merge_findings.py`
- Test: `tests/test_scoring.py`, `tests/test_merge.py`
- Fixture: `tests/fixtures/run1/modules/{seo,speed,design}.json`, `tests/fixtures/run1/context.json`

**Interfaces:**
- Consumes: `findings.validate`, `findings.apply_evidence_rule`, `findings.dedupe`, `findings.SEVERITIES`.
- Produces:
  - `scoring.PENALTY`, `scoring.WEIGHTS`, `scoring.EFFORT_WEIGHT` (wartości z Global Constraints)
  - `scoring.module_scores(findings: list[dict], depth: dict[str, str]) -> dict[str, dict]` → `{module: {"score": int | None, "depth": str, "count": int}}`; liczy tylko `confidence == "potwierdzone"`; `depth == "pominięty"` → `score None`.
  - `scoring.overall(scores: dict) -> int | None` — średnia ważona po `WEIGHTS`, pomija `pl` i `None`, `round()`.
  - `scoring.priority(f: dict) -> int`
  - `scoring.quadrant(f: dict) -> str` — `"quick win"` (impact ≥ 2 i effort S), `"duży projekt"` (impact ≥ 2 i effort M/L), `"drobiazg"` (impact 1).
  - `scoring.top(findings: list[dict], n: int = 10) -> list[dict]` — tylko potwierdzone; sort: priorytet malejąco, ranga severity, `id`.
  - `recheck.diff(prev: list[dict], curr: list[dict]) -> dict` → `{"fixed": [...], "still": [...], "new": [...]}` po kluczu `(id, url)`.
  - CLI: `python3 merge_findings.py --run DIR [--repo PATH] [--prev FILE]`. Czyta `DIR/modules/*.json` (każdy: `{"module", "depth", "reason", "findings": [...]}`). Zapisuje `DIR/findings.json` (lista po regule dowodu i deduplikacji) i `DIR/report.json`: `{"scores", "overall", "top", "quadrants": {nazwa: [ids]}, "unverified": [...], "invalid": [{"finding", "errors"}], "recheck": diff | null, "modules": {module: {"depth", "reason"}}}`. Błędne znaleziska trafiają do `invalid`, nie znikają po cichu.

- [ ] **Step 1: Write failing tests** w `test_scoring.py`:
  - `test_module_score_penalties` — seo: 1×critical + 2×medium → `score == 67`.
  - `test_score_floor_zero` — 5×critical → `0`.
  - `test_unverified_not_counted` — 1 critical „do weryfikacji” → `100`.
  - `test_skipped_module_none` — `depth["code"] = "pominięty"` → `score is None`.
  - `test_overall_excludes_pl_and_skipped` — seo 80, speed 60, pl 0, code None, cro/design 100 → `round((80*25 + 60*20 + 100*20 + 100*20) / 85) == 85`.
  - `test_priority_and_quadrant` — impact 3, effort S → `9`, `"quick win"`; impact 1, effort L → `1`, `"drobiazg"`.
  - `test_top_limits_and_orders` — 12 potwierdzonych → 10, pierwszy ma najwyższy priorytet.
  - `test_recheck_diff` — prev {A, B}, curr {B, C} → fixed [A], still [B], new [C].
  - `test_recheck_no_prev` — `diff([], curr)` → wszystko w `new`.
- [ ] **Step 2: Write failing test** `test_merge.py::test_merge_cli_end_to_end` — kopiuje `fixtures/run1` do temp, uruchamia CLI przez `subprocess`, asercje: `report.json` istnieje, `overall` jest int, `invalid` ma 1 pozycję (fixture zawiera jedno znalezisko z `impact: 7`), znalezisko `img-oversized` z seo i design scalone w 1.
- [ ] **Step 3: Run** `python3 -m unittest tests.test_scoring tests.test_merge -v` → FAIL.
- [ ] **Step 4: Implement** `scoring.py`, `recheck.py`, `merge_findings.py` (argparse).
- [ ] **Step 5: Run** → PASS.
- [ ] **Step 6: Commit** `feat: scoring, priorities, recheck, merge CLI`.

---

### Task 4: Rozpoznanie — pobranie podstaw strony

**Files:**
- Create: `site-review/scripts/fetch_basics.py`
- Test: `tests/test_fetch_basics.py`
- Fixture: `tests/fixtures/site/` — `index.html` (nav z linkami do `/a`, `/b`, `/private/x`; brak canonical; `<title>` z `<script>` w treści), `a.html`, `b.html`, `robots.txt` (`Disallow: /private/`), brak `sitemap.xml`; w teście serwowane przez `http.server` w wątku na wolnym porcie.

**Interfaces:**
- Produces:
  - `parse_meta(html: str) -> dict` → `{"title", "description", "canonical", "robots", "lang", "h1_count", "hreflang": [...], "og": {...}, "links": [...]}` (`html.parser`).
  - `select_pages(start: str, sitemap_urls: list[str], nav_links: list[str], n: int, robots: urllib.robotparser.RobotFileParser) -> list[str]` — start + do `n-1` podstron z tej samej domeny: najpierw sitemap, potem nav; bez zablokowanych przez robots; bez duplikatów; `n` ucięte do 50.
  - `fetch(url: str, timeout: int = 15) -> dict` → `{"status": int | None, "headers": dict, "body": str, "chain": [urls], "error": str | None}`; ręczne śledzenie przekierowań, max 10 (więcej → `error = "redirect loop"`).
  - CLI: `python3 fetch_basics.py URL --out DIR [--pages 5]` → `DIR/basics.json`: `{"start_url", "final_url", "chain", "status", "headers", "robots": {"status", "body"}, "sitemap": {"url", "status", "urls"}, "pages": [{"url", "status", "meta", "raw_html_path"}], "errors": [...], "pl_detected": bool}`; surowe HTML-e w `DIR/raw/`. Odstęp 1 s między żądaniami (stała `DELAY`, w testach nadpisywana na 0).

- [ ] **Step 1: Write failing tests:**
  - `test_parse_meta_basic` — z `fixtures/site/index.html`: `canonical is None`, `h1_count == 1`, `lang == "pl"`.
  - `test_select_pages_respects_robots` — `/private/x` nie jest w wyniku; `/a`, `/b` są.
  - `test_select_pages_no_sitemap_uses_nav` — `sitemap_urls=[]` → wynik niepusty z nav.
  - `test_fetch_unreachable` — `http://127.0.0.1:1/` → `status is None`, `error` niepusty, bez wyjątku.
  - `test_fetch_redirect_loop` — handler serwera z pętlą 301 → `error == "redirect loop"`.
  - `test_cli_writes_basics` — CLI na lokalnym serwerze → `basics.json` z 3 stronami, `pl_detected is True`, `sitemap.status == 404`.
- [ ] **Step 2: Run** `python3 -m unittest tests.test_fetch_basics -v` → FAIL.
- [ ] **Step 3: Implement** `fetch_basics.py` (urllib, robotparser, html.parser).
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: fetch basics, page selection, robots-aware crawl`.

---

### Task 5: Renderowanie — zrzuty ekranu i różnica HTML surowy vs wyrenderowany

**Files:**
- Create: `site-review/scripts/chrome.sh` (wspólne: znajduje Chrome — `$CHROME_PATH`, potem `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`, potem `google-chrome`/`chromium` z PATH; brak → exit 3 z komunikatem)
- Create: `site-review/scripts/screenshots.sh` — `screenshots.sh URL OUTDIR` → `shot-375.png`, `shot-768.png`, `shot-1440.png` (`--headless=new --screenshot --window-size=W,H --hide-scrollbars`, wysokość 2000)
- Create: `site-review/scripts/render_diff.py`
- Test: `tests/test_render_diff.py`
- Fixture: `tests/fixtures/csr/raw.html` (pusty `<div id="root">`), `tests/fixtures/csr/rendered.html` (pełna treść, H1, canonical)

**Interfaces:**
- Produces:
  - `render_diff.compare(raw_html: str, rendered_html: str) -> dict` → `{"raw_words": int, "rendered_words": int, "ratio": float, "missing_in_raw": [...]}`; `missing_in_raw` ⊆ `["title", "description", "canonical", "h1"]`; liczy słowa widocznego tekstu (bez `script`/`style`).
  - `render_diff.to_findings(diff: dict, url: str) -> list[dict]` — `ratio < 0.5` → `id="seo-content-js-only"`, severity `high`, module `seo`, tags `["seo","code"]`; każdy element `missing_in_raw` → `id="seo-<elem>-js-only"`, severity `medium`.
  - CLI: `python3 render_diff.py URL --raw FILE --out DIR` — wyrenderowany DOM przez `chrome.sh --dump-dom`; zapisuje `DIR/render_diff.json`.

- [ ] **Step 1: Write failing tests:** `test_compare_csr` (ratio < 0.5, `"h1" in missing_in_raw`), `test_compare_ssr_same` (ten sam HTML → ratio 1.0, `missing_in_raw == []`), `test_to_findings_csr` (zawiera `seo-content-js-only`, każde znalezisko przechodzi `findings.validate` bez błędów).
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** `render_diff.py`, `chrome.sh`, `screenshots.sh`.
- [ ] **Step 4: Run** testy → PASS. Ręcznie: `bash site-review/scripts/screenshots.sh https://example.com /tmp/x` → 3 pliki PNG > 0 B.
- [ ] **Step 5: Commit** `feat: screenshots and raw-vs-rendered diff`.

---

### Task 6: Szybkość, trackery przed zgodą, CrUX

**Files:**
- Create: `site-review/scripts/lighthouse_runs.sh` — `lighthouse_runs.sh URL OUTDIR` → `lh-mobile-{1,2,3}.json`, `lh-desktop-{1,2,3}.json`; sekwencyjnie; `npx -y lighthouse@<X.Y.Z>` (przypnij najnowszą stabilną z `npm view lighthouse version` w chwili implementacji; zapisz w zmiennej `LH_VERSION` na górze skryptu); Chrome przez `chrome.sh`; nieudany przebieg nie przerywa pozostałych.
- Create: `site-review/scripts/lh_median.py`, `site-review/scripts/trackers.py`, `site-review/scripts/crux.py`
- Test: `tests/test_speed.py`
- Fixture: `tests/fixtures/lh/` — 3 zminimalizowane raporty LH (tylko `categories.performance.score`, audyty `largest-contentful-paint`, `cumulative-layout-shift`, `total-blocking-time`, `first-contentful-paint`, `speed-index`, `network-requests`) + 1 plik uszkodzony; `tests/fixtures/psi.json`.

**Interfaces:**
- Produces:
  - `lh_median.median_run(reports: list[dict]) -> dict | None` → `{"performance": int (0–100), "lcp_ms", "cls", "tbt_ms", "fcp_ms", "si_ms", "runs": int}`; mediana per metryka; pomija raporty bez potrzebnych kluczy; 0 poprawnych → `None`.
  - `lh_median.speed_findings(summary: dict, url: str, form: str) -> list[dict]` — progi: LCP > 4000 → `high`, > 2500 → `medium`; CLS > 0.25 → `high`, > 0.1 → `medium`; TBT > 600 → `high`, > 200 → `medium`; id `speed-lcp|speed-cls|speed-tbt-<form>`; `evidence.type = "measurement"`, `source = "lighthouse"`.
  - CLI: `python3 lh_median.py DIR --url URL` → `DIR/speed.json` `{"mobile": summary | null, "desktop": summary | null, "findings": [...], "depth": "pełny" | "pominięty", "reason": str | null}`.
  - `trackers.TRACKER_HOSTS` (min.: `google-analytics.com`, `googletagmanager.com`, `connect.facebook.net`, `facebook.com/tr`, `doubleclick.net`, `analytics.tiktok.com`, `hotjar.com`, `clarity.ms`, `linkedin.com/px`, `snap.licdn.com`)
  - `trackers.before_consent(lh_report: dict) -> list[str]` — hosty z `network-requests` pasujące do listy (ładowanie strony bez interakcji = przed zgodą).
  - `crux.parse_psi(psi: dict) -> dict` → `{"available": bool, "lcp_p75", "inp_p75", "cls_p75", "category"}` z `loadingExperience`; brak danych → `available False`.
  - CLI `python3 crux.py URL --out DIR` — bez `PSI_API_KEY` w env zapisuje `{"available": false, "reason": "brak klucza PSI_API_KEY"}` i kończy z kodem 0.

- [ ] **Step 1: Write failing tests:** `test_median_three_runs` (wartości mediany z fixture), `test_median_skips_broken` (2 dobre + 1 uszkodzony → `runs == 2`), `test_median_none_when_all_broken` → `None`, `test_speed_findings_thresholds` (LCP 4500 → `high`, CLS 0.05 → brak znaleziska), `test_trackers_before_consent` (fixture z `googletagmanager.com` → na liście), `test_parse_psi` (p75 z fixture), `test_crux_cli_no_key` (env bez klucza → `available false`, exit 0).
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** skrypty.
- [ ] **Step 4: Run** testy → PASS. Ręcznie: `bash site-review/scripts/lighthouse_runs.sh https://example.com /tmp/lh && python3 site-review/scripts/lh_median.py /tmp/lh --url https://example.com` → `speed.json` z `runs == 3` dla obu form.
- [ ] **Step 5: Commit** `feat: lighthouse median, trackers before consent, crux`.

---

### Task 7: Mapowanie URL → kod

**Files:**
- Create: `site-review/scripts/route_map.py`, `site-review/scripts/locate_code.py`
- Test: `tests/test_route_map.py`
- Fixture: `tests/fixtures/repos/next-app/` (`package.json` z `next`, `app/page.tsx`, `app/produkt/[slug]/page.tsx` z `<h1>Produkt</h1>`, `app/layout.tsx` z `metadata`), `tests/fixtures/repos/astro/` (`astro.config.mjs`, `src/pages/index.astro`, `src/pages/blog/[...slug].astro`), `tests/fixtures/repos/unknown/` (sam `index.php`).

**Interfaces:**
- Produces:
  - `route_map.detect_framework(repo: str) -> str` ∈ `{"next-app", "next-pages", "astro", "sveltekit", "nuxt", "vite-react", "unknown"}` (po `package.json` zależnościach i obecności katalogów).
  - `route_map.route_to_files(repo: str, path: str) -> list[str]` — ścieżki względne plików trasy + layoutów nadrzędnych; obsługa segmentów dynamicznych `[x]`, `[...x]`, grup `(x)`; `vite-react`/`unknown` → `[]`.
  - `locate_code.locate(repo: str, url_path: str, needles: list[str]) -> dict | None` → `{"file", "line", "confidence": "pewne" | "prawdopodobne", "candidates": [...]}`. Kolejność: szukaj `needles` w plikach z `route_to_files`; jedno trafienie → `pewne`; brak/wiele → przeszukaj `src/`, `app/`, `pages/`, `components/` (pomijając `node_modules`, `.next`, `dist`), do 3 kandydatów → `prawdopodobne`; zero trafień → `None`.
  - CLI: `python3 locate_code.py REPO --path /produkt/x --needle "Produkt"` → JSON na stdout.

- [ ] **Step 1: Write failing tests:** `test_detect_next_app`, `test_detect_astro`, `test_detect_unknown`, `test_route_dynamic_segment` (`/produkt/abc` → zawiera `app/produkt/[slug]/page.tsx` i `app/layout.tsx`), `test_locate_certain` (needle `Produkt` → `pewne`, linia z `<h1>`), `test_locate_none_for_unknown_repo` (needle nieobecny → `None`), `test_locate_ignores_node_modules` (needle tylko w `node_modules/` → `None`).
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: url-to-code mapping`.

---

### Task 8: Raport HTML

**Files:**
- Create: `site-review/assets/report-template.html` — jedna strona, sekcje w kolejności ze specu §5.7 (Streszczenie, Karty ocen, Zrób teraz, Szczegóły per moduł jako `<details>`, Do weryfikacji, Metodologia); tokeny kolorów na `:root` + dark mode przez `prefers-color-scheme`; działa na szerokości 375 px; bez zewnętrznych skryptów; znaczniki `{{title}}`, `{{summary}}`, `{{scorecards}}`, `{{top}}`, `{{modules}}`, `{{unverified}}`, `{{method}}`, `{{recheck}}`.
- Create: `site-review/scripts/render_report.py`
- Test: `tests/test_render_report.py`

**Interfaces:**
- Consumes: format `report.json` i `findings.json` z Task 3.
- Produces:
  - `render(report: dict, findings: list[dict], summary: str, template: str, run_dir: str) -> str` — każda wartość pochodząca ze strony/znaleziska przez `html.escape`; zrzuty ekranu z `evidence.path` osadzane jako data URI, gdy plik ≤ 300 KB, inaczej tylko ścieżka; łączny rozmiar osadzeń ≤ 8 MB (reszta jako ścieżki).
  - Karty: wynik, głębokość, źródło; moduł `pominięty` pokazuje powód; `pl` jako znaczek zgodności, bez liczby w średniej.
  - Gdy `recheck` niepusty: sekcja z liczbą naprawionych/pozostałych/nowych.
  - CLI: `python3 render_report.py --run DIR --summary FILE` → `DIR/report.html`.

- [ ] **Step 1: Write failing tests:** `test_escapes_untrusted` (tytuł znaleziska `<script>alert(1)</script>` → w wyniku brak `<script>alert`, jest `&lt;script&gt;`), `test_sections_order` (indeksy nagłówków rosną w kolejności ze specu), `test_skipped_module_shows_reason`, `test_large_screenshot_not_embedded` (plik 400 KB → brak `data:image` dla niego), `test_recheck_section` (diff 2/1/3 → teksty z liczbami).
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** szablon i `render_report.py`.
- [ ] **Step 4: Run** → PASS; otwórz wygenerowany raport z fixture `run1` w przeglądarce, sprawdź 375 px i dark mode.
- [ ] **Step 5: Commit** `feat: html report`.

---

### Task 9: Checklisty, katalog identyfikatorów, delegacja

**Files:**
- Create: `site-review/references/seo.md`, `speed.md`, `cro.md`, `design.md`, `code.md`, `pl.md` — każdy: (1) sekcja „Instrukcja dla subagenta” (wejście: `context.json`, `basics.json`, artefakty; wyjście: `modules/<moduł>.json` w schemacie z `findings.py`; zakaz znalezisk bez dowodu); (2) „Delegacja” — który skill wywołać, jeśli jest dostępny; (3) checklista fallback 20–40 punktów z zakresu ze specu §5.3, każdy punkt z `id` z katalogu, domyślną severity, impact, effort i rodzajem dowodu.
- Create: `site-review/references/finding-ids.md` — katalog kanonicznych `id` (wspólnych dla modułów, np. `img-oversized` dla speed i design), żeby deduplikacja w Task 2 łapała ten sam problem.
- Create: `site-review/references/delegation.md` — tabela moduł → skille (`claude-seo`/`seo-audit`, `squirrelscan audit-website`, `web-quality-skills`, `marketingskills page-cro|cro`, `design:design-critique`, `design:accessibility-review`, `web-design-guidelines`, `engineering:code-review`, `security-review`, `modern-web-guidance`, `humanizer-polish`) + zasada tłumaczenia ich wyników na schemat (każde przetłumaczone znalezisko dostaje `source` = nazwa skilla; bez dowodu → do weryfikacji); kiedy moduł jest `pełny` vs `płytki`.
- Create: `site-review/references/scoring.md` — opis wag i kar dla czytelnika raportu (wartości z `scoring.py`, bez kopiowania logiki).
- Create: `site-review/references/url-to-code.md` — jak użyć `locate_code.py` i jakie `needles` brać (tekst H1, wartość meta, nazwa pliku obrazka, klasa CSS).
- Test: `tests/test_references.py`

- [ ] **Step 1: Write failing tests:** `test_all_reference_files_exist`; `test_checklist_ids_in_catalog` (każde `id` w backtickach w sekcjach checklist modułów występuje w `finding-ids.md`); `test_delegation_covers_modules` (każdy z `MODULES` ma wiersz w `delegation.md`); `test_pl_module_disclaimer` (`pl.md` zawiera „nie jest poradą prawną”).
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Write** pliki. Moduł PL: tracking przed zgodą bierze dowód z `trackers.before_consent`; CRO i design pracują na zrzutach z Task 5; speed na `speed.json` z Task 6; seo na `basics.json` i `render_diff.json`; code na repo + `locate_code.py`.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `docs: module checklists, finding ids, delegation map`.

---

### Task 10: SKILL.md — orkiestracja

**Files:**
- Modify: `site-review/SKILL.md`
- Test: `tests/test_layout.py` (dopisz testy)

**Interfaces:**
- Consumes: wszystkie CLI z Task 3–8 i pliki z Task 9 (ścieżki względem katalogu skilla).

Treść SKILL.md (≤ 500 linii, po polsku, odwołania do `references/` zamiast powielania):
1. Parsowanie wejścia i flag ze specu §5.1; tryb „tylko repo” → wykryj komendę dev z `package.json`, zaproponuj uruchomienie, audytuj `localhost`.
2. Granice bezpieczeństwa: tylko strony użytkownika lub takie, które ma prawo audytować; bez logowania; bez wysyłania formularzy; URL do PSI tylko dla publicznych adresów i informacja o tym w Metodologii.
3. Rozpoznanie: utwórz katalog przebiegu, uruchom `fetch_basics.py`, `render_diff.py`, `screenshots.sh`, `lighthouse_runs.sh` + `lh_median.py`, `crux.py`; sprawdź dostępne skille z listy sesji; zapisz `context.json` `{"url", "repo", "framework", "pages", "pl", "available_skills", "tools", "flags"}`; strona nieosiągalna → przerwij z jasnym komunikatem.
4. Moduły: `--quick` → sekwencyjnie w głównym wątku; pełny → subagent na moduł równolegle (Agent tool), każdy z instrukcją z `references/<moduł>.md`; Lighthouse nigdy równolegle.
5. Scalanie: `merge_findings.py` (z `--prev`, gdy `--recheck`), dla znalezisk z `code` lub tagiem `code` bez lokalizacji → `locate_code.py`; zapis i ponowne `merge_findings.py`.
6. Streszczenie: 4–5 zdań bez żargonu, wynik ogólny, 3 najważniejsze rzeczy → `summary.txt`; `render_report.py`; publikacja `report.html` jako Artifact.
7. Na koniec: lista 3 quick wins i pytanie, czy je naprawić (bez zgody nic nie zmieniaj); podpowiedź dopisania `.site-review/` do `.gitignore`.

- [ ] **Step 1: Write failing tests:** `test_skill_references_exist` (każda ścieżka `references/…` i `scripts/…` wymieniona w SKILL.md istnieje), `test_skill_length` (≤ 500 linii), `test_skill_mentions_flags` (zawiera `--quick`, `--pages`, `--only`, `--pl`, `--no-pl`, `--recheck`).
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Write** SKILL.md.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: orchestration in SKILL.md`.

---

### Task 11: Instalacja i test akceptacyjny

**Files:**
- Create: `tests/fixtures/acceptance/site/` — mała strona z zasianymi problemami: brak canonical, `noindex` na podstronie, obraz 3 MB bez `alt`, brak meta description, tracker GTM ładowany bez zgody, `lang="pl"`.
- Create: `tests/fixtures/acceptance/repo/` — kopia tej strony jako projekt `next-app` (tylko pliki, bez `node_modules`).
- Create: `docs/acceptance.md` — lista oczekiwanych znalezisk i wynik ręcznego przebiegu.

- [ ] **Step 1: Install:** `ln -s /Users/pawelwlodarczyk/Documents/review-website/site-review ~/.claude/skills/site-review`; sprawdź `ls -l ~/.claude/skills/site-review`.
- [ ] **Step 2: Run** cały zestaw testów `python3 -m unittest discover -s tests -v` → wszystkie PASS.
- [ ] **Step 3: Akceptacja quick:** serwuj `acceptance/site` przez `python3 -m http.server 8765`, w nowej sesji Claude Code: `/site-review http://localhost:8765 --quick`. Oczekiwane: raport zawiera `seo-canonical-missing`, `seo-noindex`, `img-oversized`, `a11y-img-alt-missing`, `pl-tracking-before-consent`; każde z dowodem; moduł code `pominięty` (brak repo).
- [ ] **Step 4: Akceptacja pełna z repo:** `/site-review http://localhost:8765 tests/fixtures/acceptance/repo`. Oczekiwane: jak wyżej + co najmniej 2 znaleziska z `code_location` wskazującym pliki w `app/`; brak `code_location` z pewnością `pewne` na pliku, który nie zawiera wskazanego tekstu.
- [ ] **Step 5: Stabilność:** uruchom `merge_findings.py` + `render_report.py` dwa razy na tym samym katalogu przebiegu → identyczne `report.json`.
- [ ] **Step 6: Recheck:** popraw canonical w fixture, `/site-review http://localhost:8765 --quick --recheck` → `seo-canonical-missing` w „naprawione”.
- [ ] **Step 7: Zapisz** wyniki w `docs/acceptance.md`; commit `test: acceptance run`.
- [ ] **Step 8: Prawdziwa strona:** poproś użytkownika o URL strony, którą posiada, i przejdź quick + pełny; rozbieżności wpisz do `docs/acceptance.md` jako zadania na v1.1.
