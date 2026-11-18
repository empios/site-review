# Katalog identyfikatorów znalezisk

Każde znalezisko używa `id` z tej listy. Ten sam problem zgłoszony przez kilka modułów MUSI mieć ten sam `id` (i ten sam `url`) — wtedy `merge_findings.py` scala go w jedną pozycję z kilkoma tagami. Jeśli żaden identyfikator nie pasuje, utwórz nowy w formacie `<moduł>-<krótki-opis>` i dopisz go tutaj przy najbliższej zmianie skilla.

`<form>` = `mobile` albo `desktop`. `<elem>` = `title`, `description`, `canonical` albo `h1`.

## Wspólne (kilka modułów)

| id | znaczenie | moduły |
|---|---|---|
| `img-oversized` | obraz dużo większy niż potrzebny (waga lub wymiary) | speed, design, code |
| `img-no-dimensions` | obraz bez `width`/`height` → przesunięcia układu | speed, design |
| `img-legacy-format` | JPEG/PNG tam, gdzie WebP/AVIF dałby dużą oszczędność | speed, code |
| `font-blocking` | fonty blokują renderowanie / brak `font-display` | speed, design |
| `seo-lang-missing` | brak lub błędny atrybut `lang` | seo, design, pl |

## SEO i indeksacja

| id | znaczenie |
|---|---|
| `seo-status-error` | strona zwraca 4xx/5xx |
| `seo-redirect-chain` | łańcuch > 1 przekierowania lub pętla |
| `seo-https-missing` | brak HTTPS lub brak przekierowania z HTTP |
| `seo-mixed-content` | zasoby HTTP na stronie HTTPS |
| `seo-robots-blocks` | `robots.txt` blokuje ważne strony lub zasoby |
| `seo-noindex` | `noindex` w meta robots na stronie, która powinna być w indeksie |
| `seo-x-robots-noindex` | `noindex` w nagłówku `X-Robots-Tag` |
| `seo-canonical-missing` | brak `link rel=canonical` |
| `seo-canonical-mismatch` | canonical wskazuje inny adres niż oczekiwany |
| `seo-sitemap-missing` | brak sitemapy |
| `seo-sitemap-page-missing` | audytowana strona nie występuje w sitemapie |
| `seo-sitemap-errors` | sitemap zawiera adresy z błędem lub przekierowaniem |
| `seo-title-missing` | brak `<title>` |
| `seo-title-length` | tytuł za krótki (< 15) lub za długi (> 60 znaków) |
| `seo-title-duplicate` | ten sam tytuł na kilku stronach |
| `seo-description-missing` | brak meta description |
| `seo-description-length` | description < 50 lub > 160 znaków |
| `seo-h1-missing` | brak H1 |
| `seo-h1-multiple` | kilka H1 na stronie |
| `seo-hreflang-invalid` | błędne lub nieodwzajemnione hreflang |
| `seo-schema-missing` | brak danych strukturalnych tam, gdzie mają sens |
| `seo-schema-invalid` | błędne dane strukturalne |
| `seo-og-missing` | brak tagów Open Graph |
| `seo-internal-links-broken` | linki wewnętrzne do 4xx/5xx |
| `seo-content-js-only` | większość treści dopiero po JS (z `render_diff.py`) |
| `seo-<elem>-js-only` | element tylko po JS (z `render_diff.py`) |
| `seo-llms-txt-missing` | brak `llms.txt` (informacyjnie) |

## Szybkość

| id | znaczenie |
|---|---|
| `speed-lcp-<form>` | LCP powyżej progu (z `lh_median.py`) |
| `speed-cls-<form>` | CLS powyżej progu (z `lh_median.py`) |
| `speed-tbt-<form>` | TBT powyżej progu (z `lh_median.py`) |
| `speed-field-poor` | dane CrUX (p75 od użytkowników) w kategorii słabej |
| `speed-ttfb-slow` | wolna odpowiedź serwera (TTFB > 800 ms) |
| `speed-render-blocking` | zasoby blokujące renderowanie |
| `speed-js-heavy` | dużo JavaScriptu na starcie |
| `speed-unused-js` | duża część JS nieużywana |
| `speed-no-compression` | brak gzip/brotli |
| `speed-no-cache-headers` | statyczne zasoby bez cache |
| `speed-third-party-heavy` | skrypty zewnętrzne kosztują dużo czasu |
| `speed-redirect` | wejście na stronę przechodzi przez przekierowanie (np. bez www → www), co dodaje czas |

## Marketing i konwersja

