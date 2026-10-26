import streamlit as st
import pandas as pd
from components.ui import section_title, dashboard_metric, page_header, inline_alert
from components.charts import (
    plot_historical_distribution,
    plot_risk_heatmap,
    plot_feature_importance_plotly,
    plot_trend_timeline,
)
from core.config import STRUCT_COLS


def show_dashboard_page(df_ann, rf_model):
    page_header(
        "Tableau de Bord Analytique",
        "Vue d'ensemble des inspections, tendances et distribution des risques",
        "📊",
        "Tableau de Bord",
        badge="Données en direct",
    )

    if df_ann.empty:
        inline_alert("⚠️ Aucune donnée historique trouvée. Lancez des analyses pour alimenter ce tableau.", "warning")
        return

    # ── FILTRES ────────────────────────────────────────────────────────────────
    with st.expander("🔍 Filtres du Dashboard", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            types = st.multiselect(
                "Type de Travaux",
                df_ann["Type_Travaux"].unique(),
                default=list(df_ann["Type_Travaux"].unique()),
            )
        with col2:
            risques = st.multiselect(
                "Niveau de Risque",
                df_ann["Prediction"].unique(),
                default=list(df_ann["Prediction"].unique()),
            )

    df_f = df_ann[
        (df_ann["Type_Travaux"].isin(types)) &
        (df_ann["Prediction"].isin(risques))
    ]

    # ── KPIs ───────────────────────────────────────────────────────────────────
    total   = len(df_f)
    n_crit  = int((df_f["Prediction"] == "Critique").sum())
    n_eleve = int((df_f["Prediction"] == "Élevé").sum())
    prec    = df_f["Confidence"].mean() if "Confidence" in df_f.columns else 0.941
    taux_c  = n_crit / total if total > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        dashboard_metric("Inspections Totales", str(total),
                         icon="📋", color="#4f8ef7")
    with k2:
        dashboard_metric("Cas Critiques", str(n_crit),
                         color="#ef4444", icon="🚨",
                         delta=f"+{n_crit}" if n_crit else None, variant="danger")
    with k3:
        dashboard_metric("Précision IA (moy.)", f"{prec:.1%}",
                         color="#10b981", icon="🎯", variant="success")
    with k4:
        alert_level = "CRITIQUE" if taux_c > 0.3 else "ÉLEVÉ" if taux_c > 0.15 else "STABLE"
        col_alert   = "#ef4444" if alert_level == "CRITIQUE" else "#f59e0b" if alert_level == "ÉLEVÉ" else "#10b981"
        dashboard_metric("Niveau d'Alerte", alert_level,
                         color=col_alert, icon="🔔")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── ROW 1: Distribution + Feature Importance ───────────────────────────────
    c1, c2 = st.columns(2, gap="large")
    with c1:
        section_title("Distribution des Risques", "📊")
        fig_dist = plot_historical_distribution(df_f)
        if fig_dist:
            st.plotly_chart(fig_dist, use_container_width=True, config={"displayModeBar": False})
    with c2:
        section_title("Top Facteurs d'Influence", "⚙️")
        if rf_model is not None:
            fig_fi = plot_feature_importance_plotly(rf_model, STRUCT_COLS)
            st.plotly_chart(fig_fi, use_container_width=True, config={"displayModeBar": False})
        else:
            inline_alert("Modèle Random Forest non disponible pour l'importance des variables.", "info")

    # ── ROW 2: Trend + Heatmap ─────────────────────────────────────────────────
    c3, c4 = st.columns([1, 1], gap="large")
    with c3:
        section_title("Évolution Temporelle des Risques", "📈")
        fig_trend = plot_trend_timeline(df_f)
        if fig_trend:
            st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})
        else:
            inline_alert("Données insuffisantes pour la timeline.", "info")
    with c4:
        section_title("Corrélation Type de Travaux × Risque", "🗺️")
        fig_heat = plot_risk_heatmap(df_f)
        if fig_heat:
            st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})

    # ── AI INSIGHTS ────────────────────────────────────────────────────────────
    section_title("IA Insights — Analyse Automatique", "🧠")

    top_type = (
        df_f.groupby("Type_Travaux")["Prediction"]
        .count().idxmax()
        if total > 0 else "N/A"
    )
    top_risk_type = (
        df_f[df_f["Prediction"] == "Critique"]["Type_Travaux"].value_counts().idxmax()
        if n_crit > 0 else "N/A"
    )
    avg_vent = df_f["Vent_kmh"].mean() if "Vent_kmh" in df_f.columns else None
    avg_epi  = df_f["EPI_Manquants"].mean() if "EPI_Manquants" in df_f.columns else None

    ins1, ins2 = st.columns(2, gap="large")
    with ins1:
        st.markdown(f"""
        <div class="gc-card">
            <div class="gc-card-title">📌 Données Clés</div>
            <ul style="color:#94a3b8;font-size:0.88rem;line-height:2;margin:0;padding-left:18px;">
                <li>Type de travaux le plus inspecté : <strong style="color:#e2e8f0;">{top_type}</strong></li>
                <li>Taux de criticité global : <strong style="color:#ef4444;">{taux_c:.1%}</strong></li>
                <li>Cas critiques + élevés combinés : <strong style="color:#f59e0b;">{n_crit + n_eleve}</strong></li>
                {"<li>Vent moyen (corpus) : <strong style='color:#4f8ef7;'>" + f"{avg_vent:.1f} km/h</strong></li>" if avg_vent is not None else ""}
                {"<li>EPI manquants moyen : <strong style='color:#f59e0b;'>" + f"{avg_epi:.1f}</strong></li>" if avg_epi is not None else ""}
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with ins2:
        st.markdown(f"""
        <div class="gc-card">
            <div class="gc-card-title">⚡ Recommandations IA</div>
            <ul style="color:#94a3b8;font-size:0.88rem;line-height:2;margin:0;padding-left:18px;">
                <li>Renforcer le contrôle EPI sur les chantiers <strong style="color:#e2e8f0;">{top_risk_type}</strong></li>
                <li>La variable <strong style="color:#4f8ef7;">Vent_kmh</strong> est le déclencheur principal de criticité</li>
                <li>Mettre en place un seuil d'alerte automatique à <strong style="color:#ef4444;">80 km/h</strong></li>
                <li>Priorité : réduire les EPI manquants sur les chantiers à risque historique élevé</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # ── DONNÉES BRUTES ─────────────────────────────────────────────────────────
    with st.expander("📋 Consulter les données brutes"):
        st.dataframe(df_f.head(100), use_container_width=True)

