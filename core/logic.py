import re
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from .config import (
    REGEX_PATTERNS, GC_LEXICON, GC_THRESHOLDS, 
    STRUCT_COLS, DANGER_KEYWORDS, SAFETY_KEYWORDS
)

def clean_text(text: str) -> str:
    """Nettoie le texte pour le NLP."""
    if not isinstance(text, str):
        return ""
    t = text.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\d+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def extract_regex_features(text: str) -> Dict[str, float]:
    """Extrait des caractéristiques numériques par Regex."""
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
                except (ValueError, IndexError):
                    pass
        feats[feat_name] = val
    
    feats["regex_urgence"]          = float(bool(re.search(r"urgent|urgente|immédiat|immédiatement", t)))
    feats["regex_arret_chantier"]   = float(bool(re.search(r"arrêt de chantier|arrêter|évacuation", t)))
    feats["regex_conf_ok"]          = float(bool(re.search(r"conformit[eé] satisfaisant|aucun risque|conforme", t)))
    feats["regex_prochaine_visite"] = float(bool(re.search(r"prochaine visite|sous quinzaine|48 heures", t)))
    return feats

def extract_gc_features(text: str) -> Dict[str, int]:
    """Extrait des indicateurs binaires basés sur le lexique GC."""
    t = str(text).lower()
    return {feat: int(any(kw in t for kw in kws)) for feat, kws in GC_LEXICON.items()}

def calculate_score_composite(
    effectif: float, temp: float, vent: float,
    epi: float, risque_hist: float
) -> float:
    """Calcule un score de risque composite basé sur les seuils GC."""
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
    scaler: Any,
    tfidf_vec: Any,
) -> np.ndarray:
    """Génère le vecteur de caractéristiques pour l'inférence."""
    
    # 1. Scaled numerical (5 features)
    num_raw = np.array([[effectif, temperature, vent_kmh, epi_manquants, risque_historique]], dtype=float)
    num_sc  = scaler.transform(num_raw)[0]

    # 2. Danger flags (6 features)
    flag_vent_danger    = int(vent_kmh    > GC_THRESHOLDS["Vent_kmh"]["danger"])
    flag_vent_alerte    = int(vent_kmh    > GC_THRESHOLDS["Vent_kmh"]["alerte"])
    flag_temp_froid     = int(temperature < GC_THRESHOLDS["Temperature"]["alerte_froid"])
    flag_temp_chaleur   = int(temperature > GC_THRESHOLDS["Temperature"]["alerte_chaleur"])
    flag_epi_critique   = int(epi_manquants >= GC_THRESHOLDS["EPI_Manquants"]["critique"])
    flag_effectif_eleve = int(effectif    > GC_THRESHOLDS["Effectif"]["surveillance"])

    # 3. Type_Travaux one-hot (Mapping manuel selon l'entraînement)
    tt = type_travaux.lower()
    type_coffrage           = int("coffrage" in tt or "béton" in tt or "beton" in tt or "maçonnerie" in tt or "maconnerie" in tt)
    type_demolition         = int("démolition" in tt or "demolition" in tt)
    type_excavation         = int("excavation" in tt or "fondation" in tt or "vrd" in tt)
    type_grutage            = int("grutage" in tt or "charpente" in tt)
    type_inconnu            = 0
    type_soudure            = 0
    type_travail_en_hauteur = int("hauteur" in tt or "toiture" in tt)

    # 4. Text features
    rx = extract_regex_features(rapport)
    gc = extract_gc_features(rapport)
    score_comp = calculate_score_composite(effectif, temperature, vent_kmh, epi_manquants, risque_historique)

    # 5. TF-IDF (Top 50)
    text_processed = clean_text(rapport)
    tfidf_full  = tfidf_vec.transform([text_processed]).toarray()[0]
    tfidf_50    = tfidf_full[:50]

    # Assemble struct features
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

