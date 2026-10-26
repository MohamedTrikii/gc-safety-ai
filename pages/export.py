import json
import streamlit as st
import pandas as pd
from core.logic import predict_batch_records
from components.ui import section_title, dashboard_metric, page_header, inline_alert


def show_export_page(best_model, label_info, scaler, tfidf_vec):
    page_header(
        "Import / Export par Lot",
        "Analysez plusieurs chantiers simultanément et exportez les résultats",
        "📤",
        "Import / Export",
        badge="Batch IA",
    )

    # ── TEMPLATE ───────────────────────────────────────────────────────────────
    section_title("Template de Données", "📥")
    st.markdown("""
    <p style="font-size:0.88rem;color:#94a3b8;margin-bottom:12px;">
    Téléchargez le template CSV et complétez-le avec vos données d'inspection avant de les soumettre.
    </p>
    """, unsafe_allow_html=True)
    template_df = pd.DataFrame([{
        "Type_Travaux": "Grutage", "Effectif": 20, "Temperature": 15.0,
        "Vent_kmh": 30.0, "EPI_Manquants": 2, "Risque_Historique": 0.40,
        "Rapport_inspection": "Exemple de rapport...",
    }])
    st.download_button(
        "📄 Télécharger Template CSV",
        data=template_df.to_csv(index=False).encode("utf-8"),
        file_name="template_gc_safety.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── UPLOAD & ANALYSE ───────────────────────────────────────────────────────
    section_title("Analyse par Lot", "🚀")
    uploaded = st.file_uploader("Choisir un fichier CSV", type=["csv"])

    if not uploaded:
        inline_alert("📂 Veuillez charger un fichier CSV pour démarrer l'analyse.", "info")
        return

    try:
        df_upload = pd.read_csv(uploaded)
    except Exception as e:
        inline_alert(f"❌ Erreur de lecture du fichier : {e}", "danger")
        return

    # Validation summary
    required_cols = ["Type_Travaux", "Effectif", "Temperature", "Vent_kmh",
                     "EPI_Manquants", "Risque_Historique", "Rapport_inspection"]
    missing = [c for c in required_cols if c not in df_upload.columns]
    if missing:
        inline_alert(f"❌ Colonnes manquantes : {', '.join(missing)}", "danger")
        return

    inline_alert(f"✅ Fichier chargé : {len(df_upload)} lignes — colonnes validées.", "ok")
    st.dataframe(df_upload.head(5), use_container_width=True)

    if not st.button("🚀 Lancer l'Analyse de Masse", type="primary", use_container_width=True):
        return

    with st.spinner("Traitement IA en cours…"):
        progress = st.progress(0, text="Initialisation…")
        df_res, err = predict_batch_records(df_upload, best_model, label_info, scaler, tfidf_vec)
        progress.progress(100, text="Analyse terminée !")

    if err:
        inline_alert(f"❌ Erreur lors de l'analyse : {err}", "danger")
        return

    st.toast("✅ Analyse terminée avec succès !", icon="✅")

    # KPIs résultats
    counts = df_res["Prediction"].value_counts()
    cols   = st.columns(len(counts))
    color_map = {"Critique": "#ef4444", "Élevé": "#f59e0b",
                 "Moyen": "#10b981",    "Faible": "#4f8ef7"}
    for i, (lbl, val) in enumerate(counts.items()):
        with cols[i]:
            dashboard_metric(lbl, str(val), color_map.get(lbl, "#4f8ef7"),
                             icon="🚨" if lbl == "Critique" else "")

    st.dataframe(df_res, use_container_width=True)

    # ── TÉLÉCHARGEMENTS ────────────────────────────────────────────────────────
    section_title("Télécharger les Résultats", "⬇️")
    dl1, dl2 = st.columns(2, gap="medium")
    with dl1:
        st.download_button(
            "⬇️ Exporter CSV",
            data=df_res.to_csv(index=False).encode("utf-8"),
            file_name="predictions_gc_batch.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with dl2:
        json_data = df_res.to_dict(orient="records")
        st.download_button(
            "⬇️ Exporter JSON",
            data=json.dumps(json_data, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="predictions_gc_batch.json",
            mime="application/json",
            use_container_width=True,
        )

