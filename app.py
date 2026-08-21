
from pathlib import Path
import html
import re

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# KONFIGURACJA
# ============================================================
st.set_page_config(
    page_title="Liderzy Innowacji AI — raport dla przełożonych",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Wagi Indeksu Dopasowania do roli Lidera Innowacji AI.
# Można je łatwo zmienić po kalibracji assessmentu.
WEIGHTS = {
    "Biznes i ROI": 0.30,
    "AI i analityka": 0.25,
    "Automatyzacja i agenci": 0.20,
    "Prompting": 0.15,
    "Bezpieczeństwo i krytyczne myślenie": 0.10,
}

DIM_COLORS = {
    "Biznes i ROI": "#7C3AED",
    "AI i analityka": "#2563EB",
    "Automatyzacja i agenci": "#10B981",
    "Prompting": "#EC4899",
    "Bezpieczeństwo i krytyczne myślenie": "#F59E0B",
}

STATUS_COLORS = {
    "Bardzo wysokie dopasowanie": "#16A34A",
    "Wysokie dopasowanie": "#0284C7",
    "Potencjał – do weryfikacji": "#D97706",
    "Rozwój przed kolejnym etapem": "#64748B",
}

OPEN_MAX_PER_QUESTION = 3
CLOSED_MAX = 15
TOTAL_MAX = 30

COL = {
    "date": "Submit Date",
    "name": "Imię i nazwisko",
    "email": "Email",
    "department": "Dział",
    "closed_sum": "Suma punktów z pytań zamkniętych (Max 15)",
    "open_sum": "Suma punktów pytań otwartych",
    "total": "Ogólna punktacja",
    "pct": "Wynik procentowy",
}

OPEN_QUESTIONS = {
    1: {
        "short": "Innowacyjny use case AI",
        "dimension": "Biznes i ROI",
        "answer": "Pytanie otwarte 1: Zaproponuj pomysł na innowacyjne wykorzystanie AI w Twoim dziale, które rozwiąże konkretny problem biznesowy. Opisz problem, proponowane rozwiązanie oraz oczekiwany efekt.",
        "feedback": "Pytanie otwarte 1: Feedback dla respondenta",
        "score": "Pytanie otwarte 1: Punkty",
    },
    2: {
        "short": "Zaawansowany prompt",
        "dimension": "Prompting",
        "answer": "Pytanie otwarte 2: Napisz zaawansowany prompt, który przeanalizuje incydent i wyciągnie z niego 3 kluczowe wnioski. Zadbaj o rolę, cel, ograniczenia i format wyjściowy.",
        "feedback": "Pytanie otwarte 2: Feedback dla respondenta",
        "score": "Pytanie otwarte 2: Punkty",
    },
    3: {
        "short": "Proces o najwyższym ROI",
        "dimension": "Biznes i ROI",
        "answer": "Pytanie otwarte 3: Wskaż proces w organizacji, którego automatyzacja z użyciem AI przyniosłaby największy zwrot z inwestycji (ROI). Uzasadnij swój wybór pod kątem oszczędności czasu lub kosztów.",
        "feedback": "Pytanie otwarte 3: Feedback dla respondenta",
        "score": "Pytanie otwarte 3: Punkty",
    },
    4: {
        "short": "Ograniczenia i ryzyka AI",
        "dimension": "Bezpieczeństwo i krytyczne myślenie",
        "answer": "Pytanie otwarte 4: Jakie są potencjalne błędy lub ograniczenie technologiczne w działaniu narzędzi AI? W jaki sposób byś sobie z tym poradził(a)?",
        "feedback": "Pytanie otwarte 4: Feedback dla respondenta",
        "score": "Pytanie otwarte 4: Punkty",
    },
    5: {
        "short": "Doświadczenie z agentami AI",
        "dimension": "Automatyzacja i agenci",
        "answer": "Pytanie otwarte 5: Opisz swoje doświadczenie, tzn. czy tworzyłaś/eś już własnych Agentów AI? Jeżeli tak, to jakie było ich zadanie? Z jakich narzędzi korzystałaś/eś?",
        "feedback": "Pytanie otwarte 5: Feedback dla respondenta",
        "score": "Pytanie otwarte 5: Punkty",
    },
}

CLOSED_SHORT = {
    1: "ML vs tradycyjne programowanie",
    2: "RAG",
    3: "Halucynacje LLM",
    4: "Prompt Engineering",
    5: "Agent AI",
    6: "Python / analiza danych",
    7: "Human-in-the-loop",
    8: "Dane wrażliwe",
    9: "Prompt Injection",
    10: "Workflow + AI",
    11: "Context Window",
    12: "Odpowiedzialność za decyzję",
    13: "Koszty modeli",
    14: "Testowanie wdrożenia AI",
    15: "AI w pracy z kodem",
}

# ============================================================
# STYL
# ============================================================
st.markdown(
    """
    <style>
      :root {
        --purple: #7C3AED;
        --blue: #2563EB;
        --green: #10B981;
        --pink: #EC4899;
        --amber: #F59E0B;
        --ink: #111827;
        --muted: #667085;
        --card: #FFFFFF;
        --line: rgba(15, 23, 42, .09);
      }

      .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1550px;
      }

      [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #F7F5FF 0%, #F4F8FF 50%, #F6FBF9 100%);
        border-right: 1px solid var(--line);
      }

      .hero {
        position: relative;
        overflow: hidden;
        border-radius: 26px;
        padding: 1.65rem 1.8rem;
        color: white;
        background:
          radial-gradient(circle at 92% 15%, rgba(236,72,153,.55), transparent 26%),
          radial-gradient(circle at 72% 100%, rgba(16,185,129,.38), transparent 30%),
          linear-gradient(115deg, #3821A5 0%, #5B35D5 42%, #2563EB 100%);
        box-shadow: 0 18px 55px rgba(73, 47, 170, .18);
        margin-bottom: 1rem;
      }

      .hero-kicker {
        font-size: .76rem;
        font-weight: 800;
        letter-spacing: .16em;
        text-transform: uppercase;
        opacity: .80;
      }

      .hero-title {
        font-size: clamp(2.1rem, 4vw, 3.6rem);
        line-height: 1;
        font-weight: 860;
        letter-spacing: -.055em;
        margin: .35rem 0 .55rem 0;
      }

      .hero-sub {
        max-width: 930px;
        font-size: 1.02rem;
        line-height: 1.55;
        opacity: .90;
      }

      .kpi {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 1rem 1.05rem .95rem;
        min-height: 132px;
        box-shadow: 0 8px 28px rgba(15, 23, 42, .045);
      }

      .kpi-top {
        height: 4px;
        border-radius: 999px;
        margin: -.05rem 0 .75rem 0;
      }

      .kpi-label {
        font-size: .74rem;
        font-weight: 800;
        letter-spacing: .09em;
        text-transform: uppercase;
        color: #667085;
      }

      .kpi-value {
        font-size: 2.15rem;
        line-height: 1.1;
        font-weight: 850;
        color: #111827;
        letter-spacing: -.04em;
        margin: .25rem 0 .2rem;
      }

      .kpi-note {
        color: #667085;
        font-size: .82rem;
        line-height: 1.35;
      }

      .section-title {
        font-size: 1.43rem;
        line-height: 1.2;
        font-weight: 820;
        letter-spacing: -.025em;
        color: #111827;
        margin: .5rem 0 .2rem;
      }

      .section-sub {
        color: #667085;
        font-size: .9rem;
        margin-bottom: .85rem;
      }

      .insight {
        border: 1px solid rgba(124, 58, 237, .15);
        background: linear-gradient(90deg, rgba(124,58,237,.08), rgba(37,99,235,.05));
        border-radius: 16px;
        padding: 1rem 1.1rem;
        margin: .4rem 0 1rem;
        color: #273047;
      }

      .status {
        display: inline-block;
        border-radius: 999px;
        padding: .36rem .72rem;
        font-size: .78rem;
        font-weight: 800;
        color: white;
        margin-bottom: .45rem;
      }

      .profile-card {
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 1.15rem 1.2rem;
        background: white;
        box-shadow: 0 8px 28px rgba(15, 23, 42, .04);
      }

      .callout {
        border-left: 4px solid #7C3AED;
        background: #FAF8FF;
        border-radius: 11px;
        padding: .8rem 1rem;
        margin: .45rem 0;
      }

      .small {
        font-size: .80rem;
        color: #667085;
      }

      .legend-chip {
        display: inline-block;
        margin: .12rem .22rem .12rem 0;
        border-radius: 999px;
        padding: .33rem .65rem;
        border: 1px solid var(--line);
        background: white;
        font-size: .77rem;
        font-weight: 700;
      }

      div[data-testid="stMetric"] {
        background: white;
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: .8rem 1rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FUNKCJE
# ============================================================
def safe(value):
    if pd.isna(value):
        return "—"
    return html.escape(str(value))


def load_data(uploaded):
    if uploaded is not None:
        return pd.read_csv(uploaded)
    return pd.read_csv(Path(__file__).with_name("dane_testowe.csv"))


def validate_columns(df):
    required = list(COL.values())
    for q in OPEN_QUESTIONS.values():
        required.extend([q["answer"], q["feedback"], q["score"]])
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error("W pliku brakuje wymaganych kolumn:\n\n" + "\n".join(f"- {x}" for x in missing))
        st.stop()


def clean_department(value):
    if pd.isna(value):
        return "Brak działu"
    value = str(value).strip()
    if value in {"", "/", " /", "/ "}:
        return "Brak działu"
    return value


def prepare(df):
    out = df.copy()
    out["_source_row"] = np.arange(len(out))
    out[COL["date"]] = pd.to_datetime(out[COL["date"]], errors="coerce")

    numeric = [COL["closed_sum"], COL["open_sum"], COL["total"], COL["pct"]]
    numeric += [q["score"] for q in OPEN_QUESTIONS.values()]
    numeric += [f"P{i}. Punkty" for i in range(1, 16) if f"P{i}. Punkty" in out.columns]

    for c in numeric:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    out["Dział_clean"] = out[COL["department"]].apply(clean_department)
    out["Nazwa_clean"] = out[COL["name"]].fillna("Brak nazwy").astype(str).str.strip()
    out["Email_clean"] = out[COL["email"]].fillna("").astype(str).str.strip().str.lower()

    # 5 wymiarów profilu lidera.
    out["AI i analityka"] = (out[COL["closed_sum"]] / CLOSED_MAX * 100).clip(0, 100)
    out["Biznes i ROI"] = (
        (out[OPEN_QUESTIONS[1]["score"]] + out[OPEN_QUESTIONS[3]["score"]])
        / (2 * OPEN_MAX_PER_QUESTION) * 100
    ).clip(0, 100)
    out["Prompting"] = (
        out[OPEN_QUESTIONS[2]["score"]] / OPEN_MAX_PER_QUESTION * 100
    ).clip(0, 100)
    out["Bezpieczeństwo i krytyczne myślenie"] = (
        out[OPEN_QUESTIONS[4]["score"]] / OPEN_MAX_PER_QUESTION * 100
    ).clip(0, 100)
    out["Automatyzacja i agenci"] = (
        out[OPEN_QUESTIONS[5]["score"]] / OPEN_MAX_PER_QUESTION * 100
    ).clip(0, 100)

    # Indeks ważony profilem roli.
    out["Indeks dopasowania"] = 0.0
    for dim, weight in WEIGHTS.items():
        out["Indeks dopasowania"] += out[dim].fillna(0) * weight

    # Pokrycie szczegółowych danych P1-P15.
    detail_cols = [f"P{i}. Punkty" for i in range(1, 16) if f"P{i}. Punkty" in out.columns]
    if detail_cols:
        out["Pokrycie P1-P15"] = out[detail_cols].notna().sum(axis=1) / len(detail_cols) * 100
    else:
        out["Pokrycie P1-P15"] = 0.0

    out["Rekomendacja"] = out.apply(recommendation_status, axis=1)
    return out


def recommendation_status(row):
    score = float(row.get("Indeks dopasowania", 0) or 0)
    business = float(row.get("Biznes i ROI", 0) or 0)
    foundation = float(row.get("AI i analityka", 0) or 0)

    # Progi demonstracyjne. Dwa najważniejsze warunki brzegowe:
    # biznes/ROI i fundament AI/analityczny.
    if score >= 75 and business >= 60 and foundation >= 60:
        return "Bardzo wysokie dopasowanie"
    if score >= 60 and business >= 50 and foundation >= 50:
        return "Wysokie dopasowanie"
    if score >= 45:
        return "Potencjał – do weryfikacji"
    return "Rozwój przed kolejnym etapem"


def latest_per_person(df, identity_mode):
    work = df.copy()

    if identity_mode == "E-mail":
        # E-mail jest kluczem docelowym. Dla testowych rekordów bez e-maila
        # stosujemy fallback do nazwy.
        work["_person_key"] = np.where(
            work["Email_clean"].ne(""),
            "email:" + work["Email_clean"],
            "name:" + work["Nazwa_clean"].str.lower(),
        )
    else:
        work["_person_key"] = "name:" + work["Nazwa_clean"].str.lower()

    work = work.sort_values(
        [COL["date"], "_source_row"],
        na_position="first"
    )
    return work.drop_duplicates("_person_key", keep="last").reset_index(drop=True)


def remove_exact_duplicates(df):
    # Ignorujemy techniczną kolumnę indeksu.
    cols = [c for c in df.columns if c != "_source_row"]
    return df.drop_duplicates(subset=cols, keep="last").reset_index(drop=True)


def format_pct(v):
    if pd.isna(v):
        return "—"
    return f"{float(v):.0f}%"


def kpi(label, value, note, color):
    st.markdown(
        f"""
        <div class="kpi">
          <div class="kpi-top" style="background:{color};"></div>
          <div class="kpi-label">{safe(label)}</div>
          <div class="kpi-value">{safe(value)}</div>
          <div class="kpi-note">{safe(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_figure(fig, height=390):
    fig.update_layout(
        height=height,
        margin=dict(l=15, r=15, t=58, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", color="#344054"),
        title_font=dict(size=17, color="#111827"),
        legend_title_text="",
        hoverlabel=dict(font_size=13),
    )
    fig.update_xaxes(gridcolor="rgba(15,23,42,.07)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(15,23,42,.07)", zeroline=False)
    return fig


def executive_insight(df):
    dims = list(WEIGHTS.keys())
    means = df[dims].mean().sort_values(ascending=False)
    strongest = means.index[0]
    weakest = means.index[-1]
    n_recommended = int(df["Rekomendacja"].isin(
        ["Bardzo wysokie dopasowanie", "Wysokie dopasowanie"]
    ).sum())

    return (
        f"Najmocniejszym obszarem badanej puli jest <b>{safe(strongest)}</b> "
        f"({means.iloc[0]:.0f}%), a największą luką <b>{safe(weakest)}</b> "
        f"({means.iloc[-1]:.0f}%). "
        f"Według proponowanego modelu <b>{n_recommended}</b> "
        f"{'osoba spełnia' if n_recommended == 1 else 'osób spełnia'} próg rekomendacji "
        f"do kolejnego etapu."
    )


def candidate_text(row):
    status = row["Rekomendacja"]
    if status == "Bardzo wysokie dopasowanie":
        return (
            "Profil bardzo dobrze odpowiada założeniom roli Lidera Innowacji AI. "
            "Kandydat łączy mocny fundament AI/analityczny z myśleniem biznesowym "
            "i warto go zaprosić do kolejnego etapu weryfikacji."
        )
    if status == "Wysokie dopasowanie":
        return (
            "Profil jest dobrze dopasowany do charakteru programu. "
            "Rekomendowane jest przejście do kolejnego etapu i pogłębienie praktycznych "
            "przykładów wykorzystania AI w procesach biznesowych."
        )
    if status == "Potencjał – do weryfikacji":
        return (
            "Wynik pokazuje istotny potencjał, ale profil jest nierówny. "
            "Kolejny etap powinien zweryfikować najmocniejsze kompetencje oraz obszary, "
            "które mogą ograniczać samodzielne prowadzenie inicjatyw AI."
        )
    return (
        "Obecny profil nie daje jeszcze mocnego sygnału gotowości do roli Lidera Innowacji AI. "
        "Warto najpierw wzmocnić wskazane kompetencje i ponownie zweryfikować gotowość."
    )


def strengths_and_gaps(row):
    dims = list(WEIGHTS.keys())
    values = {d: float(row[d]) for d in dims if pd.notna(row[d])}
    ordered = sorted(values.items(), key=lambda x: x[1], reverse=True)

    strengths = [d for d, v in ordered if v >= 60][:3]
    if not strengths and ordered:
        strengths = [ordered[0][0]]

    gaps = [d for d, v in ordered[::-1] if v < 50][:3]
    if not gaps and ordered:
        gaps = [ordered[-1][0]]

    return strengths, gaps


def verification_points(row):
    points = []
    if row["Biznes i ROI"] < 50:
        points.append("Poprosić o konkretny przykład procesu i policzenie oszczędności czasu/kosztów.")
    if row["AI i analityka"] < 50:
        points.append("Zweryfikować praktyczny fundament techniczno-analityczny, szczególnie pracę z danymi i kodem.")
    if row["Automatyzacja i agenci"] < 50:
        points.append("Sprawdzić praktyczne doświadczenie z automatyzacjami, workflow lub agentami AI.")
    if row["Prompting"] < 50:
        points.append("Zweryfikować umiejętność precyzyjnego definiowania roli, celu, ograniczeń i formatu wyniku.")
    if row["Bezpieczeństwo i krytyczne myślenie"] < 50:
        points.append("Pogłębić świadomość ograniczeń AI, sposobów walidacji i kontroli ryzyka.")
    return points or ["Pogłębić przykłady praktycznych wdrożeń i rolę kandydata w ich realizacji."]


def feedback_gap_summary(df):
    feedback = " ".join(
        df[q["feedback"]].fillna("").astype(str).str.lower().str.cat(sep=" ")
        for q in OPEN_QUESTIONS.values()
    )

    patterns = {
        "Brak mierzalnego efektu / ROI": [
            r"mierzal", r"ile godzin", r"skali korzy", r"wymiar biznes", r"oszczędno"
        ],
        "Zbyt ogólna odpowiedź": [
            r"bardzo ogóln", r"doprecyz", r"więcej szczegół", r"konkretn"
        ],
        "Brak ograniczeń / struktury promptu": [
            r"brakuje.*ogranic", r"format wyjści", r"struktury", r"rolę.*cel"
        ],
        "Brak walidacji / kontroli ryzyka": [
            r"weryfik", r"zabezpiec", r"minimaliz.*ryzyk", r"halucyn"
        ],
        "Za mało praktyki z agentami": [
            r"agent", r"narzędz", r"praktyczne doświadczenie", r"jak skonfigurow"
        ],
    }

    rows = []
    for label, pats in patterns.items():
        count = 0
        for pat in pats:
            count += len(re.findall(pat, feedback))
        rows.append({"Obszar": label, "Sygnały w feedbacku": count})
    return pd.DataFrame(rows).sort_values("Sygnały w feedbacku", ascending=True)


# ============================================================
# DANE I FILTRY
# ============================================================
with st.sidebar:
    st.markdown("## ⚡ Liderzy Innowacji AI")
    st.caption("Raport zarządczy / managerski")
    uploaded = st.file_uploader("Wczytaj nowy eksport CSV", type=["csv"])

raw = load_data(uploaded)
validate_columns(raw)
prepared = prepare(raw)

exact_before = len(prepared)
prepared = remove_exact_duplicates(prepared)
exact_removed = exact_before - len(prepared)

with st.sidebar:
    st.markdown("---")
    st.markdown("### Sposób liczenia osób")
    identity_mode = st.radio(
        "Identyfikacja respondenta",
        ["E-mail", "Imię i nazwisko"],
        index=0,
        help="W wersji produkcyjnej zalecany jest e-mail. W danych testowych część rekordów nie ma adresu, dlatego można przełączyć się na imię i nazwisko.",
    )
    attempts_mode = st.radio(
        "Podejścia do assessmentu",
        ["Ostatni wynik każdej osoby", "Wszystkie unikalne podejścia"],
        index=0,
    )

    if attempts_mode == "Ostatni wynik każdej osoby":
        data = latest_per_person(prepared, identity_mode)
    else:
        data = prepared.copy()

    st.markdown("---")
    st.markdown("### Filtry")

    departments = sorted(data["Dział_clean"].dropna().unique().tolist())
    dep_selection = st.multiselect("Dział", departments, default=departments)

    statuses = list(STATUS_COLORS.keys())
    status_selection = st.multiselect("Rekomendacja", statuses, default=statuses)

    if dep_selection:
        data = data[data["Dział_clean"].isin(dep_selection)]
    if status_selection:
        data = data[data["Rekomendacja"].isin(status_selection)]

    min_date = data[COL["date"]].min()
    max_date = data[COL["date"]].max()
    if pd.notna(min_date) and pd.notna(max_date):
        dr = st.date_input(
            "Zakres dat",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date(),
        )
        if isinstance(dr, tuple) and len(dr) == 2:
            data = data[
                (data[COL["date"]].dt.date >= dr[0]) &
                (data[COL["date"]].dt.date <= dr[1])
            ]

    st.markdown("---")
    st.caption(
        "Indeks dopasowania jest modelem pomocniczym. Przed wykorzystaniem w realnej selekcji "
        "należy zatwierdzić wagi i progi oraz połączyć wynik z dalszą oceną człowieka."
    )

if data.empty:
    st.warning("Brak rekordów dla wybranych filtrów.")
    st.stop()

data = data.sort_values(
    ["Indeks dopasowania", COL["pct"]],
    ascending=[False, False]
).reset_index(drop=True)
data["Miejsce"] = np.arange(1, len(data) + 1)

# ============================================================
# HERO + KPI
# ============================================================
st.markdown(
    """
    <div class="hero">
      <div class="hero-kicker">Raport dla przełożonych</div>
      <div class="hero-title">Potencjał Liderów Innowacji AI</div>
      <div class="hero-sub">
        Kto ma najlepsze połączenie myślenia biznesowego, kompetencji AI, zaplecza analitycznego
        i praktycznego podejścia do automatyzacji? Raport wspiera wybór osób do kolejnego etapu programu.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

avg_raw = data[COL["pct"]].mean()
avg_fit = data["Indeks dopasowania"].mean()
recommended_n = int(data["Rekomendacja"].isin(
    ["Bardzo wysokie dopasowanie", "Wysokie dopasowanie"]
).sum())
top_row = data.iloc[0]

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    kpi("Liczba osób", len(data), "Po zastosowaniu filtrów i zasad deduplikacji", "#7C3AED")
with k2:
    kpi("Średni wynik assessmentu", f"{avg_raw:.0f}%", "Wynik punktowy 0–30 pkt", "#2563EB")
with k3:
    kpi("Średni indeks dopasowania", f"{avg_fit:.0f}%", "Ważony pod kątem profilu roli", "#EC4899")
with k4:
    kpi("Rekomendowani", recommended_n, "Wysokie lub bardzo wysokie dopasowanie", "#10B981")
with k5:
    kpi("Najwyższe dopasowanie", f"{top_row['Indeks dopasowania']:.0f}%", safe(top_row["Nazwa_clean"]), "#F59E0B")

st.markdown(
    f'<div class="insight"><b>Najważniejszy sygnał:</b> {executive_insight(data)}</div>',
    unsafe_allow_html=True,
)

# ============================================================
# ZAKŁADKI
# ============================================================
tabs = st.tabs([
    "01 · Podsumowanie",
    "02 · Ranking kandydatów",
    "03 · Profil kandydata",
    "04 · Mapa potencjału",
    "05 · Kompetencje grupy",
    "06 · Odpowiedzi otwarte",
    "07 · Metodologia i jakość danych",
])

# ------------------------------------------------------------
# 01 PODSUMOWANIE
# ------------------------------------------------------------
with tabs[0]:
    st.markdown('<div class="section-title">Jak wygląda pula kandydatów?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Dwa spojrzenia: wynik samego testu oraz ważony indeks dopasowania do profilu Lidera Innowacji AI.</div>',
        unsafe_allow_html=True
    )

    c1, c2 = st.columns([1.05, 1])

    with c1:
        hist = px.histogram(
            data,
            x="Indeks dopasowania",
            nbins=10,
            color_discrete_sequence=["#7C3AED"],
            title="Rozkład Indeksu Dopasowania",
            labels={"Indeks dopasowania": "Indeks dopasowania [%]"},
        )
        hist.add_vline(
            x=avg_fit, line_dash="dash", line_color="#EC4899",
            annotation_text=f"średnia {avg_fit:.0f}%"
        )
        style_figure(hist, 390)
        st.plotly_chart(hist, use_container_width=True)

    with c2:
        status_counts = (
            data["Rekomendacja"]
            .value_counts()
            .reindex(list(STATUS_COLORS.keys()), fill_value=0)
            .rename_axis("Status")
            .reset_index(name="Liczba")
        )
        donut = px.pie(
            status_counts,
            names="Status",
            values="Liczba",
            hole=.66,
            color="Status",
            color_discrete_map=STATUS_COLORS,
            title="Struktura rekomendacji",
        )
        donut.update_traces(textinfo="percent+label", textposition="outside")
        style_figure(donut, 390)
        st.plotly_chart(donut, use_container_width=True)

    st.markdown('<div class="section-title">Profil kompetencyjny całej puli</div>', unsafe_allow_html=True)
    group_profile = pd.DataFrame({
        "Kompetencja": list(WEIGHTS.keys()),
        "Wynik": [data[d].mean() for d in WEIGHTS.keys()],
        "Waga w indeksie": [WEIGHTS[d] * 100 for d in WEIGHTS.keys()],
    })
    group_profile["Kolor"] = group_profile["Kompetencja"].map(DIM_COLORS)

    bar = go.Figure()
    for _, r in group_profile.iterrows():
        bar.add_trace(go.Bar(
            x=[r["Wynik"]],
            y=[r["Kompetencja"]],
            orientation="h",
            name=r["Kompetencja"],
            marker_color=r["Kolor"],
            text=[f"{r['Wynik']:.0f}%"],
            textposition="outside",
            hovertemplate=f"{r['Kompetencja']}: %{{x:.0f}}%<extra></extra>"
        ))
    bar.update_xaxes(range=[0, 105], title="Średni wynik [%]")
    bar.update_layout(showlegend=False, title="Gdzie grupa jest najmocniejsza, a gdzie ma największe luki?")
    style_figure(bar, 390)
    st.plotly_chart(bar, use_container_width=True)

# ------------------------------------------------------------
# 02 RANKING
# ------------------------------------------------------------
with tabs[1]:
    st.markdown('<div class="section-title">Ranking dopasowania do roli</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Ranking jest wskaźnikiem pomocniczym do wyboru osób do dalszej weryfikacji — nie zastępuje rozmowy, case study ani decyzji przełożonego.</div>',
        unsafe_allow_html=True,
    )

    ranking = data[[
        "Miejsce", "Nazwa_clean", "Dział_clean", COL["pct"], "Indeks dopasowania",
        "Biznes i ROI", "AI i analityka", "Automatyzacja i agenci",
        "Prompting", "Bezpieczeństwo i krytyczne myślenie", "Rekomendacja"
    ]].copy()

    ranking.columns = [
        "Miejsce", "Pracownik", "Dział", "Wynik assessmentu", "Indeks dopasowania",
        "Biznes i ROI", "AI i analityka", "Automatyzacja i agenci",
        "Prompting", "Bezpieczeństwo", "Rekomendacja"
    ]

    st.dataframe(
        ranking,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Miejsce": st.column_config.NumberColumn("#", width="small"),
            "Wynik assessmentu": st.column_config.ProgressColumn(
                "Wynik assessmentu", min_value=0, max_value=100, format="%.0f%%"
            ),
            "Indeks dopasowania": st.column_config.ProgressColumn(
                "Indeks dopasowania", min_value=0, max_value=100, format="%.0f%%"
            ),
            "Biznes i ROI": st.column_config.ProgressColumn(
                "Biznes i ROI", min_value=0, max_value=100, format="%.0f%%"
            ),
            "AI i analityka": st.column_config.ProgressColumn(
                "AI i analityka", min_value=0, max_value=100, format="%.0f%%"
            ),
            "Automatyzacja i agenci": st.column_config.ProgressColumn(
                "Automatyzacja i agenci", min_value=0, max_value=100, format="%.0f%%"
            ),
            "Prompting": st.column_config.ProgressColumn(
                "Prompting", min_value=0, max_value=100, format="%.0f%%"
            ),
            "Bezpieczeństwo": st.column_config.ProgressColumn(
                "Bezpieczeństwo", min_value=0, max_value=100, format="%.0f%%"
            ),
        },
    )

    csv = ranking.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ Pobierz ranking CSV",
        data=csv,
        file_name="ranking_liderow_innowacji_ai.csv",
        mime="text/csv",
    )

    st.markdown("#### Jak czytać ranking?")
    st.markdown(
        """
        <span class="legend-chip">🟢 ≥ 75% + warunki brzegowe: bardzo wysokie dopasowanie</span>
        <span class="legend-chip">🔵 ≥ 60% + warunki brzegowe: wysokie dopasowanie</span>
        <span class="legend-chip">🟠 ≥ 45%: potencjał do dalszej weryfikacji</span>
        <span class="legend-chip">⚪ < 45%: rozwój przed kolejnym etapem</span>
        """,
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------
# 03 PROFIL KANDYDATA
# ------------------------------------------------------------
with tabs[2]:
    st.markdown('<div class="section-title">Indywidualna karta kandydata</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Wybierz osobę, aby zobaczyć nie tylko wynik, ale też profil kompetencji, obszary do sprawdzenia i odpowiedzi otwarte.</div>',
        unsafe_allow_html=True,
    )

    candidate_labels = [
        f"{r['Miejsce']}. {r['Nazwa_clean']} · {r['Dział_clean']} · {r['Indeks dopasowania']:.0f}%"
        for _, r in data.iterrows()
    ]
    selected_label = st.selectbox("Kandydat", candidate_labels)
    selected_idx = candidate_labels.index(selected_label)
    person = data.iloc[selected_idx]

    status_color = STATUS_COLORS[person["Rekomendacja"]]
    st.markdown(
        f"""
        <div class="profile-card">
          <span class="status" style="background:{status_color};">{safe(person["Rekomendacja"])}</span>
          <div style="font-size:1.8rem;font-weight:850;letter-spacing:-.035em;color:#111827;">
            {safe(person["Nazwa_clean"])}
          </div>
          <div style="color:#667085;margin-top:.15rem;">
            {safe(person["Dział_clean"])} · wynik assessmentu {person[COL["pct"]]:.0f}% · indeks dopasowania {person["Indeks dopasowania"]:.0f}%
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    p1, p2, p3 = st.columns([1.0, 1.15, 1.15])

    with p1:
        st.metric("Wynik assessmentu", f"{person[COL['pct']]:.0f}%")
        st.metric("Indeks dopasowania", f"{person['Indeks dopasowania']:.0f}%")
        st.metric("Punkty", f"{person[COL['total']]:.0f} / {TOTAL_MAX}")

    with p2:
        dims = list(WEIGHTS.keys())
        values = [person[d] for d in dims]
        avg_values = [data[d].mean() for d in dims]

        radar = go.Figure()
        radar.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=dims + [dims[0]],
            fill="toself",
            name="Kandydat",
            line=dict(color="#7C3AED", width=3),
            fillcolor="rgba(124,58,237,.18)",
        ))
        radar.add_trace(go.Scatterpolar(
            r=avg_values + [avg_values[0]],
            theta=dims + [dims[0]],
            name="Średnia grupy",
            line=dict(color="#94A3B8", width=2, dash="dot"),
        ))
        radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            title="Profil kompetencyjny",
            showlegend=True,
        )
        style_figure(radar, 390)
        st.plotly_chart(radar, use_container_width=True)

    with p3:
        strengths, gaps = strengths_and_gaps(person)
        st.markdown("#### Ocena managerska")
        st.markdown(
            f'<div class="callout">{safe(candidate_text(person))}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("**Mocne strony**")
        for x in strengths:
            st.markdown(f"- **{x}** — {person[x]:.0f}%")

        st.markdown("**Obszary do weryfikacji**")
        for x in gaps:
            st.markdown(f"- **{x}** — {person[x]:.0f}%")

    st.markdown("#### Pytania na kolejny etap")
    for point in verification_points(person):
        st.markdown(f"- {point}")

    st.markdown("---")
    st.markdown("#### Odpowiedzi otwarte kandydata")
    for i, q in OPEN_QUESTIONS.items():
        score = person[q["score"]]
        with st.expander(
            f"{i}. {q['short']} — {score:.0f}/{OPEN_MAX_PER_QUESTION} pkt"
            if pd.notna(score) else f"{i}. {q['short']} — brak punktacji"
        ):
            st.markdown("**Odpowiedź respondenta**")
            st.write(person[q["answer"]] if pd.notna(person[q["answer"]]) else "Brak odpowiedzi")
            st.markdown("**Feedback z assessmentu**")
            st.write(person[q["feedback"]] if pd.notna(person[q["feedback"]]) else "Brak feedbacku")

    detailed_cols = [f"P{i}. Punkty" for i in range(1, 16)]
    available_detail = [c for c in detailed_cols if c in data.columns and pd.notna(person[c])]

    if available_detail:
        st.markdown("#### Szczegółowe pytania zamknięte")
        detail_df = pd.DataFrame({
            "Temat": [CLOSED_SHORT[int(c.split(".")[0][1:])] for c in available_detail],
            "Punkty": [person[c] for c in available_detail],
        })
        detail_df["Wynik"] = detail_df["Punkty"] * 100

        closed_fig = px.bar(
            detail_df,
            x="Wynik",
            y="Temat",
            orientation="h",
            range_x=[0, 100],
            color="Wynik",
            color_continuous_scale=["#F1F5F9", "#2563EB"],
            title="Sygnały ze szczegółowych pytań zamkniętych",
            text="Punkty",
        )
        style_figure(closed_fig, max(360, 34 * len(detail_df)))
        st.plotly_chart(closed_fig, use_container_width=True)
    else:
        st.info(
            "Dla tego wpisu eksport zawiera sumę punktów zamkniętych, ale nie zawiera punktacji P1–P15 osobno. "
            "Profil główny nadal można policzyć, ale szczegółowa diagnoza techniczna jest ograniczona."
        )

# ------------------------------------------------------------
# 04 MAPA POTENCJAŁU
# ------------------------------------------------------------
with tabs[3]:
    st.markdown('<div class="section-title">Mapa potencjału: biznes × AI/analityka</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Najbardziej interesujący profil znajduje się w prawym górnym obszarze: mocne myślenie biznesowe i jednocześnie mocny fundament AI/analityczny.</div>',
        unsafe_allow_html=True,
    )

    scatter = px.scatter(
        data,
        x="AI i analityka",
        y="Biznes i ROI",
        size="Indeks dopasowania",
        color="Rekomendacja",
        color_discrete_map=STATUS_COLORS,
        hover_name="Nazwa_clean",
        hover_data={
            "Dział_clean": True,
            COL["pct"]: ":.0f",
            "Indeks dopasowania": ":.0f",
            "Automatyzacja i agenci": ":.0f",
            "Prompting": ":.0f",
            "Bezpieczeństwo i krytyczne myślenie": ":.0f",
        },
        labels={
            "AI i analityka": "AI i fundament analityczny [%]",
            "Biznes i ROI": "Myślenie biznesowe i ROI [%]",
            "Dział_clean": "Dział",
            COL["pct"]: "Wynik assessmentu",
        },
        title="Kto łączy kompetencje biznesowe z techniczno-analitycznymi?",
        size_max=38,
    )
    scatter.add_vline(x=50, line_dash="dot", line_color="#94A3B8")
    scatter.add_hline(y=50, line_dash="dot", line_color="#94A3B8")
    scatter.add_annotation(x=76, y=94, text="Najmocniejszy profil<br>do dalszej weryfikacji", showarrow=False, font=dict(color="#16A34A"))
    scatter.update_xaxes(range=[-4, 104])
    scatter.update_yaxes(range=[-4, 104])
    style_figure(scatter, 560)
    st.plotly_chart(scatter, use_container_width=True)

    st.caption(
        "Uwaga: wymiar „AI i analityka” jest obecnie oparty na sumie 15 pytań zamkniętych. "
        "Dla jeszcze lepszej oceny backgroundu analitycznego warto w przyszłości dodać osobne pytanie profilujące praktykę z Pythonem/SQL/BI."
    )

# ------------------------------------------------------------
# 05 KOMPETENCJE GRUPY
# ------------------------------------------------------------
with tabs[4]:
    st.markdown('<div class="section-title">Mapa kompetencji całej grupy</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Pokazuje, czy problemem jest ogólny brak wiedzy, czy konkretna luka — np. ROI, agenci, prompting albo kontrola ryzyka.</div>',
        unsafe_allow_html=True,
    )

    heat = data[["Nazwa_clean"] + list(WEIGHTS.keys())].copy()
    heat = heat.set_index("Nazwa_clean")

    heatmap = go.Figure(data=go.Heatmap(
        z=heat.values,
        x=heat.columns,
        y=heat.index,
        zmin=0,
        zmax=100,
        colorscale=[
            [0.00, "#F8FAFC"],
            [0.25, "#FDE68A"],
            [0.50, "#FDBA74"],
            [0.70, "#93C5FD"],
            [1.00, "#6D28D9"],
        ],
        text=np.round(heat.values).astype(int),
        texttemplate="%{text}%",
        hovertemplate="Osoba: %{y}<br>Kompetencja: %{x}<br>Wynik: %{z:.0f}%<extra></extra>",
        colorbar=dict(title="Wynik"),
    ))
    heatmap.update_layout(title="Heatmapa profilu kandydatów")
    style_figure(heatmap, max(430, 42 * len(heat)))
    st.plotly_chart(heatmap, use_container_width=True)

    # Działy — tylko gdy mają sensowne N.
    dep_counts = data["Dział_clean"].value_counts()
    valid_deps = dep_counts[dep_counts >= 2].index.tolist()
    if valid_deps:
        dep = (
            data[data["Dział_clean"].isin(valid_deps)]
            .groupby("Dział_clean")[list(WEIGHTS.keys()) + ["Indeks dopasowania"]]
            .mean()
            .round(1)
            .reset_index()
        )
        st.markdown("#### Porównanie działów (minimum 2 osoby)")
        st.dataframe(dep, use_container_width=True, hide_index=True)
    else:
        st.info("W aktualnym zbiorze żaden dział nie ma co najmniej 2 osób po deduplikacji, więc porównanie działów byłoby niemiarodajne.")

# ------------------------------------------------------------
# 06 ODPOWIEDZI OTWARTE
# ------------------------------------------------------------
with tabs[5]:
    st.markdown('<div class="section-title">Co mówią pytania otwarte?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">To tutaj widać praktyczne myślenie: use case, ROI, jakość promptu, świadomość ryzyka i realne doświadczenie z agentami.</div>',
        unsafe_allow_html=True,
    )

    open_avg = []
    for i, q in OPEN_QUESTIONS.items():
        avg = data[q["score"]].mean() / OPEN_MAX_PER_QUESTION * 100
        open_avg.append({
            "Pytanie": f"P{i}. {q['short']}",
            "Wynik": avg,
            "Kolor": DIM_COLORS[q["dimension"]],
        })

    oq = pd.DataFrame(open_avg)
    oq_fig = go.Figure()
    for _, r in oq.iterrows():
        oq_fig.add_trace(go.Bar(
            x=[r["Wynik"]],
            y=[r["Pytanie"]],
            orientation="h",
            marker_color=r["Kolor"],
            text=[f"{r['Wynik']:.0f}%"],
            textposition="outside",
            showlegend=False,
        ))
    oq_fig.update_xaxes(range=[0, 105], title="Średni wynik [%]")
    oq_fig.update_layout(title="Które pytania praktyczne sprawiają najwięcej trudności?")
    style_figure(oq_fig, 420)
    st.plotly_chart(oq_fig, use_container_width=True)

    gaps = feedback_gap_summary(data)
    if gaps["Sygnały w feedbacku"].sum() > 0:
        gap_fig = px.bar(
            gaps,
            x="Sygnały w feedbacku",
            y="Obszar",
            orientation="h",
            text_auto=True,
            color="Sygnały w feedbacku",
            color_continuous_scale=["#FDE68A", "#EC4899", "#7C3AED"],
            title="Najczęściej pojawiające się sygnały rozwojowe w feedbacku",
        )
        style_figure(gap_fig, 400)
        st.plotly_chart(gap_fig, use_container_width=True)
        st.caption(
            "To pomocnicza analiza słów i zwrotów występujących w feedbacku z assessmentu, a nie model NLP. "
            "Jej rolą jest szybkie pokazanie powtarzających się tematów."
        )

# ------------------------------------------------------------
# 07 METODOLOGIA I JAKOŚĆ
# ------------------------------------------------------------
with tabs[6]:
    st.markdown('<div class="section-title">Metodologia Indeksu Dopasowania</div>', unsafe_allow_html=True)
    st.markdown(
        """
        Indeks nie zastępuje wyniku assessmentu. Jest **drugą warstwą interpretacji**, która nadaje większą wagę
        tym kompetencjom, które są szczególnie ważne w roli Lidera Innowacji AI: identyfikowaniu wartości biznesowej,
        łączeniu AI z procesami oraz praktycznemu wykorzystaniu automatyzacji.
        """
    )

    methodology = pd.DataFrame({
        "Wymiar": list(WEIGHTS.keys()),
        "Waga": [f"{WEIGHTS[d]*100:.0f}%" for d in WEIGHTS.keys()],
        "Źródło w obecnym assessmentcie": [
            "Pytania otwarte 1 i 3",
            "Suma 15 pytań zamkniętych",
            "Pytanie otwarte 5",
            "Pytanie otwarte 2",
            "Pytanie otwarte 4",
        ],
    })
    st.dataframe(methodology, use_container_width=True, hide_index=True)

    st.markdown("#### Proponowane progi")
    threshold_df = pd.DataFrame([
        ["Bardzo wysokie dopasowanie", "≥ 75%", "Biznes i ROI ≥ 60% oraz AI i analityka ≥ 60%", "Silny kandydat do kolejnego etapu"],
        ["Wysokie dopasowanie", "≥ 60%", "Biznes i ROI ≥ 50% oraz AI i analityka ≥ 50%", "Rekomendacja do kolejnego etapu"],
        ["Potencjał – do weryfikacji", "≥ 45%", "—", "Warto pogłębić profil w rozmowie / case study"],
        ["Rozwój przed kolejnym etapem", "< 45%", "—", "Na ten moment brakuje kilku kluczowych elementów profilu"],
    ], columns=["Status", "Indeks", "Warunek", "Interpretacja"])
    st.dataframe(threshold_df, use_container_width=True, hide_index=True)

    st.markdown("#### Jakość aktualnego pliku")
    missing_email = int(prepared["Email_clean"].eq("").sum())
    detailed_rows = int((prepared["Pokrycie P1-P15"] >= 99).sum())

    q1, q2, q3 = st.columns(3)
    with q1:
        st.metric("Rekordy źródłowe", len(raw))
    with q2:
        st.metric("Dokładne duplikaty usunięte", exact_removed)
    with q3:
        st.metric("Rekordy bez e-maila", missing_email)

    st.write(
        f"Pełną punktację P1–P15 zawiera **{detailed_rows} z {len(prepared)}** unikalnych rekordów po usunięciu dokładnych duplikatów."
    )

    if detailed_rows < len(prepared):
        st.warning(
            "Część starszych/testowych wpisów zawiera tylko sumę pytań zamkniętych, bez punktacji P1–P15. "
            "Nie blokuje to rankingu ani pięciu głównych wymiarów, ale ogranicza szczegółową diagnozę wiedzy technicznej."
        )

    st.markdown("#### Co warto dodać w kolejnej wersji assessmentu")
    st.markdown(
        """
        - **Jedno pytanie profilujące background analityczny**: Python / SQL / BI / no-code / brak doświadczenia.
        - Opcjonalnie **poziom praktyki z danymi**: używam sporadycznie / regularnie / buduję rozwiązania.
        - Zachować pełne P1–P15 dla każdego rekordu — nie tylko sumę.
        - E-mail jako obowiązkowy, unikalny identyfikator osoby.
        - Przy realnym wdrożeniu skalibrować wagi i progi na podstawie wyników kolejnego etapu programu.
        """
    )

st.markdown("---")
st.caption(
    "Raport wspiera ocenę kandydatów do kolejnego etapu programu Liderów Innowacji AI. "
    "Indeks dopasowania i progi są propozycją POC; decyzja powinna uwzględniać dodatkową ocenę człowieka, "
    "np. rozmowę, case study lub warsztat grupowy."
)
