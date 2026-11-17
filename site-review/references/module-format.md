# Format pliku modułu

Każdy moduł zapisuje dokładnie jeden plik `RUN/modules/<moduł>.json`. Skrypt `scripts/merge_findings.py` waliduje go funkcją `validate` z `scripts/findings.py` — niepoprawne znaleziska trafiają do `report.json.invalid`, a orkiestrator musi je poprawić.

```json
{
  "module": "seo",
  "depth": "pełny | płytki | pominięty",
  "reason": "co sprawdzono, czego nie i co by to pogłębiło (widać w raporcie)",
  "new_ids": ["seo-cos-nowego"],
  "findings": [ { "...": "znalezisko, niżej" } ]
}
```

## Znalezisko

| pole | wymagane | wartości |
|---|---|---|
| `id` | tak | z `references/finding-ids.md`; nowy tylko, gdy nic nie pasuje (niżej) |
| `module` | tak | `seo`, `speed`, `cro`, `design`, `code`, `pl` — moduł, który zgłasza |
| `tags` | nie | lista modułów, których problem dotyczy; zawsze zawiera własny moduł (np. `["seo", "code"]`, gdy poprawka jest w kodzie) |
| `severity` | tak | `critical`, `high`, `medium`, `low` |
| `title` | tak | jedno zdanie zrozumiałe dla właściciela strony |
| `url` | tak | adres strony z `context.json.pages` (dokładnie taki zapis — inaczej znaleziska się nie scalą) |
| `evidence` | tak* | `{"type", "detail", "path"?}`; bez dowodu znalezisko trafia do „Do weryfikacji” i nie obniża oceny |
| `evidence.type` | tak* | `http` (status, nagłówek, odpowiedź), `dom` (fragment HTML), `screenshot` (zrzut; wtedy `path`), `measurement` (liczba z pomiaru: Lighthouse, metrics.json), `file` (plik w repo) |
| `evidence.detail` | tak* | konkret: wartość, element, liczba, cytat |
| `evidence.path` | nie | ścieżka względem `RUN` (np. `shots/0/shot-375-fold.jpg`); osadzają się tylko pliki ≤ 300 KB z katalogu przebiegu |
| `fix` | tak | konkretna zmiana: co, gdzie, na co |
| `impact` | tak | liczba 1–3 (3 = duży wpływ na ruch/konwersję/zgodność) |
| `effort` | tak | `S` (godziny), `M` (dzień–dwa), `L` (więcej) |
| `source` | tak | `fallback` (checklista), `lighthouse`, `render_diff`, `browser` albo nazwa użytego skilla |
| `needles` | nie | teksty do szukania w repo (`references/url-to-code.md`) |
| `code_location` | nie | `{"file", "line", "confidence"}` — tylko z odczytu pliku lub `locate_code.py`, nigdy zgadywane |

## Zasady

- **Problem całej witryny** (ten sam brak na wszystkich stronach: polityka prywatności, stopka, formularz kontaktowy, `llms.txt`, kolor przycisków) → jedno znalezisko z `url` strony startowej; w `evidence.detail` wypisz strony, na których występuje. Problem jednej podstrony → osobne znalezisko z jej `url`.
- **Severity z checklisty to wartość domyślna.** Możesz ją obniżyć o jeden poziom, gdy problem występuje tylko częściowo (np. CTA poniżej pierwszego ekranu, ale jest przyklejony pasek z przyciskiem) — napisz to w `evidence.detail`. Podnosić tylko z mocnym dowodem.
- **Nowe identyfikatory.** Jeśli żaden `id` z katalogu nie pasuje, utwórz `<moduł>-<krótki-opis>` (małe litery, myślniki) i dopisz go do `new_ids` w pliku modułu. Nie edytuj `finding-ids.md` — orkiestrator zbiera `new_ids` w `report.json` i pokazuje je użytkownikowi do dopisania.
- **Ten sam problem z kilku modułów** → ten sam `id` i ten sam `url`; scalanie przypisze go właściwemu modułowi po prefiksie `id`.
- Nie zmieniaj plików poza `RUN`.
