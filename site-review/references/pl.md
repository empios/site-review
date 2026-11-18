# Moduł: Zgodność PL

Ten moduł wskazuje typowe braki na polskich stronach i nie jest poradą prawną — raport musi to mówić, a przy wątpliwościach odsyłaj do prawnika.

Moduł uruchamia się, gdy `context.json.pl == true` (automatycznie dla `lang="pl…"` lub domeny `.pl`, albo z flagą `--pl`). Ocena tego modułu nie wchodzi do wyniku ogólnego — w raporcie to osobny znaczek zgodności.

## Instrukcja dla subagenta

Format wyniku i zasady wspólne (pola znaleziska, typy dowodu, problemy całej witryny, nowe identyfikatory): `references/module-format.md`.

Wejście: `speed.json` → `trackers_before_consent` (lista hostów śledzących załadowanych bez żadnej interakcji = przed zgodą), zrzuty 375/1440 px, `basics.json`, surowe HTML.

1. Fonty zewnętrzne: jeśli `speed.json` → `external_fonts_before_consent` jest niepuste → jedno znalezisko `pl-external-fonts` na stronie startowej z listą wszystkich hostów w dowodzie (to problem całej witryny). Tracking przed zgodą: jeśli `trackers_before_consent` jest niepuste → jedno znalezisko `pl-tracking-before-consent` na stronie startowej, dowód typu `measurement` z listą wszystkich hostów („załadowane przy otwarciu strony, bez kliknięcia w baner”).
2. Baner cookies: na zrzucie 375 px — czy jest baner, czy „Odrzuć” jest równie łatwe jak „Akceptuj” (ten sam poziom, podobna wielkość).
3. Linki prawne: w HTML szukaj linków do polityki prywatności, regulaminu, danych firmy (stopka).
4. Formularze: czy przy formularzu jest informacja o administratorze danych / link do polityki.
5. Tekst: jeśli jest skill `humanizer-polish` lub `anthropic-skills:humanizer-polish`, użyj go tylko do oceny (nie przepisuj strony) nagłówka i pierwszego akapitu strony głównej. Bez skilla pomiń `pl-copy-ai-sounding`.
6. Głębokość: `pełny`, gdy były kroki 1–4 z danymi Lighthouse (krok 5 jest opcjonalny i nie wpływa na głębokość); `płytki` bez danych o sieci. Zapisz `RUN/modules/pl.json`.

## Delegacja

- `humanizer-polish` / `anthropic-skills:humanizer-polish` — tylko ocena brzmienia tekstu.
- `legal:compliance-check` — opcjonalnie, gdy użytkownik chce głębszej analizy (nadal nie zastępuje prawnika).

## Checklista

| id | sprawdzenie | severity | impact | effort | dowód |
|---|---|---|---|---|---|
| `pl-tracking-before-consent` | hosty śledzące w ruchu przy ładowaniu strony | high | 3 | M | measurement |
| `pl-external-fonts` | `speed.json.external_fonts_before_consent` niepuste | low | 1 | S | measurement |
| `pl-cookie-banner-missing` | są trackery/cookies niekonieczne, brak banera | high | 3 | M | screenshot |
| `pl-cookie-reject-missing` | baner bez równie łatwego „Odrzuć” | medium | 2 | S | screenshot |
| `pl-privacy-policy-missing` | brak linku do polityki prywatności | high | 2 | S | dom |
| `pl-form-rodo-info-missing` | formularz zbiera dane bez informacji o administratorze/celu | medium | 2 | S | dom |
| `pl-company-data-missing` | strona sprzedaje lub podaje ceny (sklep, usługi B2C i B2B) bez nazwy firmy, adresu, NIP | medium | 2 | S | dom |
| `pl-terms-missing` | sklep/usługa bez regulaminu | medium | 2 | M | dom |
| `seo-lang-missing` | `lang` nie zaczyna się od `pl` na polskiej stronie | medium | 2 | S | dom |
| `pl-hreflang-pl-missing` | są wersje językowe, brak `hreflang="pl"` | low | 1 | S | dom |
| `pl-keyword-inflection` | fraza w title/H1 w nienaturalnej formie („buty damskie Warszawa tanio”) | low | 1 | S | dom |
| `pl-copy-ai-sounding` | ocena skilla humanizer: tekst brzmi sztucznie | low | 1 | M | dom |
