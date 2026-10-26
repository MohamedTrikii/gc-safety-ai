import os
import joblib
import pandas as pd
import streamlit as st
from .config import MODELS_DIR, BASE_DIR

@st.cache_resource(show_spinner="Chargement des modèles IA…")
def load_models():
    """Charge les modèles et les outils de prétraitement."""
    try:
        best_model = joblib.load(os.path.join(MODELS_DIR, "best_model_v2.joblib"))
        label_info = joblib.load(os.path.join(MODELS_DIR, "label_map_v2.joblib"))
        rf_model   = joblib.load(os.path.join(MODELS_DIR, "rf_model.joblib"))
        scaler     = joblib.load(os.path.join(MODELS_DIR, "scaler.joblib"))
        tfidf_vec  = joblib.load(os.path.join(MODELS_DIR, "tfidf_vectorizer.joblib"))
        return best_model, label_info, rf_model, scaler, tfidf_vec
    except Exception as e:
        st.error(f"Erreur lors du chargement des modèles : {str(e)}")
        return None, None, None, None, None

@st.cache_data(show_spinner="Chargement des données historiques…")
def load_data():
    """Charge les datasets historiques et annotés."""
    ann_path = os.path.join(BASE_DIR, "predictions_annotated_v2.csv")
    raw_path = os.path.join(BASE_DIR, "Dataset.csv")
    
    df_ann = pd.read_csv(ann_path) if os.path.exists(ann_path) else pd.DataFrame()
    df_raw = pd.read_csv(raw_path) if os.path.exists(raw_path) else pd.DataFrame()
    
    # Basic validation/cleaning if needed
    if not df_ann.empty and "Prediction" not in df_ann.columns:
        # Fallback or initialization if prediction column is missing
        pass
        
    return df_ann, df_raw
