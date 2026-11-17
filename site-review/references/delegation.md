# Delegacja do skilli specjalistycznych

Orkiestrator sprawdza listę skilli dostępnych w sesji (lista z promptu systemowego, nazwy z prefiksem pluginu też się liczą) i zapisuje je w `context.json` → `available_skills`. Subagent modułu używa skilla tylko wtedy, gdy jest na tej liście. Nazwy skilli zmieniają się między wersjami — dopasowuj po nazwie i opisie, nie tylko po dokładnym ciągu.

| moduł | skille (kolejność preferencji) | bez nich |
|---|---|---|
| `seo` | `claude-seo` / `seo-audit`; `squirrelscan` `audit-website`; `seo-ai-visibility` (uzupełniająco) | checklista `seo.md` → `płytki` |
| `speed` | `web-quality-skills` / `web-quality-audit`; Lighthouse MCP | `lighthouse_runs.sh` + `lh_median.py` → `pełny` (pomiar jest pełny bez delegacji) |
| `cro` | `marketingskills` `page-cro` lub `cro`; `copywriting` | checklista `cro.md` → `płytki` |
| `design` | `design:design-critique`; `design:accessibility-review`; `web-design-guidelines` | Lighthouse accessibility + zrzuty + checklista → `płytki` |
| `code` | `security-review`; `engineering:code-review` (tylko pliki tras); `modern-web-guidance` | checklista `code.md` → `płytki` |
| `pl` | `humanizer-polish` (tylko ocena tekstu); `legal:compliance-check` (opcjonalnie) | checklista `pl.md` |

## Jak tłumaczyć wyniki skilla na schemat

1. Każdy problem zgłoszony przez skill → jedno znalezisko w schemacie z `scripts/findings.py` (`id`, `module`, `tags`, `severity`, `title`, `url`, `evidence`, `fix`, `impact`, `effort`, `source`).
2. `id`: dopasuj do `references/finding-ids.md`. Gdy nic nie pasuje — `<moduł>-<krótki-opis>` (małe litery, myślniki).
3. `source`: nazwa skilla (np. `claude-seo`, `design-critique`).
4. Severity skilla mapuj tak: krytyczne/błąd blokujący → `critical`; ważne/error → `high`; ostrzeżenie/warning → `medium`; sugestia/info → `low`.
5. `evidence`: przenieś konkretny dowód podany przez skill (wartość, element, zrzut, pomiar). Jeśli skill nie podał dowodu, a nie możesz go potwierdzić własnym pomiarem — zostaw znalezisko bez `evidence` (trafi do „Do weryfikacji”, nie wpłynie na ocenę).
6. Nie przepisuj ocen punktowych skilla do naszej skali. Ocena obszaru liczona jest wyłącznie z naszych znalezisk (`scripts/scoring.py`); jeśli skill ma własny wynik, wpisz go w `reason` modułu jako informację.
7. Duplikaty z checklistą są w porządku — `merge_findings.py` scali je po `(id, url)`.

## Głębokość modułu

- `pełny` — moduł użył skilla specjalistycznego albo pełnego pomiaru (Lighthouse dla szybkości).
- `płytki` — tylko checklista fallback albo niepełne dane (np. brak przeglądarki dla designu). W `reason` napisz, co by to odblokowało („doinstaluj claude-seo”, „dodaj PSI_API_KEY”).
- `pominięty` — moduł nie mógł działać (brak repo, strona nieosiągalna, flaga `--only`). `reason` obowiązkowy.
