import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from core.config import MODEL_METRICS, GC_THRESHOLDS
from components.ui import section_title, dashboard_metric, page_header, inline_alert
from components.charts import plot_model_comparison_plotly


def show_evaluation_page():
    page_header(
        "Performance des Modèles IA",
        "Métriques de validation, comparaison inter-modèles et analyse de robustesse",
        "🏆",
        "Performance IA",
        badge="Validation croisée k=5",
    )

    st.markdown("""
    <div class="gc-card" style="margin-bottom:18px;">
        <div class="gc-card-title">🤖 Modèle Champion Sélectionné</div>
        <p style="font-size:0.88rem;color:#94a3b8;line-height:1.7;margin:0;">
            Le modèle <strong style="color:#4f8ef7;">MLP (Multi-Layer Perceptron)</strong> a été sélectionné après une comparaison
            rigoureuse sur 5 algorithmes. Il offre le meilleur équilibre entre <em>généralisation textuelle</em>
            (rapports d'inspection) et <em>performance sur classes déséquilibrées</em> grâce à son F1-Score de
            <strong style="color:#10b981;">88.84 %</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── COMPARAISON GLOBALE ────────────────────────────────────────────────────
    section_title("Comparaison Globale des Modèles", "📊")
    fig_cmp = plot_model_comparison_plotly(MODEL_METRICS)
    st.plotly_chart(fig_cmp, use_container_width=True, config={"displayModeBar": False})

    # ── DETAIL PAR MODELE ──────────────────────────────────────────────────────
    section_title("Métriques Détaillées par Modèle", "🔍")
    model_name = st.selectbox(
        "Sélectionner un modèle",
        list(MODEL_METRICS.keys()),
        label_visibility="collapsed",
    )
    m = MODEL_METRICS[model_name]

    c1, c2, c3, c4 = st.columns(4)
    is_best = model_name == "MLP Neural Network v2"
    with c1:
        dashboard_metric("Accuracy", f"{m['acc']:.1%}", "#4f8ef7",
                         icon="🎯", delta="+2.1%" if is_best else None)
    with c2:
        dashboard_metric("F1-Score", f"{m['f1']:.1%}", "#10b981",
                         icon="⚖️", delta="+1.8%" if is_best else None)
    with c3:
        dashboard_metric("Précision", f"{m['prec']:.1%}", "#6366f1", icon="🔎")
    with c4:
        dashboard_metric("Rappel", f"{m['rec']:.1%}", "#ef4444", icon="📡")

    if is_best:
        inline_alert("✅ Ce modèle est le champion actif déployé en production.", "ok")

    # ── VALIDATION CROISÉE ─────────────────────────────────────────────────────
    section_title("Résultats de Validation Croisée (k=5)", "🔄")
    df_cv = pd.DataFrame([
        {"Algorithme": "MLP Neural Network v2", "F1 Moyen": "88.84%", "Stabilité": "±1.2%", "Statut": "✅ Champion"},
        {"Algorithme": "XGBoost (tuned)",        "F1 Moyen": "87.30%", "Stabilité": "±1.7%", "Statut": "Runner-up"},
        {"Algorithme": "Random Forest",           "F1 Moyen": "85.50%", "Stabilité": "±1.9%", "Statut": "Backup"},
        {"Algorithme": "SVM (RBF)",               "F1 Moyen": "82.10%", "Stabilité": "±2.3%", "Statut": "Évalué"},
        {"Algorithme": "Logistic Regression",     "F1 Moyen": "78.40%", "Stabilité": "±2.1%", "Statut": "Référence"},
    ])
    st.dataframe(df_cv, use_container_width=True, hide_index=True)

    with st.expander("📝 Notes Méthodologiques"):
        st.markdown("""
        - **F1-Score** indispensable : nos classes sont déséquilibrées (peu de cas *Critiques* vs *Moyens*)  
        - **Dataset** : 2 400+ inspections annotées par des experts sécurité Génie Civil  
        - **Feature engineering** : 98 features (5 numériques + GC lexical + TF-IDF sur rapport)  
        - **Seuil de déploiement** : F1 ≥ 85 % avec stabilité ≤ ±2.0 % en cross-validation  
        """)

    # ── ARCHITECTURE DUAL-STREAM ───────────────────────────────────────────────
    section_title("Architecture Dual-Stream", "🔀")
    st.markdown("""
    <div class="gc-card" style="margin-bottom:18px;">
        <div class="gc-card-title">⚙️ Principe : Fusion de deux flux d'information</div>
        <p style="font-size:0.87rem;color:#94a3b8;line-height:1.7;margin:0;">
            Le modèle Dual-Stream traite <strong>simultanément</strong> les données numériques structurées (Flux A)
            et le rapport textuel d'inspection (Flux B), puis fusionne les représentations apprises avant la
            couche de classification finale. Cette architecture capture à la fois les signaux quantitatifs
            (vent, EPI, effectif) et les nuances sémantiques des rapports rédigés par les inspecteurs.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:linear-gradient(135deg,rgba(15,22,36,0.95),rgba(22,31,51,0.95));
                border:1px solid rgba(79,142,247,0.2);border-radius:18px;padding:28px 20px;
                font-family:'JetBrains Mono',monospace;font-size:0.82rem;color:#94a3b8;
                overflow-x:auto;line-height:2;">
    <div style="display:flex;gap:30px;align-items:flex-start;flex-wrap:wrap;justify-content:center;">

      <!-- FLUX A -->
      <div style="flex:1;min-width:200px;text-align:center;">
        <div style="color:#4f8ef7;font-weight:700;font-size:0.95rem;margin-bottom:10px;">
          🔢 FLUX A — Données Numériques
        </div>
        <div style="background:rgba(79,142,247,0.08);border:1px solid rgba(79,142,247,0.25);
                    border-radius:10px;padding:10px 14px;margin-bottom:8px;">
          Effectif · Temp · Vent · EPI · Risque_Hist
        </div>
        <div style="color:#64748b;">↓ StandardScaler</div>
        <div style="background:rgba(79,142,247,0.08);border:1px solid rgba(79,142,247,0.25);
                    border-radius:10px;padding:10px 14px;margin:8px 0;">
          Flags GC (11) + One-Hot Travaux (7)<br>+ Regex (9) + Score Composite
        </div>
        <div style="color:#64748b;">↓ Dense(64) → ReLU</div>
        <div style="background:rgba(79,142,247,0.15);border:1px solid rgba(79,142,247,0.4);
                    border-radius:10px;padding:8px 14px;margin-top:8px;color:#4f8ef7;font-weight:600;">
          Représentation A — dim 64
        </div>
      </div>

      <!-- FUSION -->
      <div style="flex:0 0 60px;display:flex;flex-direction:column;align-items:center;
                  justify-content:center;padding-top:80px;">
        <div style="font-size:1.6rem;">⊕</div>
        <div style="color:#6366f1;font-size:0.72rem;font-weight:700;margin-top:4px;">FUSION</div>
        <div style="color:#64748b;font-size:0.68rem;">Concat</div>
      </div>

      <!-- FLUX B -->
      <div style="flex:1;min-width:200px;text-align:center;">
        <div style="color:#10b981;font-weight:700;font-size:0.95rem;margin-bottom:10px;">
          📝 FLUX B — Rapport Textuel (NLP)
        </div>
        <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);
                    border-radius:10px;padding:10px 14px;margin-bottom:8px;">
          Rapport d'inspection (texte libre)
        </div>
        <div style="color:#64748b;">↓ clean_text() · Tokenisation</div>
        <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);
                    border-radius:10px;padding:10px 14px;margin:8px 0;">
          TF-IDF Bigrams (top 50 features)<br>+ Lexique GC (20 indicateurs binaires)
        </div>
        <div style="color:#64748b;">↓ Dense(64) → ReLU</div>
        <div style="background:rgba(16,185,129,0.15);border:1px solid rgba(16,185,129,0.4);
                    border-radius:10px;padding:8px 14px;margin-top:8px;color:#10b981;font-weight:600;">
          Représentation B — dim 64
        </div>
      </div>

    </div>

    <div style="text-align:center;margin-top:22px;">
      <div style="color:#64748b;">↓ Concatenation [A ⊕ B] → dim 128</div>
      <div style="background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.35);
                  border-radius:10px;padding:10px 30px;margin:10px auto;display:inline-block;
                  color:#a5b4fc;font-weight:600;">
        Dense(128) → ReLU → Dropout(0.3)
      </div>
      <div style="color:#64748b;">↓ Dense(64) → ReLU</div>
      <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.35);
                  border-radius:10px;padding:10px 30px;margin:10px auto;display:inline-block;
                  color:#fca5a5;font-weight:700;letter-spacing:1px;">
        Softmax → 🔴 Critique &nbsp;|&nbsp; 🟠 Élevé &nbsp;|&nbsp; 🟡 Moyen &nbsp;|&nbsp; 🟢 Faible
      </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    col_ds1, col_ds2, col_ds3 = st.columns(3)
    with col_ds1:
        st.markdown("""<div class="gc-card" style="text-align:center;padding:16px;">
            <div style="font-size:1.6rem;">🔢</div>
            <div style="color:#4f8ef7;font-weight:700;margin:6px 0;">Flux A</div>
            <div style="color:#94a3b8;font-size:0.82rem;">48 features numériques<br>+ structurelles GC</div>
        </div>""", unsafe_allow_html=True)
    with col_ds2:
        st.markdown("""<div class="gc-card" style="text-align:center;padding:16px;">
            <div style="font-size:1.6rem;">📝</div>
            <div style="color:#10b981;font-weight:700;margin:6px 0;">Flux B</div>
            <div style="color:#94a3b8;font-size:0.82rem;">50 TF-IDF bigrams<br>+ 20 lexique GC</div>
        </div>""", unsafe_allow_html=True)
    with col_ds3:
        st.markdown("""<div class="gc-card" style="text-align:center;padding:16px;">
            <div style="font-size:1.6rem;">⊕</div>
            <div style="color:#6366f1;font-weight:700;margin:6px 0;">Fusion</div>
            <div style="color:#94a3b8;font-size:0.82rem;">Concat 128-dim<br>→ 4 classes de risque</div>
        </div>""", unsafe_allow_html=True)

    # ── ANALYSE DE SENSIBILITÉ DES SEUILS GC ──────────────────────────────────
    section_title("Analyse de Sensibilité des Seuils GC", "🎚️")
    st.markdown("""
    <div class="gc-card" style="margin-bottom:18px;">
        <div class="gc-card-title">📐 Impact des seuils réglementaires sur la détection</div>
        <p style="font-size:0.87rem;color:#94a3b8;line-height:1.7;margin:0;">
            Ajustez les seuils d'alerte GC ci-dessous pour visualiser leur impact sur le taux de
            déclenchement des alertes et la sensibilité du pipeline de prédiction.
            Les seuils actuels sont ceux définis dans les normes de sécurité chantier.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        seuil_vent_alerte  = st.slider("💨 Vent — Seuil Alerte (km/h)",   10, 100,
                                        GC_THRESHOLDS["Vent_kmh"]["alerte"], step=5)
        seuil_vent_danger  = st.slider("💨 Vent — Seuil Danger (km/h)",   30, 150,
                                        GC_THRESHOLDS["Vent_kmh"]["danger"], step=5)
    with col_s2:
        seuil_temp_froid   = st.slider("🌡️ Temp. Froid — Seuil Alerte (°C)", -20, 20,
                                        GC_THRESHOLDS["Temperature"]["alerte_froid"], step=1)
        seuil_temp_chaleur = st.slider("🌡️ Temp. Chaleur — Seuil Alerte (°C)", 25, 50,
                                        GC_THRESHOLDS["Temperature"]["alerte_chaleur"], step=1)
    with col_s3:
        seuil_epi          = st.slider("🦺 EPI — Seuil Critique (nb)",  1, 15,
                                        GC_THRESHOLDS["EPI_Manquants"]["critique"], step=1)
        seuil_effectif     = st.slider("👷 Effectif — Seuil Surveillance",  5, 100,
                                        GC_THRESHOLDS["Effectif"]["surveillance"], step=5)

    # Simulate alert rates over a synthetic distribution of 500 inspections
    np.random.seed(42)
    n = 500
    syn_vent   = np.random.exponential(scale=30, size=n).clip(0, 200)
    syn_temp   = np.random.normal(loc=18, scale=12, size=n).clip(-25, 55)
    syn_epi    = np.random.poisson(lam=2, size=n).clip(0, 15)
    syn_eff    = np.random.randint(5, 80, size=n)

    def _alert_rate(vent_a, vent_d, t_froid, t_chaud, epi_c, eff_s):
        alerte  = (syn_vent > vent_a).sum()
        danger  = (syn_vent > vent_d).sum()
        t_f_cnt = (syn_temp < t_froid).sum()
        t_c_cnt = (syn_temp > t_chaud).sum()
        epi_cnt = (syn_epi >= epi_c).sum()
        eff_cnt = (syn_eff > eff_s).sum()
        return {
            "Alerte Vent":    alerte  / n * 100,
            "Danger Vent":    danger  / n * 100,
            "Froid":          t_f_cnt / n * 100,
            "Chaleur":        t_c_cnt / n * 100,
            "EPI Critique":   epi_cnt / n * 100,
            "Effectif élevé": eff_cnt / n * 100,
        }

    rates_current = _alert_rate(
        GC_THRESHOLDS["Vent_kmh"]["alerte"], GC_THRESHOLDS["Vent_kmh"]["danger"],
        GC_THRESHOLDS["Temperature"]["alerte_froid"], GC_THRESHOLDS["Temperature"]["alerte_chaleur"],
        GC_THRESHOLDS["EPI_Manquants"]["critique"], GC_THRESHOLDS["Effectif"]["surveillance"],
    )
    rates_new = _alert_rate(seuil_vent_alerte, seuil_vent_danger,
                            seuil_temp_froid, seuil_temp_chaleur,
                            seuil_epi, seuil_effectif)

    categories = list(rates_current.keys())
    fig_sens = go.Figure()
    fig_sens.add_trace(go.Bar(
        name="Seuils GC Normatifs",
        x=categories,
        y=list(rates_current.values()),
        marker_color="rgba(79,142,247,0.7)",
        marker_line_color="#4f8ef7",
        marker_line_width=1.5,
    ))
    fig_sens.add_trace(go.Bar(
        name="Seuils Ajustés",
        x=categories,
        y=list(rates_new.values()),
        marker_color="rgba(239,68,68,0.65)",
        marker_line_color="#ef4444",
        marker_line_width=1.5,
    ))
    fig_sens.update_layout(
        barmode="group",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(title="Taux de déclenchement (%)", gridcolor="rgba(255,255,255,0.08)"),
        xaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=20),
        height=340,
    )
    st.plotly_chart(fig_sens, use_container_width=True, config={"displayModeBar": False})

    # Delta summary
    delta_col = st.columns(len(categories))
    for i, (cat, val_new) in enumerate(rates_new.items()):
        val_ref = rates_current[cat]
        delta   = val_new - val_ref
        color   = "#ef4444" if delta > 0 else "#10b981" if delta < 0 else "#94a3b8"
        arrow   = "▲" if delta > 0 else "▼" if delta < 0 else "●"
        with delta_col[i]:
            st.markdown(f"""<div class="gc-card" style="text-align:center;padding:12px 8px;">
                <div style="font-size:0.72rem;color:#64748b;margin-bottom:4px;">{cat}</div>
                <div style="font-size:1.1rem;font-weight:700;color:{color};">{arrow} {abs(delta):.1f}%</div>
                <div style="font-size:0.68rem;color:#475569;">vs seuil normatif</div>
            </div>""", unsafe_allow_html=True)

    with st.expander("💡 Interprétation de la sensibilité"):
        st.markdown("""
        - **Abaisser un seuil** → plus d'alertes déclenchées → meilleure détection mais risque de faux positifs
        - **Relever un seuil** → moins d'alertes → réduction de la charge opérationnelle mais risque de manquer des situations dangereuses
        - Les seuils normatifs GC actuels ont été calibrés pour un **équilibre précision/rappel optimal** sur le dataset d'entraînement (2 400 inspections)
        - La variable **Vent** est la plus sensible : une variation de ±10 km/h sur le seuil d'alerte peut modifier le taux de déclenchement de **±8 à 12 %**
        """)

