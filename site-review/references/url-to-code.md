# Mapowanie znaleziska na kod

Używaj tylko, gdy `context.json.repo` jest ustawione.

```bash
python3 "$SKILL_DIR/scripts/locate_code.py" "$REPO" --path /sciezka/strony --needle "tekst 1" --needle "tekst 2"
```

Wynik: `{"file", "line", "confidence": "pewne" | "prawdopodobne", "candidates": [...]}` albo `null`.

- `pewne` — tekst znaleziony w dokładnie jednym pliku trasy tej strony (lub jej layoucie).
- `prawdopodobne` — znaleziony poza plikami trasy; `candidates` ma do 3 miejsc.
- `null` — nie wpisuj `code_location`. Nigdy nie zgaduj pliku.

Obsługiwane konwencje tras: Next.js (`app/`, `pages/`, także w `src/`), Astro (`src/pages`), SvelteKit (`src/routes`), Nuxt (`pages/`). Segmenty `[x]`, `[...x]`, `[[...x]]`, grupy `(x)`. Vite + React Router i nieznane frameworki → tylko szerokie wyszukiwanie w `src/`, `app/`, `pages/`, `components/` i plikach w katalogu głównym.

## Jakie `needles` brać

| znalezisko | needle |
|---|---|
| title / description / canonical | dokładna wartość z `basics.json` (title, description) albo `canonical`, `metadata`, `generateMetadata`, `<title` |
| H1, nagłówki, CTA, teksty | dokładny, krótki (3–8 słów), unikalny fragment tekstu ze strony |
| obraz | nazwa pliku z URL obrazka (`hero.jpg`) |
| element z klasą | charakterystyczna nazwa klasy CSS z HTML |
| skrypt zewnętrzny / tracker | domena (`googletagmanager.com`) lub ID (`GTM-XXXX`) |

Teksty z treści CMS mogą nie występować w repo — wtedy `null` jest poprawnym wynikiem; w `fix` napisz, że zmiana jest w CMS.

Znaleziska z polem `needles` orkiestrator przetwarza sam: dla każdego bez `code_location` uruchamia `locate_code.py`, wpisuje wynik do pliku modułu i ponownie uruchamia `merge_findings.py`.
