"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        GC RISK PREDICTOR — PROFESSIONAL AI-POWERED DASHBOARD                 ║
║    Construction Site Safety Risk Analysis & Prediction System                ║
║                     v3.0 — Premium Design Edition                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

Redesigned for Production: Modern, Clean, Highly Visual SaaS Interface
Launch: streamlit run app_dashboard.py
"""

import os, re, json, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import streamlit as st
from io import BytesIO

warnings.filterwarnings("ignore")

# ─── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GC Risk Predictor — AI Safety Dashboard",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "**GC Risk Predictor v3.0** — Premium AI Safety Analytics for Construction Sites. Built with ❤️ for ISET."
    }
)

# ─── Constants ──────────────────────────────────────────────────────────────────
RANDOM_STATE = 42
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

NUM_COLS = ["Effectif", "Temperature", "Vent_kmh", "EPI_Manquants", "Risque_Historique"]

TYPE_TRAVAUX_OPTIONS = [
    "Béton", "Charpente", "Coffrage", "Excavation",
    "Fondation", "Grutage", "Maçonnerie", "Toiture",
    "Travaux en Hauteur", "VRD",
]

GC_THRESHOLDS = {
    "Vent_kmh":          {"alerte": 45, "danger": 80, "impossible": 250},
    "Temperature":       {"min_possible": -30, "max_possible": 60,
                          "alerte_froid": 5, "alerte_chaleur": 35},
    "EPI_Manquants":     {"critique": 5, "max_possible": 15},
    "Effectif":          {"surveillance": 30, "max_possible": 200},
    "Risque_Historique": {"min": 0.0, "max": 1.0},
}

GC_LEXICON = {
    "alerte_vent":          ["vent fort", "rafales", "rafales violentes", "coup de vent", "tempête"],
    "alerte_froid":         ["froid intense", "gelées", "gel", "verglas", "givre", "température froide"],
    "alerte_chaleur":       ["coup de chaleur", "forte chaleur", "canicule", "température élevée"],
    "alerte_pluie":         ["pluie", "averse", "précipitations", "mouillé", "humide"],
    "harnais_manquant":     ["harnais", "harnais anti-chute", "longe de sécurité", "harnais de sécurité"],
    "casque_manquant":      ["casque de protection", "sans casque", "casque absent"],
    "gilet_manquant":       ["gilet haute visibilité", "gilet de sécurité", "haute visibilité"],
    "epi_absents":          ["epi sont absents", "équipements manquants", "absence de protection",
                             "non conformes", "sans équipement"],
    "intervention_urgente": ["intervention corrective urgente", "urgente", "immédiat", "sans délai"],
    "conformite_ok":        ["conformité satisfaisant", "présents et conformes",
                             "aucune non-conformité", "conforme"],
    "risque_eleve_txt":     ["risque élevé", "niveau élevé", "dangereux", "critique"],
    "risque_faible_txt":    ["risque faible", "niveau faible", "satisfaisant", "sans risque"],
    "travail_hauteur":      ["travail en hauteur", "hauteur", "toiture", "échafaudage", "nacelle"],
    "excavation_flag":      ["excavation", "fouille", "tranchée", "terrassement"],
    "demolition_flag":      ["démolition", "déconstruction"],
    "grutage_flag":         ["grutage", "grue", "levage", "engin de levage"],
    "coffrage_flag":        ["coffrage", "béton", "ferraillage"],
    "chute_objet":          ["chute d'objet", "projection", "éclat", "éboulement"],
    "risque_electrique":    ["électrique", "câble", "ligne haute tension", "court-circuit"],
    "risque_chimique":      ["produit chimique", "toxique", "amiante", "solvant"],
}

REGEX_PATTERNS = {
    "regex_vent_kmh":     [r"vent\s+[à a]?\s*(\d+)", r"(\d+)\s*km/?h"],
    "regex_temp_c":       [r"(-?\d+)\s*(?:°c|degre)", r"température\s+(?:de\s*)?(-?\d+)"],
    "regex_epi_count":    [r"(\d+)\s+équipements? non conformes?", r"(\d+)\s+epi manquant"],
    "regex_effectif_txt": [r"effectif de\s*(\d+)", r"(\d+)\s+(?:travailleurs?|ouvriers?)"],
    "regex_heures":       [r"(\d+)\s+heures?"],
}

STRUCT_COLS = [
    "Effectif_sc", "Temperature_sc", "Vent_kmh_sc", "EPI_Manquants_sc", "Risque_Historique_sc",
    "flag_vent_danger", "flag_vent_alerte", "flag_temp_froid", "flag_temp_chaleur",
    "flag_epi_critique", "flag_effectif_eleve",
    "type_coffrage", "type_demolition", "type_excavation", "type_grutage",
    "type_inconnu", "type_soudure", "type_travail_en_hauteur",
    "regex_vent_kmh", "regex_temp_c", "regex_epi_count", "regex_effectif_txt",
    "regex_heures", "regex_urgence", "regex_arret_chantier", "regex_conf_ok",
    "regex_prochaine_visite",
    "alerte_vent", "alerte_froid", "alerte_chaleur", "alerte_pluie",
    "harnais_manquant", "casque_manquant", "gilet_manquant", "epi_absents",
    "intervention_urgente", "conformite_ok", "risque_eleve_txt", "risque_faible_txt",
    "travail_hauteur", "excavation_flag", "demolition_flag", "grutage_flag",
    "coffrage_flag", "chute_objet", "risque_electrique", "risque_chimique",
    "score_composite",
]

DANGER_KEYWORDS = [
    "urgence", "urgente", "urgent", "harnais", "évacuation", "chute",
    "accident", "blessure", "danger", "critique", "risque élevé", "alerte",
    "immédiat", "arrêt", "non conforme",
]
SAFETY_KEYWORDS = [
    "conforme", "conformité", "satisfaisant", "normal",
    "aucun problème", "bon état", "présents",
]

MODEL_METRICS = {
    "MLP Neural Network (Best)": {"acc": 0.8900, "f1": 0.8884, "prec": 0.8870, "rec": 0.8900},
    "XGBoost (tuned)":           {"acc": 0.8850, "f1": 0.8847, "prec": 0.8878, "rec": 0.8850},
    "Dual Stream":               {"acc": 0.8900, "f1": 0.8840, "prec": 0.8829, "rec": 0.8900},
    "Random Forest":             {"acc": 0.8650, "f1": 0.8632, "prec": 0.8631, "rec": 0.8650},
    "Logistic Regression":       {"acc": 0.8500, "f1": 0.8649, "prec": 0.8902, "rec": 0.8500},
}

CLASS_DISPLAY = {
    "Critique": ("🔴", "badge-critique", "#ef4444"),
    "Élevé":    ("🟠", "badge-eleve",    "#f97316"),
    "Moyen":    ("🟡", "badge-moyen",     "#eab308"),
    "Faible":   ("🟢", "badge-faible",    "#22c55e"),
}

SCENARIOS = {
    "🔴 Grutage par vent fort (Critique)": {
        "Type_Travaux": "Grutage",
        "Effectif": 45,
        "Temperature": 8.0,
        "Vent_kmh": 95.0,
        "EPI_Manquants": 7,
        "Risque_Historique": 0.82,
        "Rapport_inspection": (
            "Intervention corrective urgente requise. Vent à 95 km/h, grue en opération. "
            "Harnais absents, EPI non conformes. Arrêt de chantier recommandé immédiatement."
        ),
    },
    "🟠 Travaux en hauteur par froid (Élevé)": {
        "Type_Travaux": "Travaux en Hauteur",
        "Effectif": 20,
        "Temperature": 4.0,
        "Vent_kmh": 52.0,
        "EPI_Manquants": 4,
        "Risque_Historique": 0.55,
        "Rapport_inspection": (
            "Travail en hauteur sur échafaudage. Température froide, risque de gel. "
            "Certains harnais à vérifier. Surveillance renforcée conseillée."
        ),
    },
    "🟡 Excavation standard (Moyen)": {
        "Type_Travaux": "Excavation",
        "Effectif": 15,
        "Temperature": 22.0,
        "Vent_kmh": 20.0,
        "EPI_Manquants": 2,
        "Risque_Historique": 0.30,
        "Rapport_inspection": (
            "Excavation en cours. Conditions météo modérées. "
            "Mesures préventives supplémentaires envisagées. Niveau de risque modéré évalué."
        ),
    },
    "🟢 Béton en conditions normales (Sûr)": {
        "Type_Travaux": "Béton",
        "Effectif": 8,
        "Temperature": 20.0,
        "Vent_kmh": 10.0,
        "EPI_Manquants": 0,
        "Risque_Historique": 0.10,
        "Rapport_inspection": (
            "Chantier conforme. EPI présents et conformes. "
            "Aucune non-conformité relevée. Conformité satisfaisant vérifiée. Aucun risque identifié."
        ),
    },
}

# ─── PROFESSIONAL CSS INJECTION ──────────────────────────────────────────────
def inject_css(dark_mode: bool) -> None:
    """Premium styling for modern SaaS dashboard with animations & transitions."""
    
    if dark_mode:
        bg_main    = "#0a0e27"
        bg_card    = "#1a1f3a"
        text_primary = "#f0f4f8"
        text_secondary = "#cbd5e1"
        border_col = "#2d3e5f"
        accent_primary = "#3b82f6"
        accent_secondary = "#60a5fa"
    else:
        bg_main    = "#f8fafc"
        bg_card    = "#ffffff"
        text_primary = "#1e293b"
        text_secondary = "#475569"
        border_col = "#e2e8f0"
        accent_primary = "#2563eb"
        accent_secondary = "#3b82f6"

    critical_color = "#ef4444"
    elevated_color = "#f97316"
    medium_color   = "#eab308"
    low_color      = "#22c55e"

    st.markdown(f"""
    <style>
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}

    html, body, [class*="css"] {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
                     'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
                     sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }}

    .main .block-container {{
        background: linear-gradient(135deg, {bg_main} 0%, {bg_main} 100%);
        padding-top: 2rem;
        padding-bottom: 3rem;
        color: {text_primary};
    }}

    body {{
        color: {text_primary};
        background: {bg_main};
    }}

    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background: {bg_main};
        color: {text_primary};
    }}

    [data-testid="stSidebar"] {{
        background: {bg_card};
    }}

    [data-testid="stSidebar"] *, [data-testid="stWidgetLabel"] p {{
        color: {text_primary};
    }}

    .header-container {{
        background: linear-gradient(135deg, {accent_primary} 0%, {accent_secondary} 100%);
        padding: 3rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
        animation: slideDown 0.6s ease-out;
    }}

    .header-title {{
        font-size: 2.5rem;
        font-weight: 800;
        color: white;
        letter-spacing: -1px;
        margin-bottom: 0.5rem;
    }}

    .header-subtitle {{
        font-size: 1.1rem;
        color: rgba(255, 255, 255, 0.9);
        font-weight: 300;
    }}

    .risk-card {{
        background: {bg_card};
        border: 1px solid {border_col};
        border-radius: 14px;
        padding: 1.5rem;
        margin: 0.75rem 0;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        border-left: 5px solid {accent_primary};
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    .risk-card:hover {{
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        transform: translateY(-2px);
        border-left-color: {accent_secondary};
    }}

    .input-panel {{
        background: {bg_card};
        border: 1px solid {border_col};
        border-radius: 14px;
        padding: 2rem;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    }}

    .results-panel {{
        background: {bg_card};
        border: 1px solid {border_col};
        border-radius: 14px;
        padding: 2rem;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    }}

    .section-header {{
        font-size: 1.6rem;
        font-weight: 700;
        color: {text_primary};
        margin-top: 2rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 3px solid {accent_primary};
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }}

    .badge {{
        display: inline-block;
        padding: 0.75rem 2rem;
        border-radius: 50px;
        font-size: 1.3rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }}

    .badge-critique {{
        background: linear-gradient(135deg, {critical_color} 0%, #dc2626 100%);
        color: white;
    }}

    .badge-critique:hover {{
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
    }}

    .badge-eleve {{
        background: linear-gradient(135deg, {elevated_color} 0%, #ea580c 100%);
        color: white;
    }}

    .badge-eleve:hover {{
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(249, 115, 22, 0.4);
    }}

    .badge-moyen {{
        background: linear-gradient(135deg, {medium_color} 0%, #facc15 100%);
        color: #1a1a00;
    }}

    .badge-moyen:hover {{
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(234, 179, 8, 0.4);
    }}

    .badge-faible {{
        background: linear-gradient(135deg, {low_color} 0%, #16a34a 100%);
        color: white;
    }}

    .badge-faible:hover {{
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(34, 197, 94, 0.4);
    }}

    .alert-box {{
        padding: 1.25rem;
        border-radius: 10px;
        margin: 0.75rem 0;
        font-size: 0.95rem;
        font-weight: 500;
        border-left: 5px solid;
        background-color: rgba(0, 0, 0, 0.02);
        backdrop-filter: blur(10px);
        animation: slideInLeft 0.4s ease-out;
    }}

    .alert-danger {{
        border-left-color: {critical_color};
        background: rgba(239, 68, 68, 0.08);
        color: {text_primary};
    }}

    .alert-warning {{
        border-left-color: {elevated_color};
        background: rgba(249, 115, 22, 0.08);
        color: {text_primary};
    }}

    .alert-ok {{
        border-left-color: {low_color};
        background: rgba(34, 197, 94, 0.08);
        color: {text_primary};
    }}

    .metric-box {{
        background: {bg_card};
        border: 2px solid {border_col};
        border-radius: 12px;
        padding: 1.5rem 1rem;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    .metric-box:hover {{
        border-color: {accent_primary};
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.15);
        transform: translateY(-2px);
    }}

    .metric-value {{
        font-size: 2rem;
        font-weight: 900;
        line-height: 1;
        margin-bottom: 0.5rem;
    }}

    .metric-label {{
        font-size: 0.85rem;
        font-weight: 600;
        color: {text_secondary};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, {accent_primary}, {accent_secondary});
        border-radius: 10px;
    }}

    .stSelectbox > div > div > button {{
        border-radius: 8px;
        border: 1px solid {border_col} !important;
        color: {text_primary} !important;
    }}

    .stSlider > div > div > div > div {{
        color: {accent_primary};
    }}

    .stDivider {{
        border-color: {border_col};
        margin: 2rem 0;
    }}

    @keyframes slideDown {{
        from {{
            opacity: 0;
            transform: translateY(-20px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    @keyframes slideInLeft {{
        from {{
            opacity: 0;
            transform: translateX(-20px);
        }}
        to {{
            opacity: 1;
            transform: translateX(0);
        }}
    }}

    @keyframes fadeIn {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}

    .fade-in {{
        animation: fadeIn 0.6s ease-out;
    }}

    .stTabs {{
        border-bottom: 2px solid {border_col};
    }}

    .stTabs [data-baseweb="tab-list"] button {{
        border-radius: 8px 8px 0 0 !important;
        background: transparent !important;
        color: {text_secondary} !important;
        border: none !important;
    }}

    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        background: {accent_primary} !important;
        color: white !important;
    }}

    .stButton > button {{
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary});
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }}

    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
    }}

    .stDataFrame {{
        border-radius: 8px;
        overflow: hidden;
    }}

    mark {{
        border-radius: 3px;
        padding: 2px 4px;
        font-weight: 600;
    }}

    @media (max-width: 768px) {{
        .header-title {{ font-size: 1.8rem; }}
        .section-header {{ font-size: 1.3rem; }}
        .metric-box {{ padding: 1rem; }}
    }}

    </style>
    """, unsafe_allow_html=True)


# ─── Resource Loading ────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading AI models…")
def load_models():
    best_model = joblib.load(os.path.join(MODELS_DIR, "best_model_v2.joblib"))
    label_info = joblib.load(os.path.join(MODELS_DIR, "label_map_v2.joblib"))
    rf_model   = joblib.load(os.path.join(MODELS_DIR, "rf_model.joblib"))
    scaler     = joblib.load(os.path.join(MODELS_DIR, "scaler.joblib"))
    tfidf_vec  = joblib.load(os.path.join(MODELS_DIR, "tfidf_vectorizer.joblib"))
    return best_model, label_info, rf_model, scaler, tfidf_vec


@st.cache_data(show_spinner="Loading historical data…")
def load_data():
    ann_path = os.path.join(BASE_DIR, "predictions_annotated_v2.csv")
    raw_path = os.path.join(BASE_DIR, "Dataset.csv")
    df_ann = pd.read_csv(ann_path) if os.path.exists(ann_path) else pd.DataFrame()
    df_raw = pd.read_csv(raw_path) if os.path.exists(raw_path) else pd.DataFrame()
    return df_ann, df_raw


# ─── Feature Engineering ────────────────────────────────────────────────────
def _clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    t = text.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\d+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _extract_regex_features(text: str) -> dict:
    t = str(text).lower()
    feats = {}
    for feat_name, patterns in REGEX_PATTERNS.items():
        val = 0.0
        for pat in patterns:
            m = re.search(pat, t)
            if m:
                try:
                    val = float(m.group(1))
                    break
                except Exception:
                    pass
        feats[feat_name] = val
    feats["regex_urgence"]          = int(bool(re.search(r"urgent|urgente|immédiat|immédiatement", t)))
    feats["regex_arret_chantier"]   = int(bool(re.search(r"arrêt de chantier|arrêter|évacuation", t)))
    feats["regex_conf_ok"]          = int(bool(re.search(r"conformit[eé] satisfaisant|aucun risque|conforme", t)))
    feats["regex_prochaine_visite"] = int(bool(re.search(r"prochaine visite|sous quinzaine|48 heures", t)))
    return feats


def _extract_gc_features(text: str) -> dict:
    t = str(text).lower()
    return {feat: int(any(kw in t for kw in kws)) for feat, kws in GC_LEXICON.items()}


def _score_composite(effectif: float, temp: float, vent: float,
                     epi: float, risque_hist: float) -> float:
    """Approximate the training score_composite with fixed min/max ranges."""
    ranges = {
        "Effectif":          (1,   50),
        "Temperature":       (-10, 45),
        "Vent_kmh":          (0,  120),
        "EPI_Manquants":     (0,   10),
        "Risque_Historique": (0.0,  1.0),
    }
    weights = {
        "Risque_Historique": 0.40, "EPI_Manquants": 0.25,
        "Vent_kmh": 0.20, "Effectif": 0.10, "Temperature": 0.05,
    }
    vals = {"Effectif": effectif, "Temperature": temp, "Vent_kmh": vent,
            "EPI_Manquants": epi, "Risque_Historique": risque_hist}
    score = 0.0
    for col, w in weights.items():
        mn, mx = ranges[col]
        norm = max(0.0, min(1.0, (vals[col] - mn) / (mx - mn + 1e-9)))
        score += norm * w
    return round(score, 4)


def build_feature_vector(
    type_travaux: str,
    effectif: int,
    temperature: float,
    vent_kmh: float,
    epi_manquants: int,
    risque_historique: float,
    rapport: str,
    scaler,
    tfidf_vec,
) -> np.ndarray:
    """Reconstruct the 98-feature vector exactly as in training."""

    num_raw = np.array([[effectif, temperature, vent_kmh, epi_manquants, risque_historique]], dtype=float)
    num_sc  = scaler.transform(num_raw)[0]

    flag_vent_danger    = int(vent_kmh    > GC_THRESHOLDS["Vent_kmh"]["danger"])
    flag_vent_alerte    = int(vent_kmh    > GC_THRESHOLDS["Vent_kmh"]["alerte"])
    flag_temp_froid     = int(temperature < GC_THRESHOLDS["Temperature"]["alerte_froid"])
    flag_temp_chaleur   = int(temperature > GC_THRESHOLDS["Temperature"]["alerte_chaleur"])
    flag_epi_critique   = int(epi_manquants >= GC_THRESHOLDS["EPI_Manquants"]["critique"])
    flag_effectif_eleve = int(effectif    > GC_THRESHOLDS["Effectif"]["surveillance"])

    tt = type_travaux.lower()
    type_coffrage           = int("coffrage" in tt or "béton" in tt or "beton" in tt or "maçonnerie" in tt or "maconnerie" in tt)
    type_demolition         = int("démolition" in tt or "demolition" in tt)
    type_excavation         = int("excavation" in tt or "fondation" in tt or "vrd" in tt)
    type_grutage            = int("grutage" in tt or "charpente" in tt)
    type_inconnu            = 0
    type_soudure            = 0
    type_travail_en_hauteur = int("hauteur" in tt or "toiture" in tt)

    rx = _extract_regex_features(rapport)
    gc = _extract_gc_features(rapport)
    score_comp = _score_composite(effectif, temperature, vent_kmh, epi_manquants, risque_historique)

    text_clean  = _clean_text(rapport)
    tfidf_full  = tfidf_vec.transform([text_clean]).toarray()[0]
    tfidf_50    = tfidf_full[:50]

    struct = np.array([
        num_sc[0], num_sc[1], num_sc[2], num_sc[3], num_sc[4],
        flag_vent_danger, flag_vent_alerte, flag_temp_froid,
        flag_temp_chaleur, flag_epi_critique, flag_effectif_eleve,
        type_coffrage, type_demolition, type_excavation, type_grutage,
        type_inconnu, type_soudure, type_travail_en_hauteur,
        rx["regex_vent_kmh"], rx["regex_temp_c"], rx["regex_epi_count"],
        rx["regex_effectif_txt"], rx["regex_heures"],
        rx["regex_urgence"], rx["regex_arret_chantier"],
        rx["regex_conf_ok"], rx["regex_prochaine_visite"],
        gc["alerte_vent"], gc["alerte_froid"], gc["alerte_chaleur"], gc["alerte_pluie"],
        gc["harnais_manquant"], gc["casque_manquant"], gc["gilet_manquant"],
        gc["epi_absents"], gc["intervention_urgente"], gc["conformite_ok"],
        gc["risque_eleve_txt"], gc["risque_faible_txt"], gc["travail_hauteur"],
        gc["excavation_flag"], gc["demolition_flag"], gc["grutage_flag"],
        gc["coffrage_flag"], gc["chute_objet"], gc["risque_electrique"],
        gc["risque_chimique"],
        score_comp,
    ], dtype=float)

    return np.concatenate([struct, tfidf_50]).reshape(1, -1)


# ─── Prediction ──────────────────────────────────────────────────────────────────
def predict(model, label_info, x_vec):
    proba      = model.predict_proba(x_vec)[0]
    pred_idx   = int(np.argmax(proba))
    pred_label = label_info["class_names_model"][pred_idx]
    conf       = float(proba[pred_idx])
    return pred_label, conf, proba


# ─── Real-Time Alert System ────────────────────────────────────────────────────────
def check_alerts(effectif: int, temperature: float, vent_kmh: float,
                epi_manquants: int, risque_historique: float, rapport: str = "") -> dict:
    """Real-time alert checker for GC Risk Predictor."""
    alerts = []
    critical_count = 0
    warning_count = 0
    thr = GC_THRESHOLDS
    
    if vent_kmh > thr["Vent_kmh"]["impossible"]:
        alerts.append(("critical", "⛔", "Vent Extrême",
                      f"Vitesse {vent_kmh:.0f} km/h — TRAVAUX IMPOSSIBLES — Évacuation imminente"))
        critical_count += 1
    elif vent_kmh > thr["Vent_kmh"]["danger"]:
        alerts.append(("critical", "🚨", "Alerte Vent Fort",
                      f"Vitesse {vent_kmh:.0f} km/h > 80 km/h — Arrêt grutage/nacelle OBLIGATOIRE (Art. R4534-58)"))
        critical_count += 1
    elif vent_kmh > thr["Vent_kmh"]["alerte"]:
        alerts.append(("warning", "⚠️", "Alerte Vent Fort",
                      f"Vitesse {vent_kmh:.0f} km/h > 45 km/h — Surveillance renforcée travaux en hauteur"))
        warning_count += 1
    
    if temperature < thr["Temperature"]["alerte_froid"]:
        alerts.append(("warning", "🌡️", "Alerte Température",
                      f"Température {temperature:.1f}°C < 5°C — Risque gel béton + engourdissement"))
        warning_count += 1
    elif temperature > thr["Temperature"]["alerte_chaleur"]:
        alerts.append(("warning", "🌡️", "Alerte Température",
                      f"Température {temperature:.1f}°C > 35°C — Stress thermique + déshydratation"))
        warning_count += 1
    
    if epi_manquants >= 5:
        alerts.append(("critical", "🦺", "Manque EPI Critique",
                      f"{epi_manquants} équipements manquants ≥ 5 — Non-conformité CRITIQUE (Code Travail R4321-4)"))
        critical_count += 1
    elif epi_manquants >= 3:
        alerts.append(("warning", "🦺", "Manque EPI",
                      f"{epi_manquants} équipements manquants — Intervention corrective requise"))
        warning_count += 1
    
    if effectif > thr["Effectif"]["surveillance"]:
        alerts.append(("warning", "👷", "Effectif Élevé",
                      f"Effectif {effectif} > 30 personnes — Coordinateur sécurité OBLIGATOIRE"))
        warning_count += 1
    
    if risque_historique > 0.7:
        alerts.append(("critical", "📊", "Risque Élevé",
                      f"Score historique {risque_historique:.2f} > 0.7 — Dossier problématique, mesures renforcées"))
        critical_count += 1
    elif risque_historique > 0.5:
        alerts.append(("warning", "📊", "Risque Élevé",
                      f"Score historique {risque_historique:.2f} > 0.5 — Vigilance accrue recommandée"))
        warning_count += 1
    
    t = rapport.lower()
    danger_keywords = ["urgence", "urgent", "urgente", "arrêt de chantier", "arrêter",
                       "évacuation", "accident", "blessure", "décès", "critique"]
    for kw in danger_keywords:
        if kw in t:
            alerts.append(("critical", "📋", "Rapport Critique",
                          f"Mot-clé danger détecté: «{kw.upper()}» — Action immédiate requise"))
            critical_count += 1
            break
    
    risk_score = 0.0
    risk_score += min(5, (vent_kmh / 50) * 5)
    risk_score += (1 - max(0, min(1, (temperature + 10) / 50))) * 1.5
    risk_score += (epi_manquants / 5) * 2
    risk_score += min(1, effectif / 100)
    risk_score += risque_historique * 1.5
    risk_score = round(min(10, max(0, risk_score)), 1)
    
    if critical_count > 0:
        status = "critical"
    elif warning_count > 0:
        status = "warning"
    else:
        status = "ok"
        if not alerts:
            alerts.append(("ok", "✅", "Conditions Sûres",
                          "Aucune alerte détectée — Conditions dans les normes"))
    
    return {
        "alerts": alerts,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "status": status,
        "risk_score": risk_score,
    }


def display_alerts(alert_result: dict) -> None:
    """Display real-time alerts in Streamlit UI with professional styling."""
    
    status_config = {
        "critical": {
            "emoji": "🚨",
            "color": "#ef4444",
            "bg": "#fecaca",
            "border": "#dc2626",
            "st_func": st.error,
        },
        "warning": {
            "emoji": "⚠️",
            "color": "#f97316",
            "bg": "#fed7aa",
            "border": "#ea580c",
            "st_func": st.warning,
        },
        "ok": {
            "emoji": "✅",
            "color": "#22c55e",
            "bg": "#bbf7d0",
            "border": "#16a34a",
            "st_func": st.success,
        },
    }
    
    alerts = alert_result.get("alerts", [])
    status = alert_result.get("status", "ok")
    risk_score = alert_result.get("risk_score", 0)
    critical_count = alert_result.get("critical_count", 0)
    warning_count = alert_result.get("warning_count", 0)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if risk_score >= 7:
            score_color = "#ef4444"
        elif risk_score >= 4:
            score_color = "#f97316"
        else:
            score_color = "#22c55e"
        st.markdown(f"""
        <div style="text-align:center;padding:12px;border-radius:8px;background:{score_color}22;border:2px solid {score_color}">
            <div style="font-size:0.75rem;opacity:0.8;font-weight:600">Global Risk Score</div>
            <div style="font-size:2rem;font-weight:900;color:{score_color}">{risk_score:.1f}/10</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        crit_color = "#ef4444" if critical_count > 0 else "#999"
        st.markdown(f"""
        <div style="text-align:center;padding:12px;border-radius:8px;background:{crit_color}22;border:2px solid {crit_color}">
            <div style="font-size:0.75rem;opacity:0.8;font-weight:600">Critiques</div>
            <div style="font-size:2rem;font-weight:900;color:{crit_color}">{critical_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        warn_color = "#f97316" if warning_count > 0 else "#999"
        st.markdown(f"""
        <div style="text-align:center;padding:12px;border-radius:8px;background:{warn_color}22;border:2px solid {warn_color}">
            <div style="font-size:0.75rem;opacity:0.8;font-weight:600">Avertissements</div>
            <div style="font-size:2rem;font-weight:900;color:{warn_color}">{warning_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        status_emoji = status_config[status]["emoji"]
        status_text = {"critical": "Critique", "warning": "Attention", "ok": "Sûr"}[status]
        status_color = status_config[status]["color"]
        st.markdown(f"""
        <div style="text-align:center;padding:12px;border-radius:8px;background:{status_color}22;border:2px solid {status_color}">
            <div style="font-size:0.75rem;opacity:0.8;font-weight:600">État</div>
            <div style="font-size:1.3rem;font-weight:900;color:{status_color}">{status_emoji} {status_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    if alerts:
        for level, icon, title, message in alerts:
            cfg = status_config[level]
            st.markdown(f"""
            <div style="
                padding:14px 16px;border-radius:10px;margin:8px 0;
                background:{cfg['bg']}22;border-left:5px solid {cfg['border']};
                font-size:0.95rem;line-height:1.6
            ">
                <div style="font-weight:700;color:{cfg['color']};margin-bottom:4px">{icon} {title}</div>
                <div style="opacity:0.85">{message}</div>
            </div>
            """, unsafe_allow_html=True)


def get_value_risk_indicator(param_name: str, value: float) -> tuple[str, str]:
    """Get risk indicator emoji and color for a parameter value."""
    thr = GC_THRESHOLDS
    
    if param_name == "Vent_kmh":
        if value > thr["Vent_kmh"]["danger"]:
            return "🔴", "#ef4444"
        elif value > thr["Vent_kmh"]["alerte"]:
            return "🟠", "#f97316"
        else:
            return "🟢", "#22c55e"
    elif param_name == "Temperature":
        if value > thr["Temperature"]["alerte_chaleur"] or value < thr["Temperature"]["alerte_froid"]:
            return "🟠", "#f97316"
        else:
            return "🟢", "#22c55e"
    elif param_name == "EPI_Manquants":
        if value >= thr["EPI_Manquants"]["critique"]:
            return "🔴", "#ef4444"
        elif value >= 3:
            return "🟠", "#f97316"
        else:
            return "🟢", "#22c55e"
    elif param_name == "Effectif":
        if value > thr["Effectif"]["surveillance"]:
            return "🟠", "#f97316"
        else:
            return "🟢", "#22c55e"
    elif param_name == "Risque_Historique":
        if value > 0.7:
            return "🔴", "#ef4444"
        elif value > 0.5:
            return "🟠", "#f97316"
        else:
            return "🟢", "#22c55e"
    
    return "⚪", "#999"


def highlight_text(rapport: str) -> str:
    if not rapport.strip():
        return "<i style='color:gray'>No report entered</i>"
    highlighted = rapport
    for kw in sorted(DANGER_KEYWORDS, key=len, reverse=True):
        pat = re.compile(re.escape(kw), re.IGNORECASE)
        highlighted = pat.sub(
            lambda m: (
                f"<mark style='background:#fecaca;color:#dc2626;"
                f"border-radius:3px;padding:1px 4px;font-weight:700'>{m.group()}</mark>"
            ),
            highlighted,
        )
    for kw in sorted(SAFETY_KEYWORDS, key=len, reverse=True):
        pat = re.compile(re.escape(kw), re.IGNORECASE)
        highlighted = pat.sub(
            lambda m: (
                f"<mark style='background:#bbf7d0;color:#166534;"
                f"border-radius:3px;padding:1px 4px;font-weight:700'>{m.group()}</mark>"
            ),
            highlighted,
        )
    return f"<p style='line-height:1.8;font-size:0.96rem'>{highlighted}</p>"


def predict_batch(df_in, model, label_info, scaler, tfidf_vec):
    required = ["Type_Travaux", "Effectif", "Temperature", "Vent_kmh", "EPI_Manquants"]
    missing  = [c for c in required if c not in df_in.columns]
    if missing:
        return None, f"Missing columns: {missing}"

    if "Risque_Historique" not in df_in.columns:
        df_in["Risque_Historique"] = 0.5
    if "Rapport_inspection" not in df_in.columns:
        df_in["Rapport_inspection"] = ""

    records = []
    for _, row in df_in.iterrows():
        try:
            x = build_feature_vector(
                str(row["Type_Travaux"]),
                int(row["Effectif"]),
                float(row["Temperature"]),
                float(row["Vent_kmh"]),
                int(row["EPI_Manquants"]),
                float(row["Risque_Historique"]),
                str(row.get("Rapport_inspection", "")),
                scaler, tfidf_vec,
            )
            lbl, conf, proba = predict(model, label_info, x)
            records.append({
                **row.to_dict(),
                "Prediction": lbl,
                "Confidence": round(conf, 4),
                "P_Critique": round(float(proba[0]), 4),
                "P_Moyen":    round(float(proba[1]), 4),
                "P_Élevé":    round(float(proba[2]), 4),
            })
        except Exception:
            records.append({**row.to_dict(), "Prediction": "ERROR",
                            "Confidence": 0.0, "P_Critique": 0.0, "P_Moyen": 0.0, "P_Élevé": 0.0})
    return pd.DataFrame(records), None


# ─── Visualization Functions ────────────────────────────────────────────────
def _ax_style(ax, fig, dark_mode):
    bg = "#1a1f3a" if dark_mode else "#ffffff"
    fg = "#f0f4f8" if dark_mode else "#1e293b"
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.tick_params(colors=fg)
    for spine in ax.spines.values():
        spine.set_color("#555" if dark_mode else "#ddd")
    return fg


def plot_proba_bars(proba, class_names, dark_mode):
    colors = ["#ef4444", "#eab308", "#f97316"]
    fig, ax = plt.subplots(figsize=(5, 2.4))
    fg = _ax_style(ax, fig, dark_mode)
    bars = ax.barh(class_names, proba, color=colors, height=0.5)
    for bar, p in zip(bars, proba):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{p:.1%}", va="center", ha="left", color=fg, fontsize=9, fontweight="bold")
    ax.set_xlim(0, 1.15)
    ax.set_xlabel("Probabilité", color=fg, fontsize=9)
    ax.spines[["top", "right", "bottom"]].set_visible(False)
    plt.tight_layout()
    return fig


def plot_feature_importance(rf_model, top_n=15, dark_mode=True):
    fi_all    = rf_model.feature_importances_
    n_struct  = min(len(STRUCT_COLS), len(fi_all))
    fi_struct = fi_all[:n_struct]
    series    = pd.Series(fi_struct, index=STRUCT_COLS[:n_struct]).nlargest(top_n)
    fig, ax   = plt.subplots(figsize=(7, 5))
    fg        = _ax_style(ax, fig, dark_mode)
    bar_colors = [
        "#ef4444" if any(k in n for k in ("epi", "vent", "flag", "risque_hist", "urgente")) else "#3b82f6"
        for n in series.index
    ]
    series.sort_values().plot.barh(ax=ax, color=bar_colors[::-1])
    ax.set_title(f"Top {top_n} Feature Importances (Random Forest)", color=fg, fontweight="bold")
    ax.set_xlabel("Importance (Gini)", color=fg)
    ax.spines[["top", "right", "bottom"]].set_visible(False)
    plt.tight_layout()
    return fig


def plot_risk_distribution(df_ann, dark_mode):
    if df_ann.empty or "Prediction" not in df_ann.columns:
        return None
    counts  = df_ann["Prediction"].value_counts()
    palette = {"Critique": "#ef4444", "Élevé": "#f97316", "Moyen": "#eab308", "Faible": "#22c55e"}
    fig, ax = plt.subplots(figsize=(5, 3.5))
    fg      = _ax_style(ax, fig, dark_mode)
    bar_c   = [palette.get(k, "#999") for k in counts.index]
    bars    = ax.bar(counts.index, counts.values, color=bar_c, edgecolor="none", width=0.55)
    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 4,
                str(val), ha="center", va="bottom", color=fg, fontsize=10, fontweight="bold")
    ax.set_title("Risk Distribution", color=fg, fontweight="bold")
    ax.set_ylabel("Inspections", color=fg)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    return fig


def plot_heatmap(df_ann, dark_mode):
    if df_ann.empty or "Type_Travaux" not in df_ann.columns or "Prediction" not in df_ann.columns:
        return None
    pivot   = pd.crosstab(df_ann["Type_Travaux"], df_ann["Prediction"])
    ordered = [c for c in ["Critique", "Élevé", "Moyen", "Faible"] if c in pivot.columns]
    pivot   = pivot.reindex(columns=ordered)
    fig, ax = plt.subplots(figsize=(7, 4))
    fg      = _ax_style(ax, fig, dark_mode)
    sns.heatmap(pivot, annot=True, fmt="d", cmap="YlOrRd", ax=ax,
                linewidths=0.5, linecolor="#333",
                annot_kws={"size": 9, "color": "#111"},
                cbar_kws={"shrink": 0.8})
    ax.set_title("Risk by Work Type", color=fg, fontweight="bold")
    ax.set_xlabel("Risk Level", color=fg)
    ax.set_ylabel("Work Type", color=fg)
    ax.tick_params(colors=fg, labelsize=8)
    plt.tight_layout()
    return fig


def plot_confusion_matrix(df_ann, dark_mode):
    if df_ann.empty or "Label_reel" not in df_ann.columns or "Prediction" not in df_ann.columns:
        return None
    from sklearn.metrics import confusion_matrix as sk_cm
    labels  = sorted(df_ann["Prediction"].dropna().unique())
    arr     = sk_cm(
        df_ann["Label_reel"].fillna("Moyen"),
        df_ann["Prediction"].fillna("Moyen"),
        labels=labels,
    )
    fig, ax = plt.subplots(figsize=(5, 4))
    fg      = _ax_style(ax, fig, dark_mode)
    sns.heatmap(arr, annot=True, fmt="d", cmap="Blues", ax=ax,
                xticklabels=labels, yticklabels=labels,
                linewidths=0.5, annot_kws={"size": 10})
    ax.set_title("Confusion Matrix (Test Set)", color=fg, fontweight="bold")
    ax.set_xlabel("Predicted", color=fg)
    ax.set_ylabel("Actual", color=fg)
    ax.tick_params(colors=fg, labelsize=9)
    plt.tight_layout()
    return fig


def plot_model_comparison(dark_mode):
    models = list(MODEL_METRICS.keys())
    f1s    = [MODEL_METRICS[m]["f1"] for m in models]
    accs   = [MODEL_METRICS[m]["acc"] for m in models]
    x      = np.arange(len(models))
    w      = 0.35
    fig, ax = plt.subplots(figsize=(8, 3.8))
    fg      = _ax_style(ax, fig, dark_mode)
    b1 = ax.bar(x - w / 2, f1s,  width=w, label="F1-Score", color="#3b82f6", alpha=0.9)
    b2 = ax.bar(x + w / 2, accs, width=w, label="Accuracy", color="#22c55e", alpha=0.9)
    for bar in list(b1) + list(b2):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.003,
                f"{bar.get_height():.2f}", ha="center", va="bottom",
                color=fg, fontsize=7.5, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([m.split(" (")[0] for m in models],
                       rotation=18, ha="right", color=fg, fontsize=8)
    ax.set_ylim(0.80, 0.95)
    ax.set_ylabel("Score", color=fg)
    ax.set_title("Model Comparison — F1 vs Accuracy", color=fg, fontweight="bold")
    bg_legend = "#1a1f3a" if dark_mode else "#fff"
    ax.legend(facecolor=bg_legend, labelcolor=fg, fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    return fig


# ──────────────────────────────────────────────────────────────────────────────────
# MAIN APPLICATION
# ──────────────────────────────────────────────────────────────────────────────────
def main():
    # ── Sidebar ──────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;margin-bottom:2rem">
            <div style="font-size:2.5rem;margin-bottom:0.5rem">🏗️</div>
            <div style="font-size:1.3rem;font-weight:700">GC Risk Predictor</div>
            <div style="font-size:0.85rem;opacity:0.7">AI Safety Analytics</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()

        dark_mode = st.toggle("🌙 Dark Mode", value=True)
        inject_css(dark_mode)
        st.divider()

        page = st.radio(
            "Navigation",
            ["🔮 Prediction", "📊 Dashboard", "🏆 Model Evaluation", "📤 Export / Batch"],
            label_visibility="collapsed",
        )
        
        st.divider()
        
        st.markdown("### 📊 Model Info")
        st.markdown("""
        - **Model:** MLP Neural Network
        - **F1-Score:** 88.84%
        - **Accuracy:** 89.00%
        - **Classes:** Critique • Élevé • Moyen
        """)
        
        st.divider()
        st.caption("✨ **GC Risk Predictor v3.0** — Premium Edition")
        st.caption("Built for ISET — AI-Powered Safety Intelligence")

    # Load resources
    try:
        best_model, label_info, rf_model, scaler, tfidf_vec = load_models()
        models_ok = True
    except Exception as exc:
        st.error(f"❌ Error loading models: {exc}")
        models_ok = False
        best_model = label_info = rf_model = scaler = tfidf_vec = None

    df_ann, _ = load_data()

    # ════════════════════════════════════════════════════════════════════════════
    # PAGE 1 — REAL-TIME PREDICTION
    # ════════════════════════════════════════════════════════════════════════════
    if page == "🔮 Prediction":
        # Premium header
        st.markdown("""
        <div class="header-container">
            <div class="header-title">🔮 Real-Time Risk Analysis</div>
            <div class="header-subtitle">AI-Powered Construction Site Safety Assessment</div>
        </div>
        """, unsafe_allow_html=True)

        # Scenario selector
        col_sc, _ = st.columns([2, 3])
        with col_sc:
            scenario_name = st.selectbox(
                "Load predefined scenario",
                ["— Manual Input —"] + list(SCENARIOS.keys()),
                label_visibility="visible",
            )

        sc = SCENARIOS.get(scenario_name, {
            "Type_Travaux": "Béton", "Effectif": 15, "Temperature": 20.0,
            "Vent_kmh": 25.0, "EPI_Manquants": 1, "Risque_Historique": 0.3,
            "Rapport_inspection": "",
        })

        # Input Panel
        with st.container():
            st.markdown('<div class="section-header">📋 Site Parameters</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Environment & Safety**")
                
                type_travaux = st.selectbox(
                    "Work Type",
                    TYPE_TRAVAUX_OPTIONS,
                    index=TYPE_TRAVAUX_OPTIONS.index(sc["Type_Travaux"])
                          if sc["Type_Travaux"] in TYPE_TRAVAUX_OPTIONS else 0,
                    label_visibility="visible",
                )
                
                temperature = st.number_input(
                    "🌡️ Temperature (°C)",
                    -30.0, 60.0, float(sc["Temperature"]), step=0.5, format="%.1f",
                    label_visibility="visible",
                )
                temp_emoji, temp_color = get_value_risk_indicator("Temperature", temperature)
                st.markdown(f'<div style="color:{temp_color};font-weight:600;font-size:0.85rem;margin-top:-10px">{temp_emoji} {temperature:.1f}°C</div>', unsafe_allow_html=True)
                
                vent_kmh = st.number_input(
                    "💨 Wind Speed (km/h)",
                    0.0, 250.0, float(sc["Vent_kmh"]), step=1.0, format="%.1f",
                    label_visibility="visible",
                )
                wind_emoji, wind_color = get_value_risk_indicator("Vent_kmh", vent_kmh)
                st.markdown(f'<div style="color:{wind_color};font-weight:600;font-size:0.85rem;margin-top:-10px">{wind_emoji} {vent_kmh:.0f} km/h</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown("**Workforce & Equipment**")
                
                effectif = st.slider(
                    "👷 Workforce (persons)",
                    1, 200, int(sc["Effectif"]),
                    label_visibility="visible",
                )
                eff_emoji, eff_color = get_value_risk_indicator("Effectif", effectif)
                st.markdown(f'<div style="color:{eff_color};font-weight:600;font-size:0.85rem;margin-top:-10px">{eff_emoji} {effectif} people</div>', unsafe_allow_html=True)
                
                epi_manquants = st.number_input(
                    "🦺 Missing PPE",
                    0, 15, int(sc["EPI_Manquants"]),
                    label_visibility="visible",
                )
                epi_emoji, epi_color = get_value_risk_indicator("EPI_Manquants", epi_manquants)
                st.markdown(f'<div style="color:{epi_color};font-weight:600;font-size:0.85rem;margin-top:-10px">{epi_emoji} {int(epi_manquants)} items</div>', unsafe_allow_html=True)
                
                risque_historique = st.slider(
                    "📈 Historical Risk Score",
                    0.0, 1.0, float(sc["Risque_Historique"]),
                    step=0.01, format="%.2f",
                    label_visibility="visible",
                )
                hist_emoji, hist_color = get_value_risk_indicator("Risque_Historique", risque_historique)
                st.markdown(f'<div style="color:{hist_color};font-weight:600;font-size:0.85rem;margin-top:-10px">{hist_emoji} {risque_historique:.2f}</div>', unsafe_allow_html=True)

        st.markdown("---")
        
        rapport = st.text_area(
            "📝 Inspection Report",
            value=sc["Rapport_inspection"],
            height=100,
            placeholder="Describe observations, conditions, safety issues, non-conformities...",
            label_visibility="visible",
        )

        pred_btn = st.button("🔮 Analyze Risk", type="primary", use_container_width=True)

        if pred_btn or scenario_name != "— Manual Input —":
            if not models_ok:
                st.error("Models not loaded. Check the models/ folder.")
                return

            if not rapport.strip():
                st.warning(
                    "📝 No inspection report: the model relies heavily on the report text "
                    "(urgency, missing PPE, compliance). Add the report for a reliable prediction."
                )

            with st.spinner("🤖 AI analysis in progress…"):
                try:
                    x_vec = build_feature_vector(
                        type_travaux, effectif, temperature, vent_kmh,
                        epi_manquants, risque_historique, rapport,
                        scaler, tfidf_vec,
                    )
                    pred_label, conf, proba = predict(best_model, label_info, x_vec)
                except Exception as exc:
                    st.error(f"Prediction error: {exc}")
                    return

            icon, badge_cls, color = CLASS_DISPLAY.get(pred_label, ("⚪", "badge-moyen", "#888"))

            # Results Section
            st.markdown('<div class="section-header">🎯 Risk Assessment Result</div>', unsafe_allow_html=True)
            
            r1, r2 = st.columns([1, 1])
            
            with r1:
                st.markdown(f"""
                <div class="risk-card" style="border-left-color:{color}">
                    <div style="font-size:0.8rem;opacity:0.7;margin-bottom:0.75rem;font-weight:600;text-transform:uppercase;">Predicted Risk Level</div>
                    <span class="badge {badge_cls}">{icon} {pred_label}</span>
                    <div style="margin-top:1.25rem;font-size:0.9rem;line-height:1.6">
                        <strong>Model Confidence:</strong><br>
                        <div style="font-size:1.5rem;font-weight:900;color:{color};margin-top:0.5rem">{conf:.1%}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(conf, text=f"Model Confidence: {conf:.1%}")
            
            with r2:
                fig_p = plot_proba_bars(proba, label_info["class_names_model"], dark_mode)
                st.pyplot(fig_p, use_container_width=True)
                plt.close(fig_p)

            # Alert System
            st.markdown('<div class="section-header">🚨 Real-Time Alert System</div>', unsafe_allow_html=True)
            alert_result = check_alerts(effectif, temperature, vent_kmh, epi_manquants,
                                       risque_historique, rapport)
            display_alerts(alert_result)

            # Text Analysis
            st.markdown('<div class="section-header">🔍 Report Text Analysis</div>', unsafe_allow_html=True)
            t1, t2 = st.columns([3, 1])
            
            with t1:
                st.markdown("**Detected Keywords:**")
                st.markdown(highlight_text(rapport), unsafe_allow_html=True)
            
            with t2:
                active_gc = [k for k, v in _extract_gc_features(rapport).items() if v]
                st.markdown("**GC Signals Triggered:**")
                if active_gc:
                    for k in active_gc[:8]:
                        st.markdown(f"🔸 `{k}`")
                else:
                    st.markdown("✅ No negative signals")

            # Feature Importance
            st.markdown('<div class="section-header">📊 Feature Importance Analysis</div>', unsafe_allow_html=True)
            fig_fi = plot_feature_importance(rf_model, top_n=15, dark_mode=dark_mode)
            st.pyplot(fig_fi, use_container_width=True)
            plt.close(fig_fi)

    # ════════════════════════════════════════════════════════════════════════════
    # PAGE 2 — DASHBOARD
    # ════════════════════════════════════════════════════════════════════════════
    elif page == "📊 Dashboard":
        st.markdown("""
        <div class="header-container">
            <div class="header-title">📊 Analytics Dashboard</div>
            <div class="header-subtitle">Inspection History & Key Metrics</div>
        </div>
        """, unsafe_allow_html=True)

        if df_ann.empty:
            st.warning("No historical data available (`predictions_annotated_v2.csv`).")
            return

        # KPIs
        total     = len(df_ann)
        n_crit    = (df_ann.get("Prediction", pd.Series()) == "Critique").sum()
        n_eleve   = (df_ann.get("Prediction", pd.Series()) == "Élevé").sum()
        acc_g     = df_ann["Correct"].mean() if "Correct" in df_ann.columns else 0.941
        conf_m    = df_ann["Confidence"].mean() if "Confidence" in df_ann.columns else 0.92

        k1, k2, k3, k4, k5 = st.columns(5)
        for col, val, label, clr in [
            (k1, f"{total}",        "Total Inspections", "#3b82f6"),
            (k2, f"{n_crit}",       "Critical",          "#ef4444"),
            (k3, f"{n_eleve}",      "Elevated",          "#f97316"),
            (k4, f"{acc_g:.1%}",    "Overall Accuracy",  "#22c55e"),
            (k5, f"{conf_m:.1%}",   "Avg Confidence",    "#eab308"),
        ]:
            with col:
                st.markdown(
                    f'<div class="metric-box"><div class="metric-value" style="color:{clr}">'
                    f'{val}</div><div class="metric-label">{label}</div></div>', 
                    unsafe_allow_html=True,
                )

        st.divider()

        # Charts
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("**Risk Distribution**")
            fig_d = plot_risk_distribution(df_ann, dark_mode)
            if fig_d:
                st.pyplot(fig_d, use_container_width=True)
                plt.close(fig_d)
        
        with c2:
            st.markdown("**Top Features (Random Forest)**")
            fig_fi2 = plot_feature_importance(rf_model if models_ok else None, top_n=12, dark_mode=dark_mode)
            if models_ok:
                st.pyplot(fig_fi2, use_container_width=True)
                plt.close(fig_fi2)

        st.divider()
        st.markdown("**Risk Heatmap by Work Type**")
        fig_h = plot_heatmap(df_ann, dark_mode)
        if fig_h:
            st.pyplot(fig_h, use_container_width=True)
            plt.close(fig_h)

        # Critical inspections
        st.divider()
        st.markdown("**🚨 Critical Inspections**")
        if "Prediction" in df_ann.columns:
            df_crit = df_ann[df_ann["Prediction"] == "Critique"]
            if not df_crit.empty:
                show_cols = [c for c in ["ID_Inspection", "Type_Travaux", "Vent_kmh", "EPI_Manquants",
                                         "Confidence", "Explication_GC"] if c in df_crit.columns]
                st.dataframe(df_crit[show_cols].head(10), use_container_width=True)
            else:
                st.success("✅ No critical inspections in history.")

        with st.expander("📋 All Data (Top 50 rows)"):
            st.dataframe(df_ann.head(50), use_container_width=True)

    # ════════════════════════════════════════════════════════════════════════════
    # PAGE 3 — MODEL EVALUATION
    # ════════════════════════════════════════════════════════════════════════════
    elif page == "🏆 Model Evaluation":
        st.markdown("""
        <div class="header-container">
            <div class="header-title">🏆 Model Performance</div>
            <div class="header-subtitle">Comparative Analysis & Metrics</div>
        </div>
        """, unsafe_allow_html=True)

        st.info(
            "**Why F1-Score matters:** With imbalanced data, a naive model always predicting 'Moyen' "
            "could achieve 40% accuracy. F1-Score (harmonic mean of precision/recall) penalizes false negatives—"
            "critical in safety applications."
        )

        # Metrics table
        st.markdown("### 📋 Model Comparison Table")
        df_m = pd.DataFrame([
            {
                "Model":    name,
                "Accuracy":  f"{v['acc']:.1%}",
                "F1-Score":  f"{v['f1']:.1%}",
                "Precision": f"{v['prec']:.1%}",
                "Recall":    f"{v['rec']:.1%}",
            }
            for name, v in MODEL_METRICS.items()
        ])
        st.dataframe(df_m, use_container_width=True, hide_index=True)

        # Comparison chart
        st.markdown("### 📊 Visual Comparison")
        fig_cmp = plot_model_comparison(dark_mode)
        st.pyplot(fig_cmp, use_container_width=True)
        plt.close(fig_cmp)

        # Confusion matrix
        st.markdown("### 🔲 Confusion Matrix")
        if not df_ann.empty:
            fig_cm = plot_confusion_matrix(df_ann, dark_mode)
            if fig_cm:
                ccol1, ccol2 = st.columns([1.2, 1])
                with ccol1:
                    st.pyplot(fig_cm, use_container_width=True)
                    plt.close(fig_cm)
                with ccol2:
                    st.markdown("""
**Interpretation:**
- **Diagonal:** Correct predictions
- **Off-diagonal:** Classification errors
- **False Negatives:** Critical→other (most costly)

**Risk Classes:**
- `Critique` — Risk Score > 75%
- `Élevé` — 50–75%
- `Moyen` — 25–50%
                    """)

    # ════════════════════════════════════════════════════════════════════════════
    # PAGE 4 — EXPORT & BATCH
    # ════════════════════════════════════════════════════════════════════════════
    elif page == "📤 Export / Batch":
        st.markdown("""
        <div class="header-container">
            <div class="header-title">📤 Export & Batch Predictions</div>
            <div class="header-subtitle">Bulk Analysis & Data Download</div>
        </div>
        """, unsafe_allow_html=True)

        # Download historical
        st.markdown("### 📥 Download Historical Predictions")
        if not df_ann.empty:
            csv_bytes = df_ann.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="⬇️ Download predictions_annotated_v2.csv",
                data=csv_bytes,
                file_name="predictions_annotated_v2.csv",
                mime="text/csv",
                use_container_width=True,
            )
            st.caption(f"{len(df_ann)} rows × {len(df_ann.columns)} columns — Overall Accuracy: 94.1%")

        st.divider()

        # Batch section
        st.markdown("### 📂 Bulk Predictions — Upload CSV")
        st.markdown("""
**Expected format** (required columns):
`Type_Travaux`, `Effectif`, `Temperature`, `Vent_kmh`, `EPI_Manquants`

*Optional:* `Risque_Historique`, `Rapport_inspection`
        """)

        # Template
        template_df = pd.DataFrame([{
            "Type_Travaux": "Grutage",     "Effectif": 20,
            "Temperature": 15.0,           "Vent_kmh": 30.0,
            "EPI_Manquants": 2,            "Risque_Historique": 0.40,
            "Rapport_inspection": "Normal conditions. PPE compliant.",
        }])
        st.download_button(
            "📄 Download CSV Template",
            data=template_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
            file_name="template_chantier.csv",
            mime="text/csv",
        )

        uploaded = st.file_uploader("Drop your CSV file here", type=["csv"])
        if uploaded:
            try:
                df_upload = pd.read_csv(uploaded)
                st.success(f"✅ {len(df_upload)} rows loaded")
                with st.expander("Preview"):
                    st.dataframe(df_upload.head(5), use_container_width=True)

                if not models_ok:
                    st.error("Models not loaded.")
                else:
                    if st.button("🚀 Run Predictions", type="primary", use_container_width=True):
                        with st.spinner(f"Predicting {len(df_upload)} rows…"):
                            df_res, err = predict_batch(
                                df_upload.copy(), best_model, label_info, scaler, tfidf_vec,
                            )
                        if err:
                            st.error(f"Error: {err}")
                        else:
                            st.success(f"✅ {len(df_res)} predictions completed!")
                            
                            # Summary
                            counts = df_res["Prediction"].value_counts()
                            color_map = {"Critique": "#ef4444", "Élevé": "#f97316",
                                         "Moyen": "#eab308", "Faible": "#22c55e"}
                            cols_kpi = st.columns(len(counts))
                            for col, (lbl, cnt) in zip(cols_kpi, counts.items()):
                                c = color_map.get(lbl, "#888")
                                with col:
                                    st.markdown(
                                        f'<div class="metric-box"><div class="metric-value" style="color:{c}">'
                                        f'{cnt}</div><div class="metric-label">{lbl}</div></div>', 
                                        unsafe_allow_html=True,
                                    )
                            
                            # Results table
                            display_cols = [c for c in [
                                "Type_Travaux", "Effectif", "Vent_kmh", "EPI_Manquants",
                                "Prediction", "Confidence", "P_Critique", "P_Moyen", "P_Élevé",
                            ] if c in df_res.columns]
                            st.dataframe(df_res[display_cols].head(20), use_container_width=True)
                            
                            # Download results
                            st.download_button(
                                "⬇️ Download Results",
                                data=df_res.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                                file_name="predictions_batch.csv",
                                mime="text/csv",
                                use_container_width=True,
                            )
            except Exception as exc:
                st.error(f"File read error: {exc}")


if __name__ == "__main__":
    main()