def get_gc_regulatory_alerts(
    vent: float, temp: float, epi: int, effectif: int, rapport: str
) -> List[Tuple[str, str]]:
    """Retourne une liste d'alertes basées sur les normes GC."""
    alerts = []
    thr = GC_THRESHOLDS
    
    if vent > thr["Vent_kmh"]["impossible"]:
        alerts.append(("danger",  f"⛔ Vent {vent:.0f} km/h — TRAVAUX IMPOSSIBLES"))
    elif vent > thr["Vent_kmh"]["danger"]:
        alerts.append(("danger",  f"🚨 Vent {vent:.0f} km/h > 80 — Arrêt grutage OBLIGATOIRE (Art. R4534-58)"))
    elif vent > thr["Vent_kmh"]["alerte"]:
        alerts.append(("warning", f"⚠️ Vent {vent:.0f} km/h > 45 — Surveillance renforcée travaux en hauteur"))

    if temp < thr["Temperature"]["alerte_froid"]:
        alerts.append(("warning", f"🌡️ Température {temp:.1f}°C < 5°C — Gel béton + engourdissement ouvriers"))
    elif temp > thr["Temperature"]["alerte_chaleur"]:
        alerts.append(("warning", f"🌡️ Température {temp:.1f}°C > 35°C — Stress thermique + déshydratation"))

    if epi >= thr["EPI_Manquants"]["critique"]:
        alerts.append(("danger",  f"🦺 {epi} EPI manquants ≥ 5 — Non-conformité CRITIQUE (Code Travail R4321-4)"))

    if effectif > thr["Effectif"]["surveillance"]:
        alerts.append(("warning", f"👷 Effectif {effectif} > 30 — Coordinateur sécurité requis"))

    t = rapport.lower()
    for kw in ["urgence", "urgente", "arrêt", "évacuation", "accident", "blessure"]:
        if kw in t:
            alerts.append(("danger", f"📋 Rapport: mot-clé danger détecté → «{kw}»"))
            break

    if not alerts:
        alerts.append(("ok", "✅ Aucune alerte réglementaire — Conditions dans les normes"))

    return alerts

def predict_risk(model: Any, label_info: Dict, x_vec: np.ndarray) -> Tuple[str, float, np.ndarray]:
    """Réalise une prédiction et retourne le label, la confiance et les probabilités."""
    proba      = model.predict_proba(x_vec)[0]
    pred_idx   = int(np.argmax(proba))
    pred_label = label_info["class_names_model"][pred_idx]
    conf       = float(proba[pred_idx])
    return pred_label, conf, proba

def predict_batch_records(
    df_in: pd.DataFrame, 
    model: Any, 
    label_info: Dict, 
    scaler: Any, 
    tfidf_vec: Any
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Effectue des prédictions en lot sur un DataFrame."""
    required = ["Type_Travaux", "Effectif", "Temperature", "Vent_kmh", "EPI_Manquants"]
    missing  = [c for c in required if c not in df_in.columns]
    if missing:
        return None, f"Colonnes manquantes : {missing}"

    df = df_in.copy()
    if "Risque_Historique" not in df.columns:
        df["Risque_Historique"] = 0.5
    if "Rapport_inspection" not in df.columns:
        df["Rapport_inspection"] = ""

    results = []
    for _, row in df.iterrows():
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
            lbl, conf, proba = predict_risk(model, label_info, x)
            
            res_row = row.to_dict()
            res_row.update({
                "Prediction": lbl,
                "Confidence": round(conf, 4),
                "P_Critique": round(float(proba[0]), 4),
                "P_Moyen":    round(float(proba[1]), 4),
                "P_Élevé":    round(float(proba[2]), 4),
            })
            results.append(res_row)
        except Exception as e:
            res_row = row.to_dict()
            res_row.update({"Prediction": "ERREUR", "Confidence": 0.0})
            results.append(res_row)
            
    return pd.DataFrame(results), None
