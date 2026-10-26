import os

# ─── Constants ──────────────────────────────────────────────────────────────────
RANDOM_STATE = 42
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    "Critique": ("🔴", "badge-critique", "#c62828"),
    "Élevé":    ("🟠", "badge-eleve",    "#e65100"),
    "Moyen":    ("🟡", "badge-moyen",     "#f9a825"),
    "Faible":   ("🟢", "badge-faible",    "#2e7d32"),
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
