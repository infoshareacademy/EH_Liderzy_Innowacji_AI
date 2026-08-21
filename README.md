# EH — Liderzy Innowacji AI

Raport Streamlit dla przełożonych / HR wspierający ocenę puli kandydatów do programu Liderów Innowacji AI.

## Co zmieniło się względem pierwszego POC

Raport nie jest już zwykłym dashboardem wyników ankiety. Został przebudowany pod pytanie:

> Które osoby mają najlepsze połączenie myślenia biznesowego, kompetencji AI, zaplecza analitycznego i praktycznego podejścia do automatyzacji?

Raport zawiera:

- podsumowanie całej puli,
- ranking kandydatów,
- Indeks Dopasowania do roli Lidera Innowacji AI,
- indywidualną kartę kandydata,
- pięć wymiarów kompetencji,
- mapę biznes × AI/analityka,
- heatmapę kandydatów,
- analizę pytań otwartych,
- odpowiedzi i feedback każdego kandydata,
- pytania/obszary do weryfikacji w kolejnym etapie,
- kontrolę jakości danych,
- eksport rankingu do CSV.

## Pięć wymiarów

- Biznes i ROI — 30%
- AI i analityka — 25%
- Automatyzacja i agenci — 20%
- Prompting — 15%
- Bezpieczeństwo i krytyczne myślenie — 10%

Wagi są zapisane na początku `app.py` w słowniku `WEIGHTS` i można je łatwo zmienić.

## Ważna uwaga o obecnych danych

Pytania otwarte mają łącznie maksimum 15 punktów, więc raport przyjmuje skalę 0–3 pkt na każde z pięciu pytań.

W części testowych rekordów nie ma szczegółowej punktacji P1–P15, mimo że jest suma pytań zamkniętych. Raport nadal działa, ale szczegółowa analiza pytań zamkniętych jest wtedy niedostępna.

## Uruchomienie na Windows

W folderze projektu:

```bash
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

Jeżeli komenda `streamlit` nie jest widoczna w PATH, zawsze można używać formy:

```bash
py -m streamlit run app.py
```

## Dane

Domyślnie aplikacja korzysta z:

`dane_testowe.csv`

Nowy eksport można też wgrać bezpośrednio z panelu bocznego aplikacji.

## Model rekomendacji

Progi POC:

- bardzo wysokie dopasowanie: indeks >= 75% + minimum 60% w Biznes i ROI i AI/analityce,
- wysokie dopasowanie: indeks >= 60% + minimum 50% w Biznes i ROI i AI/analityce,
- potencjał — do weryfikacji: indeks >= 45%,
- rozwój przed kolejnym etapem: indeks < 45%.

To model pomocniczy. Przed realnym wykorzystaniem w procesie należy skalibrować wagi i progi oraz połączyć raport z kolejnym etapem oceny człowieka.
