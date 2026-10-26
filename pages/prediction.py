import streamlit as st
import time
from core.config import SCENARIOS, TYPE_TRAVAUX_OPTIONS, GC_THRESHOLDS
from core.logic import build_feature_vector, predict_risk, get_gc_regulatory_alerts, extract_gc_features
from components.ui import (
    section_title, risk_badge, highlighted_report,
    risk_result_card, page_header, gc_signal_pills,
    animated_prob_bars, score_breakdown_card, input_validation_badge,
    inline_alert,
)
from components.charts import plot_confidence_gauge, plot_risk_radar, plot_prediction_confidence


# ─── LIVE ALERT PANEL ────────────────────────────────────────────────────────────
def _render_live_alert_panel(vent: float, temp: float, epi: int, effectif: int) -> None:
    """Panneau de surveillance temps réel des seuils GC — mis à jour à chaque interaction."""
    thr = GC_THRESHOLDS

    checks = [
        {
            "label": f"Vent {vent:.0f} km/h",
            "ok": vent <= thr["Vent_kmh"]["alerte"],
            "warn": thr["Vent_kmh"]["alerte"] < vent <= thr["Vent_kmh"]["danger"],
            "crit": vent > thr["Vent_kmh"]["danger"],
            "msg_warn": f"Alerte > {thr['Vent_kmh']['alerte']} km/h",
            "msg_crit": f"DANGER > {thr['Vent_kmh']['danger']} km/h",
            "icon": "💨",
        },
        {
            "label": f"Temp. {temp:.1f} °C",
            "ok":   thr["Temperature"]["alerte_froid"] <= temp <= thr["Temperature"]["alerte_chaleur"],
            "warn": temp < thr["Temperature"]["alerte_froid"] or temp > thr["Temperature"]["alerte_chaleur"],
            "crit": temp < thr["Temperature"]["min_possible"] + 5 or temp > thr["Temperature"]["max_possible"] - 5,
            "msg_warn": "Stress thermique",
            "msg_crit": "Température extrême",
            "icon": "🌡️",
        },
        {
            "label": f"EPI {epi} manquants",
            "ok":   epi == 0,
            "warn": 0 < epi < thr["EPI_Manquants"]["critique"],
            "crit": epi >= thr["EPI_Manquants"]["critique"],
            "msg_warn": "EPI incomplets",
            "msg_crit": f"CRITIQUE ≥ {thr['EPI_Manquants']['critique']}",
            "icon": "🦺",
        },
        {
            "label": f"Effectif {effectif}",
            "ok":   effectif <= thr["Effectif"]["surveillance"],
            "warn": effectif > thr["Effectif"]["surveillance"],
            "crit": effectif > thr["Effectif"]["max_possible"] * 0.75,
            "msg_warn": f"> {thr['Effectif']['surveillance']} → SPS requis",
            "msg_crit": "Sureffectif critique",
            "icon": "👷",
        },
    ]

    n_danger  = sum(1 for c in checks if c["crit"])
    n_warning = sum(1 for c in checks if c["warn"] and not c["crit"])
    n_ok      = sum(1 for c in checks if c["ok"])

    if n_danger > 0:
        panel_color = "#ef4444"; panel_bg = "rgba(239,68,68,0.07)"; panel_icon = "🚨"; status_txt = "ALERTE CRITIQUE"
    elif n_warning > 0:
        panel_color = "#f59e0b"; panel_bg = "rgba(245,158,11,0.07)"; panel_icon = "⚠️"; status_txt = "SURVEILLANCE"
    else:
        panel_color = "#10b981"; panel_bg = "rgba(16,185,129,0.07)"; panel_icon = "✅"; status_txt = "NOMINAL"

    rows_html = ""
    for c in checks:
        if c["crit"]:
            dot = "#ef4444"; badge = f'<span style="font-size:0.68rem;color:#ef4444;font-weight:700;">⛔ {c["msg_crit"]}</span>'
        elif c["warn"]:
            dot = "#f59e0b"; badge = f'<span style="font-size:0.68rem;color:#f59e0b;font-weight:600;">⚠️ {c["msg_warn"]}</span>'
        else:
            dot = "#10b981"; badge = '<span style="font-size:0.68rem;color:#10b981;">✓ OK</span>'

        rows_html += f"""
        <div style="display:flex;align-items:center;gap:8px;padding:5px 0;
                    border-bottom:1px solid rgba(255,255,255,0.04);">
            <span style="font-size:0.9rem;">{c["icon"]}</span>
            <span style="flex:1;font-size:0.78rem;color:#94a3b8;">{c["label"]}</span>
            <span style="width:8px;height:8px;border-radius:50%;background:{dot};
                         box-shadow:0 0 6px {dot};flex-shrink:0;"></span>
            {badge}
        </div>"""

    st.markdown(f"""
    <div style="background:{panel_bg};border:1px solid {panel_color}40;border-radius:14px;
                padding:14px 16px;margin-top:14px;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
            <span style="font-size:1.1rem;">{panel_icon}</span>
            <span style="font-family:'Space Grotesk',sans-serif;font-weight:700;
                         font-size:0.78rem;color:{panel_color};letter-spacing:1.5px;
                         text-transform:uppercase;">Monitoring — {status_txt}</span>
            <span style="margin-left:auto;background:{panel_color}22;border:1px solid {panel_color}55;
                         border-radius:99px;font-size:0.62rem;font-weight:700;color:{panel_color};
                         padding:2px 8px;">{n_danger}🔴 {n_warning}🟡 {n_ok}🟢</span>
        </div>
        {rows_html}
        <div style="font-size:0.65rem;color:#475569;margin-top:8px;text-align:right;">
            ↻ Mis à jour en temps réel
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── MAIN PAGE ───────────────────────────────────────────────────────────────────
def show_prediction_page(best_model, label_info, scaler, tfidf_vec) -> None:
    page_header(
        "Analyse de Risque",
        "Prédiction IA temps réel du niveau de risque d'un chantier de Génie Civil",
        "🔮",
        "Analyse de Risque",
        badge="LIVE · MLP v2 · F1=88.84%"
    )

    # ── MODE TABS ──────────────────────────────────────────────────────────────
    tab_single, tab_compare = st.tabs(["📍 Analyse Simple", "⚖️ Comparaison de Scénarios"])

    with tab_single:
        _single_prediction_ui(best_model, label_info, scaler, tfidf_vec)

    with tab_compare:
        _compare_scenarios_ui(best_model, label_info, scaler, tfidf_vec)


# ─── SINGLE PREDICTION ───────────────────────────────────────────────────────────
def _single_prediction_ui(best_model, label_info, scaler, tfidf_vec) -> None:
    col_form, col_side = st.columns([3, 1], gap="large")

    # Read live values from session_state (populated by widgets on previous render)
    _vent = st.session_state.get("vent_single", 25.0)
    _temp = st.session_state.get("temp_single", 20.0)
    _epi  = st.session_state.get("epi_single",  1)
    _eff  = st.session_state.get("eff_single",  15)

    with col_side:
        # Scenario picker card
        st.markdown("""
        <div class="gc-card">
            <div class="gc-card-title">⚡ Scénario Prédéfini</div>
        </div>
        """, unsafe_allow_html=True)
        scenario_name = st.selectbox(
            "Charger un cas type",
            ["— Saisie manuelle —"] + list(SCENARIOS.keys()),
            label_visibility="collapsed",
        )
        sc = SCENARIOS.get(scenario_name, {
            "Type_Travaux": "Béton", "Effectif": 15, "Temperature": 20.0,
            "Vent_kmh": 25.0, "EPI_Manquants": 1, "Risque_Historique": 0.3,
            "Rapport_inspection": "",
        })

        # ── PANNEAU DE SURVEILLANCE TEMPS RÉEL ─────────────────────────────
        _render_live_alert_panel(_vent, _temp, _epi, _eff)

        st.markdown("""
        <div class="gc-card" style="margin-top:14px;">
            <div class="gc-card-title">💡 Guide de Saisie</div>
            <p style="font-size:0.82rem; color:#94a3b8; line-height:1.6; margin:0;">
                Renseignez les données issues de l'inspection chantier. Le modèle IA analyse <strong>6 paramètres</strong> structurés + le texte du rapport pour générer la prédiction.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_form:
        inputs = _render_form("single", sc)
        # Real-time validation badges
        input_validation_badge(
            inputs["vent"], inputs["temp"], inputs["epi"], inputs["effectif"]
        )
        btn_predict = st.button(
            "🔮  Lancer l'Analyse Prédictive",
            type="primary",
            use_container_width=True,
            key="btn_single"
        )

    if btn_predict:
        with st.spinner("L'IA analyse les données du chantier…"):
            time.sleep(0.6)
            try:
                res = _run_analysis(inputs, best_model, label_info, scaler, tfidf_vec)
            except Exception as exc:
                st.error(f"Erreur de prédiction : {exc}")
                return
        _display_results(res, inputs, label_info)


# ─── COMPARE SCENARIOS ───────────────────────────────────────────────────────────
def _compare_scenarios_ui(best_model, label_info, scaler, tfidf_vec) -> None:
    st.markdown("Comparez deux configurations de chantier côte à côte pour mesurer l'impact de chaque facteur de risque.")
    st.markdown("<br>", unsafe_allow_html=True)

    col_a, sep, col_b = st.columns([5, 1, 5], gap="small")

    with col_a:
        st.markdown("""<div class="gc-card-title" style="margin-bottom:14px;">📋 Scénario A</div>""", unsafe_allow_html=True)
        inputs_a = _render_form("cmp_a")

    with sep:
        st.markdown("<div style='display:flex;align-items:center;justify-content:center;height:100%;'><span style='font-size:1.5rem;color:#334155;'>⚖️</span></div>", unsafe_allow_html=True)

    with col_b:
        st.markdown("""<div class="gc-card-title" style="margin-bottom:14px;">📋 Scénario B</div>""", unsafe_allow_html=True)
        inputs_b = _render_form("cmp_b")

    if st.button("🚀  Analyser les deux scénarios", type="primary", use_container_width=True, key="btn_compare"):
        with st.spinner("Analyse comparative en cours…"):
            time.sleep(0.5)
            res_a = _run_analysis(inputs_a, best_model, label_info, scaler, tfidf_vec)
            res_b = _run_analysis(inputs_b, best_model, label_info, scaler, tfidf_vec)

        st.markdown("---")
        r1, r2 = st.columns(2, gap="large")
        with r1:
            st.markdown("#### Résultat — Scénario A")
            _display_results(res_a, inputs_a, label_info)
        with r2:
            st.markdown("#### Résultat — Scénario B")
            _display_results(res_b, inputs_b, label_info)


# ─── FORM RENDER ─────────────────────────────────────────────────────────────────
def _render_form(suffix: str, defaults: dict = None) -> dict:
    if defaults is None:
        defaults = {
            "Type_Travaux": "Béton", "Effectif": 15, "Temperature": 20.0,
            "Vent_kmh": 25.0, "EPI_Manquants": 1, "Risque_Historique": 0.3,
            "Rapport_inspection": "",
        }

    with st.container():
        st.markdown('<div class="gc-card">', unsafe_allow_html=True)
        st.markdown('<div class="gc-card-title">⚙️ Paramètres du Chantier</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2, gap="medium")
        with c1:
            type_trav = st.selectbox(
                "🔧 Nature des Travaux",
                TYPE_TRAVAUX_OPTIONS,
                index=TYPE_TRAVAUX_OPTIONS.index(defaults["Type_Travaux"])
                if defaults["Type_Travaux"] in TYPE_TRAVAUX_OPTIONS else 0,
                key=f"type_{suffix}",
            )
            effectif = st.number_input(
                "👷 Effectif sur site (personnes)", 1, 200,
                int(defaults["Effectif"]), key=f"eff_{suffix}"
            )
            temperature = st.number_input(
                "🌡️ Température (°C)", -30.0, 60.0,
                float(defaults["Temperature"]), step=0.5, key=f"temp_{suffix}"
            )

        with c2:
            vent = st.number_input(
                "💨 Vitesse du vent (km/h)", 0.0, 250.0,
                float(defaults["Vent_kmh"]), step=1.0, key=f"vent_{suffix}"
            )
            epi = st.number_input(
                "🦺 EPI Manquants", 0, 15,
                int(defaults["EPI_Manquants"]),
                help="Équipements de Protection Individuelle manquants ou non conformes",
                key=f"epi_{suffix}",
            )
            hist = st.slider(
                "📈 Risque Historique du chantier", 0.0, 1.0,
                float(defaults["Risque_Historique"]),
                step=0.01, format="%.2f", key=f"hist_{suffix}",
                help="0 = historique sûr, 1 = historique très accidentogène"
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # Rapport section separate card feel
        st.markdown('<div class="gc-card" style="margin-top:4px;">', unsafe_allow_html=True)
        st.markdown('<div class="gc-card-title">📝 Rapport d\'Inspection</div>', unsafe_allow_html=True)
        rapport = st.text_area(
            "Saisissez le contenu du rapport",
            value=defaults["Rapport_inspection"],
            height=110,
            placeholder="Ex: Vent à 95 km/h, harnais absents, grue en opération. Intervention urgente requise…",
            key=f"rapport_{suffix}",
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    return {
        "type": type_trav, "effectif": effectif, "temp": temperature,
        "vent": vent, "epi": epi, "hist": hist, "rapport": rapport,
    }


# ─── CORE ANALYSIS ───────────────────────────────────────────────────────────────
def _run_analysis(inputs: dict, model, label_info, scaler, tfidf_vec) -> dict:
    x_vec = build_feature_vector(
        inputs["type"], inputs["effectif"], inputs["temp"],
        inputs["vent"], inputs["epi"], inputs["hist"],
        inputs["rapport"], scaler, tfidf_vec,
    )
    label, conf, proba = predict_risk(model, label_info, x_vec)
    alerts = get_gc_regulatory_alerts(
        inputs["vent"], inputs["temp"], inputs["epi"],
        inputs["effectif"], inputs["rapport"]
    )
    active_gc = [k for k, v in extract_gc_features(inputs["rapport"]).items() if v]
    return {"label": label, "conf": conf, "proba": proba, "alerts": alerts, "gc_signals": active_gc}


# ─── DISPLAY RESULTS ─────────────────────────────────────────────────────────────
def _display_results(res: dict, inputs: dict, label_info) -> None:

    # ── 1. RESULT CARD + GAUGE ──
    section_title("Résultat de l'Analyse", "🎯")
    r1, r2, r3 = st.columns([2, 1, 1], gap="large")
    with r1:
        risk_result_card(res["label"], res["conf"])
    with r2:
        st.markdown("<div class='gc-card' style='padding:16px;'>", unsafe_allow_html=True)
        fig_gauge = plot_confidence_gauge(res["conf"], res["label"])
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
    with r3:
        st.markdown("<div class='gc-card' style='padding:16px;'>", unsafe_allow_html=True)
        fig_radar = plot_risk_radar(inputs)
        st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 2. ANIMATED PROBABILITY BARS ──
    section_title("Distribution des Probabilités", "📊")
    animated_prob_bars(list(res["proba"]), list(label_info["class_names_model"]))

    # ── 3. SCORE BREAKDOWN ──
    from core.logic import calculate_score_composite
    score = calculate_score_composite(
        inputs["vent"], inputs["temp"], inputs["epi"],
        inputs["effectif"], inputs["hist"]
    )
    score_breakdown_card(
        inputs["vent"], inputs["temp"], inputs["epi"],
        inputs["effectif"], inputs["hist"], score
    )

    # ── 4. ALERTS ──
    section_title("Alertes Réglementaires GC", "⚠️")
    if res["alerts"]:
        for level, msg in res["alerts"]:
            css = {"danger": "alert-danger", "warning": "alert-warning", "ok": "alert-ok"}.get(level, "alert-info")
            st.markdown(f'<div class="alert-box {css}"><div>{msg}</div></div>', unsafe_allow_html=True)
    else:
        inline_alert("✅ Aucune alerte réglementaire détectée.", "ok")

    # ── 5. REPORT ANALYSIS ──
    section_title("Analyse Textuelle du Rapport", "🔍")
    col_rep, col_gc = st.columns([2, 1], gap="large")
    with col_rep:
        highlighted_report(inputs["rapport"])
    with col_gc:
        st.markdown(
            '<div class="gc-card-title" style="margin-bottom:10px;">⚡ Signaux GC Détectés</div>',
            unsafe_allow_html=True
        )
        gc_signal_pills(res.get("gc_signals", []))
