# Test akceptacyjny site-review v1

Data: 2026-11-17 · Strona testowa: `tests/fixtures/acceptance/site` (serwowana na `http://127.0.0.1:8765`) · Repo testowe: `tests/fixtures/acceptance/repo` (Next.js, app router). Obraz `hero.png` (~3 MB) generuje `python3 tests/fixtures/acceptance/make_assets.py tests/fixtures/acceptance` (nie jest w repo).

Zasiane problemy: brak canonical i meta description na stronie głównej, `noindex` na `/o-nas`, obraz 3 MB bez `alt` i wymiarów, GTM ładowany bez zgody, brak banera cookies i polityki prywatności, `lang="pl"`.

Przebieg wykonał model w tej samej sesji według `SKILL.md` (kroki skryptowe uruchomione dosłownie, moduły wypełnione według checklist w `references/`), a nie w nowej sesji przez `/site-review`.

## Wyniki

| krok | oczekiwane | wynik |
|---|---|---|
| Instalacja | skill widoczny w sesji | OK — symlink `~/.claude/skills/site-review`, skill pojawił się na liście skilli sesji |
| Testy jednostkowe | wszystkie zielone | OK — `python3 -m unittest discover -s tests -t .` |
| Quick (`--pages 1`, bez repo) | `seo-canonical-missing`, `img-oversized`, `a11y-img-alt-missing`, `pl-tracking-before-consent`, kod `pominięty` | OK — wszystkie obecne z dowodem; kod `pominięty` („brak repo”); wynik ogólny 86 |
| Pełny z repo (`--pages 3`) | jak wyżej + `seo-noindex`; ≥ 2 znaleziska z `code_location` | OK — 7 znalezisk z lokalizacją, wszystkie `pewne`, w każdym wskazana linia zawiera szukany tekst; wynik ogólny 82 |
| Stabilność | identyczny `report.json` przy ponownym scaleniu | OK — `cmp` bez różnic |
| `--recheck` po dodaniu canonical | `seo-canonical-missing` w „naprawione” | OK — fixed: 1, still: 14, new: 0 |
| Raport | czytelny na 375 px i w trybie ciemnym, bez przewijania poziomego | OK |

## Znalezione i naprawione podczas akceptacji

- **Zrzuty 375 px były w rzeczywistości 500 px.** Headless Chrome z `--window-size` nie schodzi poniżej ~500 px, więc zrzut „mobilny” był przyciętym widokiem 500 px — dawałby fałszywe „przewijanie poziome”. Naprawione: `scripts/screenshot.mjs` emuluje urządzenie przez DevTools Protocol (Node 22+), zapisuje `metrics.json` z prawdziwą szerokością; test `tests/test_screenshots.py`.
- Nowy identyfikator `design-viewport-missing` (strona bez `<meta name=viewport>` układa się na telefonie na ~980 px) — wykrywany z `metrics.json`.

## Ograniczenia tego testu

- Lighthouse i CrUX w przebiegu pełnym przejęte z przebiegu quick (ta sama strona startowa), żeby nie powtarzać 6 pomiarów.
- Moduły ocenił ten sam model, który pisał skill — test potwierdza, że instrukcje i skrypty działają razem, a nie niezależną jakość ocen.
- Nie testowano: delegacji do zewnętrznych skilli (claude-seo, marketingskills — niezainstalowane), subagentów równoległych, trybu „tylko repo” z uruchamianiem serwera.

## Do zrobienia (v1.1)

- Przebieg na prawdziwej stronie użytkownika w nowej sesji przez `/site-review` (quick i pełny).
- Lighthouse i porównanie HTML surowego z wyrenderowanym także dla podstron, nie tylko startowej.
