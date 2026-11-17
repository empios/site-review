# Moduł: Marketing i konwersja

## Instrukcja dla subagenta

Format wyniku i zasady wspólne (pola znaleziska, typy dowodu, problemy całej witryny, nowe identyfikatory): `references/module-format.md`.

Wejście: zrzuty `RUN/shots/<n>/shot-375.png`, `shot-1440.png` (cała strona — do oceny) i `shot-375-fold.jpg`, `shot-1440-fold.jpg` (pierwszy ekran — do dowodu w raporcie) dla każdej strony, `basics.json` (title, description, og, linki), `speed.json` → `analytics_detected` (analityka wykryta w ruchu sieciowym, także własna, np. Vercel Analytics), surowe HTML.

1. Najpierw ustal cel strony z treści (sprzedaż, zapis, kontakt, pobranie, informacja) i wpisz go w `reason`. Bez celu nie da się ocenić konwersji.
2. Jeśli jest skill z sekcji Delegacja — użyj go na zrzutach i treści strony głównej oraz najważniejszej strony docelowej; wyniki przetłumacz według `references/delegation.md`. Głębokość `pełny`.
3. W przeciwnym razie przejdź checklistę. Głębokość `płytki`.
4. Zapisz `RUN/modules/cro.json`.

Zasady: dowodem jest zrzut ekranu (`evidence.type = "screenshot"`, `evidence.path` = ścieżka względem `RUN`, najlepiej `shots/<n>/shot-375-fold.jpg` lub `shot-1440-fold.jpg` — tylko te lekkie pliki osadzają się w raporcie) plus opis tego, co na nim widać, albo cytat z HTML. Nie wysyłaj formularzy, licz pola w HTML. Unikaj ogólników („popraw copy”): napisz, co konkretnie zmienić i gdzie. Pisz dla właściciela strony, bez żargonu.

## Delegacja

- `marketingskills` (`page-cro` w v1, `cro` w v2; Corey Haines) — heurystyki konwersji strony.
- `marketingskills` `copywriting` — tylko gdy problemem jest tekst nagłówka/CTA.

## Checklista

| id | sprawdzenie | severity | impact | effort | dowód |
|---|---|---|---|---|---|
| `cro-value-prop-unclear` | na 375 i 1440 px pierwszy ekran nie mówi, co to i dla kogo | high | 3 | M | screenshot |
| `cro-cta-missing` | brak głównego przycisku akcji w pierwszym ekranie | high | 3 | S | screenshot |
| `cro-cta-weak` | CTA słabo widoczne (kolor, rozmiar) lub ogólne („Wyślij”, „Kliknij”) | medium | 2 | S | screenshot |
| `cro-cta-phone-only` | na 1440 px główne CTA w pierwszym ekranie to tylko `tel:` | medium | 2 | S | screenshot |
| `cro-cta-offpage-link` | CTA prowadzi na inną stronę, choć bieżąca ma formularz | low | 1 | S | dom |
| `cro-cta-competing` | ≥ 3 równorzędne przyciski w pierwszym ekranie | medium | 2 | S | screenshot |
| `cro-mobile-cta-hidden` | na 375 px CTA poza pierwszym ekranem | medium | 3 | S | screenshot |
| `cro-trust-missing` | brak opinii, logotypów klientów, liczb, certyfikatów | medium | 2 | M | screenshot |
| `cro-social-proof-missing` | brak dowodu społecznego przy cenie/formularzu | low | 2 | M | screenshot |
| `cro-contact-missing` | brak telefonu/maila/formularza kontaktu w nagłówku lub stopce | medium | 2 | S | dom |
| `cro-contact-email-private` | kontakt firmowy na gmail/yahoo/wp/onet/o2/interia | low | 1 | S | dom |
| `cro-form-too-long` | formularz kontaktu/zapisu > 5 pól | medium | 2 | S | dom |
| `cro-pricing-unclear` | strona ofertowa bez ceny lub jasnego następnego kroku | medium | 2 | M | screenshot |
| `cro-message-mismatch` | title/description obiecują co innego niż nagłówek strony | medium | 2 | S | dom |
| `cro-analytics-missing` | `speed.json.analytics_detected` puste | medium | 2 | S | measurement |
| `cro-og-image-missing` | brak `og:image` (udostępnienia wyglądają źle) | low | 1 | S | dom |