| id | znaczenie |
|---|---|
| `cro-value-prop-unclear` | nad zgięciem nie wiadomo, co to jest i dla kogo |
| `cro-cta-missing` | brak głównego wezwania do działania nad zgięciem |
| `cro-cta-weak` | CTA mało widoczne lub niejasne |
| `cro-cta-phone-only` | główne CTA na komputerze tylko dzwoni (`tel:`), bez formularza |
| `cro-cta-destination-mismatch` | CTA obiecuje jedno („Zamów audyt”), a prowadzi do formularza o czymś innym |
| `cro-cta-offpage-link` | CTA wyprowadza na inną stronę, choć ta ma własny formularz |
| `cro-cta-competing` | kilka równorzędnych CTA konkuruje ze sobą |
| `cro-mobile-cta-hidden` | na telefonie CTA poza pierwszym ekranem |
| `cro-trust-missing` | brak sygnałów zaufania (opinie, logotypy, liczby) |
| `cro-social-proof-missing` | brak dowodu społecznego przy decyzji |
| `cro-contact-missing` | trudno znaleźć dane kontaktowe |
| `cro-contact-email-private` | firmowy kontakt na prywatnej domenie poczty (gmail, yahoo…) |
| `cro-form-too-long` | formularz ma więcej pól niż potrzeba |
| `cro-pricing-unclear` | niejasna cena lub następny krok |
| `cro-message-mismatch` | title/description obiecują co innego niż strona |
| `cro-analytics-missing` | brak analityki (nie da się mierzyć konwersji) |
| `cro-og-image-missing` | brak obrazka do udostępnień |

## Design i dostępność

| id | znaczenie |
|---|---|
| `a11y-img-alt-missing` | obrazy treściowe bez `alt` |
| `a11y-contrast-low` | za niski kontrast tekstu |
| `a11y-tap-target-small` | elementy dotykowe < 24×24 px lub za blisko siebie |
| `a11y-focus-invisible` | niewidoczny focus klawiatury |
| `a11y-label-missing` | pola formularza bez etykiet |
| `a11y-heading-order` | nagłówki przeskakują poziomy |
| `design-viewport-missing` | brak `<meta name=viewport>` — telefon pokazuje stronę w wersji desktopowej, pomniejszoną |
| `design-horizontal-scroll` | przewijanie poziome na telefonie |
| `design-hierarchy-unclear` | brak jasnej hierarchii wizualnej |
| `design-typography-readability` | za mały tekst, za długie linie, słaby interlinia |
| `design-inconsistent-spacing` | niespójne odstępy i style komponentów |
| `design-layout-shift-visible` | widoczne skoki układu podczas ładowania |
| `design-console-errors` | błędy JS w konsoli |
| `design-dark-mode-broken` | tryb ciemny psuje czytelność |

## Kod

| id | znaczenie |
|---|---|
| `code-csr-only-seo-pages` | strony ważne dla SEO renderowane tylko po stronie klienta |
| `code-metadata-not-configured` | metadane nie są ustawiane mechanizmem frameworka |
| `code-img-not-optimized` | obrazy poza komponentem/pipeline'em optymalizacji |
| `code-bundle-large` | duży bundle startowy (z istniejącego builda) |
| `code-deps-vulnerable` | zależności ze znanymi podatnościami |
| `code-deps-outdated` | mocno przestarzałe zależności frameworka |
| `code-security-headers-missing` | brak nagłówków bezpieczeństwa (CSP, HSTS, X-Content-Type-Options, Referrer-Policy) |
| `code-secret-in-client` | sekret lub klucz w kodzie trafiającym do przeglądarki |
| `code-console-logs` | `console.log` z danymi w kodzie produkcyjnym |

## Zgodność PL

| id | znaczenie |
|---|---|
| `pl-tracking-before-consent` | skrypty śledzące ładują się przed zgodą |
| `pl-external-fonts` | fonty z zewnętrznego serwera (np. Google Fonts) ładowane przed zgodą — przekazują IP odwiedzającego |
| `pl-cookie-banner-missing` | brak banera zgody przy cookies niekoniecznych |
| `pl-cookie-reject-missing` | brak równie łatwej opcji „odrzuć” |
| `pl-privacy-policy-missing` | brak linku do polityki prywatności |
| `pl-form-rodo-info-missing` | formularz bez klauzuli informacyjnej RODO |
| `pl-company-data-missing` | brak danych firmy (nazwa, adres, NIP/KRS) przy sprzedaży |
| `pl-terms-missing` | brak regulaminu sklepu/usługi |
| `pl-hreflang-pl-missing` | wersje językowe bez `hreflang="pl"` |
| `pl-keyword-inflection` | fraza w title/H1 w nienaturalnej formie (bez odmiany) |
| `pl-copy-ai-sounding` | tekst brzmi jak generowany automatycznie |

## Dawne identyfikatory

Te identyfikatory nie są już używane. `--recheck` traktuje je jak ich następców (`scripts/findings.py` → `ALIASES`), więc zmiana nazwy nie wygląda jak „naprawione + nowe”. Przy zmianie nazwy w katalogu dopisz parę tutaj i w `ALIASES`.

| dawny | obecny |
|---|---|
| `cro-cta-tel-desktop` | `cro-cta-phone-only` |
| `speed-redirect-apex` | `speed-redirect` |
