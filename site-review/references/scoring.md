# Jak liczona jest ocena

Wartości są zdefiniowane w `scripts/scoring.py` (`PENALTY`, `WEIGHTS`, `EFFORT_WEIGHT`). Ten plik je opisuje — przy zmianie wag zmień kod, a potem ten opis.

- **Ocena obszaru** = 100 − suma kar za potwierdzone znaleziska, minimum 0. Kary: krytyczne 25, wysokie 10, średnie 4, niskie 1.
- Znaleziska „do weryfikacji” (bez dowodu) nie obniżają oceny.
- **Wynik ogólny** = średnia ważona ocen obszarów: SEO 25, szybkość 20, marketing 20, design 20, kod 15. Obszary pominięte nie wchodzą do średniej (wagi pozostałych się normalizują). Zgodność PL nigdy nie wchodzi do średniej — to osobny znaczek.
- **Priorytet** znaleziska = wpływ (1–3) × waga wysiłku (S = 3, M = 2, L = 1). „Zrób teraz” to 10 potwierdzonych znalezisk o najwyższym priorytecie (remis: wyższa severity, potem `id`).
- **Ćwiartki**: quick win (wpływ ≥ 2, wysiłek S), duży projekt (wpływ ≥ 2, wysiłek M/L), drobiazg (wpływ 1).
- Stabilność: liczby liczy kod, nie model; pomiary szybkości to mediana z 3 przebiegów.
