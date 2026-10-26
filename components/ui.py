import re
from typing import Optional
import streamlit as st
from core.config import DANGER_KEYWORDS, SAFETY_KEYWORDS


# ─── MASTER CSS ──────────────────────────────────────────────────────────────────
def inject_custom_css() -> None:
    """Injecte le système de design complet : typographie, glassmorphism, animations, IHM."""
    # JS : détecte le thème Streamlit (localStorage + data-theme) et pose data-gc-theme sur <html>
    st.markdown("""<script>
    (function(){
        function applyGcTheme(){
            var light=false;
            try{
                var raw=localStorage.getItem('stActiveTheme');
                if(raw){var t=JSON.parse(raw);light=(t.base==='light');}
                else{
                    var el=document.querySelector('[data-theme]');
                    if(el){light=el.getAttribute('data-theme')==='light';}
                    else{light=window.matchMedia('(prefers-color-scheme:light)').matches;}
                }
            }catch(e){}
            document.documentElement.setAttribute('data-gc-theme',light?'light':'dark');
        }
        applyGcTheme();
        setTimeout(applyGcTheme,150);
        setTimeout(applyGcTheme,600);
        new MutationObserver(applyGcTheme).observe(document.documentElement,
            {attributes:true,subtree:true,attributeFilter:['data-theme','class']});
    })();
    </script>""", unsafe_allow_html=True)
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── TOKENS ────────────────────────────────────────────────────────
       Les tokens principaux (--bg, --surface, --text, --primary) mappent
       aux variables CSS natives de Streamlit → le switch Sombre/Clair
       fonctionne automatiquement dans toutes les versions Streamlit.
    ────────────────────────────────────────────────────────────────── */
    :root {
        /* === Mappés aux vars Streamlit (se mettent à jour avec le thème) === */
        --bg:      var(--background-color, #060b17);
        --surface: var(--secondary-background-color, #0f1624);
        --text:    var(--text-color, #e2e8f0);
        --primary: var(--primary-color, #4f8ef7);
        /* === Tokens étendus — dark par défaut === */
        --bg-grid:      radial-gradient(ellipse at 20% 50%, rgba(79,142,247,0.04) 0%, transparent 60%),
                        radial-gradient(ellipse at 80% 20%, rgba(99,102,241,0.04) 0%, transparent 60%);
        --surface-2:    #161f33;
        --surface-3:    #1e2a44;
        --surface-glass:rgba(15,22,36,0.75);
        --border:       rgba(255,255,255,0.06);
        --border-hi:    rgba(79,142,247,0.45);
        --border-glow:  rgba(79,142,247,0.2);
        --primary-dark: #2563eb;
        --primary-glow: rgba(79,142,247,0.22);
        --indigo:       #6366f1;
        --indigo-glow:  rgba(99,102,241,0.2);
        --cyan:         #06b6d4;
        --danger:       #ef4444;
        --danger-glow:  rgba(239,68,68,0.18);
        --danger-bg:    rgba(239,68,68,0.08);
        --warning:      #f59e0b;
        --warning-glow: rgba(245,158,11,0.18);
        --warning-bg:   rgba(245,158,11,0.08);
        --success:      #10b981;
        --success-glow: rgba(16,185,129,0.18);
        --success-bg:   rgba(16,185,129,0.08);
        --info:         #3b82f6;
        --text-dim:     #64748b;
        --text-muted:   #475569;
        --text-body:    #cbd5e1;
        --radius-sm:  10px;
        --radius-md:  14px;
        --radius-lg:  20px;
        --radius-xl:  28px;
        --shadow:     0 4px 20px rgba(0,0,0,0.45);
        --shadow-lg:  0 12px 40px rgba(0,0,0,0.55);
        --shadow-xl:  0 24px 60px rgba(0,0,0,0.6);
        --glow-primary: 0 0 28px var(--primary-glow);
        /* Tokens adaptatifs au thème */
        --track-bg:        rgba(255,255,255,0.05);
        --card-subtle-bg:  rgba(255,255,255,0.02);
        --card-subtle-brd: rgba(255,255,255,0.05);
    }

    /* ── TOKENS LIGHT ────────────────────────────────────────────────── */
    /* Sélecteurs multiples : couvre toutes les versions Streamlit + le JS detector */
    html[data-theme="light"],
    [data-theme="light"],
    html[data-gc-theme="light"],
    [data-gc-theme="light"] {
        --bg-grid:      radial-gradient(ellipse at 20% 50%, rgba(79,142,247,0.06) 0%, transparent 60%),
                        radial-gradient(ellipse at 80% 20%, rgba(99,102,241,0.06) 0%, transparent 60%);
        --surface-2:    #f1f5fb;
        --surface-3:    #e2eaf8;
        --surface-glass:rgba(255,255,255,0.85);
        --border:       rgba(0,0,0,0.08);
        --border-hi:    rgba(37,99,235,0.45);
        --border-glow:  rgba(37,99,235,0.15);
        --primary-dark: #1d4ed8;
        --primary-glow: rgba(37,99,235,0.18);
        --indigo:       #4f46e5;
        --indigo-glow:  rgba(79,70,229,0.15);
        --cyan:         #0891b2;
        --danger:       #dc2626;
        --danger-glow:  rgba(220,38,38,0.15);
        --danger-bg:    rgba(220,38,38,0.06);
        --warning:      #d97706;
        --warning-glow: rgba(217,119,6,0.15);
        --warning-bg:   rgba(217,119,6,0.06);
        --success:      #059669;
        --success-glow: rgba(5,150,105,0.15);
        --success-bg:   rgba(5,150,105,0.06);
        --info:         #2563eb;
        --text-dim:     #64748b;
        --text-muted:   #94a3b8;
        --text-body:    #374151;
        --shadow:     0 4px 20px rgba(0,0,0,0.08);
        --shadow-lg:  0 12px 40px rgba(0,0,0,0.12);
        --shadow-xl:  0 24px 60px rgba(0,0,0,0.15);
        --glow-primary: 0 0 28px var(--primary-glow);
        --track-bg:        rgba(0,0,0,0.06);
        --card-subtle-bg:  rgba(0,0,0,0.02);
        --card-subtle-brd: rgba(0,0,0,0.07);
    }

    /* ── RESET & BASE ────────────────────────────────────────────────── */
    html, body, .stApp {
        background-color: var(--bg) !important;
        background-image: var(--bg-grid) !important;
        font-family: 'Inter', system-ui, sans-serif;
        color: var(--text);
        -webkit-font-smoothing: antialiased;
    }
    [data-theme="light"] .stApp,
    [data-theme="light"] body,
    [data-gc-theme="light"] .stApp,
    [data-gc-theme="light"] body {
        background-color: var(--bg) !important;
        background-image: var(--bg-grid) !important;
        color: var(--text) !important;
    }
    h1,h2,h3,h4 { font-family: 'Space Grotesk', sans-serif; color: var(--text); letter-spacing: -0.02em; }
    code, pre { font-family: 'JetBrains Mono', monospace !important; }
    /* Hide only unwanted Streamlit chrome — keep toolbar/Settings visible */
    footer { visibility: hidden; }
    [data-testid="stDecoration"]  { display: none !important; }
    [data-testid="stDeployButton"] { display: none !important; }
    .stDeployButton { display: none !important; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--surface); }
    ::-webkit-scrollbar-thumb { background: var(--surface-3); border-radius: 99px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--primary); }

    /* Block container padding */
    .main .block-container {
        padding: 2rem 2.5rem 3rem 2.5rem !important;
        max-width: 1400px;
    }

    /* ── SIDEBAR ─────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0e1a 0%, #101627 100%) !important;
        border-right: 1px solid var(--border) !important;
        width: 270px !important;
    }
    [data-theme="light"] section[data-testid="stSidebar"],
    [data-gc-theme="light"] section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e8eef8 0%, #f1f5fb 100%) !important;
        border-right: 1px solid rgba(0,0,0,0.08) !important;
    }

    section[data-testid="stSidebar"] > div { padding: 0 !important; }

    /* ── LOGO BLOCK ──────────────────────────────────────────────────── */
    .sidebar-logo {
        padding: 30px 22px 20px 22px;
        border-bottom: 1px solid var(--border);
        text-align: center;
        position: relative;
    }
    .sidebar-logo::after {
        content: ''; position: absolute;
        bottom: 0; left: 20%; right: 20%; height: 1px;
        background: linear-gradient(90deg, transparent, var(--primary-glow), transparent);
    }
    .logo-icon {
        font-size: 2.6rem; display: block; margin-bottom: 8px;
        filter: drop-shadow(0 0 18px var(--primary-glow));
        animation: float-icon 4s ease-in-out infinite;
    }
    @keyframes float-icon {
        0%, 100% { transform: translateY(0px); }
        50%       { transform: translateY(-4px); }
    }
    .logo-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.1rem; font-weight: 700;
        color: var(--text); letter-spacing: 0.5px;
    }
    .logo-sub {
        font-size: 0.62rem; color: var(--primary); font-weight: 600;
        text-transform: uppercase; letter-spacing: 2.5px; margin-top: 3px;
    }
    .logo-version {
        display: inline-block; margin-top: 8px;
        background: rgba(79,142,247,0.12);
        border: 1px solid rgba(79,142,247,0.25); border-radius: 99px;
        font-size: 0.62rem; color: var(--primary);
        padding: 2px 10px; font-weight: 600;
    }

    /* ── NAV ITEMS ───────────────────────────────────────────────────── */
    .nav-section-label {
        font-size: 0.62rem;
        font-weight: 700;
        color: var(--text-dim);
        text-transform: uppercase;
        letter-spacing: 2px;
        padding: 18px 22px 6px 22px;
    }
    .nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 11px 22px;
        margin: 2px 12px;
        border-radius: var(--radius-md);
        cursor: pointer;
        font-size: 0.9rem;
        font-weight: 500;
        color: var(--text-dim);
        border: 1px solid transparent;
        text-decoration: none !important;
        transition: all 0.2s ease;
        user-select: none;
    }
    .nav-item:hover {
        background: rgba(79,142,247,0.08);
        color: var(--text);
        border-color: var(--border);
    }
    .nav-item.active {
        background: linear-gradient(135deg, rgba(79,142,247,0.2), rgba(99,102,241,0.15));
        color: #fff;
        border-color: var(--border-hi);
        box-shadow: 0 2px 12px var(--primary-glow);
    }
    .nav-item.active .nav-icon { filter: drop-shadow(0 0 6px var(--primary)); }
    .nav-badge {
        margin-left: auto;
        background: var(--danger);
        color: #fff;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 99px;
    }
    .nav-badge-ok {
        margin-left: auto;
        background: var(--success);
        color: #fff;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 99px;
    }

    /* ── SIDEBAR STATUS BOX ──────────────────────────────────────────── */
    .sidebar-status {
        margin: 14px 14px; padding: 16px 18px;
        background: rgba(79,142,247,0.07);
        border: 1px solid rgba(79,142,247,0.15);
        border-radius: var(--radius-md);
        backdrop-filter: blur(4px);
    }
    .status-dot {
        display: inline-block; width: 8px; height: 8px;
        border-radius: 50%; background: var(--success);
        box-shadow: 0 0 10px var(--success); margin-right: 7px;
        animation: pulse-dot 2.2s ease-in-out infinite;
    }
    @keyframes pulse-dot {
        0%, 100% { box-shadow: 0 0 6px var(--success); opacity: 1; }
        50%       { box-shadow: 0 0 18px var(--success); opacity: 0.7; }
    }
    .sidebar-status p { margin: 5px 0; font-size: 0.78rem; color: var(--text-dim); }
    .status-title { font-weight: 700; color: var(--text); font-size: 0.84rem; }

    /* ── SIDEBAR FOOTER ──────────────────────────────────────────────── */
    .sidebar-footer {
        padding: 14px 22px;
        border-top: 1px solid var(--border);
        text-align: center;
        margin-top: 12px;
    }
    .sidebar-footer span { font-size: 0.7rem; color: var(--text-dim); }

    /* ── PAGE HEADER ─────────────────────────────────────────────────── */
    .page-header {
        padding: 0 0 28px 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 32px;
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
    }
    .page-header-left .page-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text);
        margin: 0 0 4px 0;
    }
    .page-header-left .page-subtitle {
        font-size: 0.88rem;
        color: var(--text-dim);
        margin: 0;
    }
    .page-breadcrumb {
        font-size: 0.75rem; color: var(--text-dim);
        margin-bottom: 6px;
    }
    .page-breadcrumb span { color: var(--primary); }

    /* ── PAGE HEADER ANIMATIONS ─────────────────────────────────────── */
    .page-header { animation: fadeInDown 0.4s ease; }
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-12px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(16px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes scalePop {
        from { opacity: 0; transform: scale(0.85); }
        to   { opacity: 1; transform: scale(1); }
    }
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-10px); }
        to   { opacity: 1; transform: translateX(0); }
    }
    @keyframes grow-bar {
        from { width: 0% !important; }
        to   { width: var(--bar-width); }
    }
    @keyframes shimmer {
        0%   { background-position: -800px 0; }
        100% { background-position:  800px 0; }
    }

    /* ── CARDS ───────────────────────────────────────────────────────── */
    .gc-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 24px 26px;
        margin-bottom: 18px;
        box-shadow: var(--shadow);
        transition: transform 0.28s cubic-bezier(0.34,1.56,0.64,1),
                    box-shadow 0.25s ease, border-color 0.25s ease;
        position: relative; overflow: hidden;
    }
    .gc-card::before {
        content: ''; position: absolute;
        top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(79,142,247,0.15), transparent);
    }
    .gc-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-lg);
        border-color: var(--border-glow);
    }
    .gc-card-title {
        font-size: 0.7rem; font-weight: 700; color: var(--primary);
        text-transform: uppercase; letter-spacing: 1.8px;
        margin-bottom: 14px;
    }

    /* ── KPI CARDS ───────────────────────────────────────────────────── */
    .kpi-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 22px 18px; text-align: center;
        position: relative; overflow: hidden;
        transition: transform 0.25s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.25s ease;
        animation: fadeInUp 0.5s ease both;
    }
    .kpi-card::before {
        content: ''; position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, var(--primary), var(--indigo)); opacity: 0.85;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: var(--shadow-lg), 0 0 0 1px var(--border-glow);
    }
    .kpi-icon  { font-size: 1.6rem; margin-bottom: 10px; display: block; }
    .kpi-value { font-size: 2rem; font-weight: 800; margin: 0; line-height: 1; font-family: 'Space Grotesk', sans-serif; }
    .kpi-label { font-size: 0.68rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1.2px; margin-top: 8px; }
    .kpi-delta { font-size: 0.74rem; font-weight: 600; margin-top: 7px; display: inline-flex; align-items: center; gap: 4px; }
    .kpi-danger::before  { background: linear-gradient(90deg, var(--danger), #ff6b6b); }
    .kpi-success::before { background: linear-gradient(90deg, var(--success), #34d399); }
    .kpi-warning::before { background: linear-gradient(90deg, var(--warning), #fcd34d); }
    .kpi-indigo::before  { background: linear-gradient(90deg, var(--indigo), var(--cyan)); }

    /* ── SECTION HEADERS ─────────────────────────────────────────────── */
    .section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 30px 0 16px 0;
    }
    .section-header .sh-icon {
        width: 34px; height: 34px;
        background: var(--primary-glow);
        border-radius: var(--radius-sm);
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem;
        border: 1px solid rgba(79,142,247,0.3);
    }
    .section-header .sh-text { font-size: 1.1rem; font-weight: 700; color: var(--text); }
    .section-header::after {
        content: ''; flex: 1; height: 1px;
        background: linear-gradient(to right, var(--border), transparent);
    }

    /* ── BADGES ──────────────────────────────────────────────────────── */
    .risk-badge {
        display: inline-flex; align-items: center; gap: 8px;
        padding: 8px 22px; border-radius: 99px;
        font-size: 1rem; font-weight: 700;
        border: 1px solid transparent;
        letter-spacing: 0.3px;
        animation: scalePop 0.35s cubic-bezier(0.34,1.56,0.64,1) both;
    }
    .rb-critique { background: rgba(239,68,68,0.15); color: #f87171; border-color: rgba(239,68,68,0.5); box-shadow: 0 0 20px rgba(239,68,68,0.15); }
    .rb-eleve    { background: rgba(245,158,11,0.15); color: #fbbf24; border-color: rgba(245,158,11,0.5); box-shadow: 0 0 20px rgba(245,158,11,0.15); }
    .rb-moyen    { background: rgba(16,185,129,0.15);  color: #34d399; border-color: rgba(16,185,129,0.5);  box-shadow: 0 0 20px rgba(16,185,129,0.15); }
    .rb-faible   { background: rgba(79,142,247,0.15);  color: #93c5fd; border-color: rgba(79,142,247,0.5);  box-shadow: 0 0 20px rgba(79,142,247,0.15); }

    /* ── ALERT BOXES ─────────────────────────────────────────────────── */
    .alert-box {
        display: flex; align-items: flex-start; gap: 14px;
        padding: 14px 18px;
        border-radius: var(--radius-md);
        margin-bottom: 10px;
        border-left: 3px solid transparent;
        animation: slideInLeft 0.35s ease-out both;
    }
    .alert-danger  { background: var(--danger-bg);  border-left-color: var(--danger);  color: #fca5a5; }
    .alert-warning { background: var(--warning-bg); border-left-color: var(--warning); color: #fcd34d; }
    .alert-ok      { background: var(--success-bg); border-left-color: var(--success); color: #6ee7b7; }
    .alert-info    { background: rgba(59,130,246,0.08); border-left-color: var(--info); color: #93c5fd; }
    .alert-box strong { font-weight: 700; }

    /* ── ANIMATED PROGRESS BARS ─────────────────────────────────────── */
    .progress-wrap { margin-bottom: 14px; }
    .progress-label {
        display: flex; justify-content: space-between;
        font-size: 0.78rem; font-weight: 600; margin-bottom: 6px;
        color: var(--text-dim);
    }
    .progress-label .pct { color: var(--text); font-weight: 700; }
    .progress-track {
        background: var(--track-bg);
        border-radius: 99px; height: 8px; overflow: hidden;
        border: 1px solid var(--border);
    }
    .progress-fill {
        height: 100%; border-radius: 99px;
        animation: grow-bar 1s cubic-bezier(0.4, 0, 0.2, 1) both;
        animation-delay: 0.1s;
    }

    /* ── SKELETON ────────────────────────────────────────────────────── */
    .skel {
        background: linear-gradient(
            90deg,
            var(--card-subtle-bg) 25%,
            var(--track-bg) 50%,
            var(--card-subtle-bg) 75%
        );
        background-size: 800px 100%;
        animation: shimmer 1.8s infinite;
        border-radius: var(--radius-sm);
        margin-bottom: 14px;
    }

    /* ── SIGNAL PILLS ────────────────────────────────────────────────── */
    .signal-pill {
        display: inline-block;
        background: rgba(239,68,68,0.12); color: #f87171;
        border: 1px solid rgba(239,68,68,0.28); border-radius: 99px;
        padding: 3px 13px; font-size: 0.73rem; font-weight: 600;
        margin: 3px 3px; transition: all 0.2s;
    }
    .signal-pill:hover { background: rgba(239,68,68,0.22); transform: translateY(-1px); }

    /* ── FORM INPUTS ─────────────────────────────────────────────────── */
    .stNumberInput input, .stTextInput input, .stTextArea textarea {
        background: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text) !important;
        font-family: 'Inter', sans-serif !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    .stNumberInput input:focus,
    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px var(--primary-glow) !important;
        outline: none !important;
    }
    .stSelectbox > div > div {
        background: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text) !important;
    }

    /* ── BUTTONS ─────────────────────────────────────────────────────── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary) 0%, var(--indigo) 100%) !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 700 !important; font-size: 0.9rem !important;
        letter-spacing: 0.4px; color: #fff !important;
        box-shadow: 0 4px 16px var(--primary-glow) !important;
        padding: 12px 28px !important;
        transition: all 0.22s ease !important;
        position: relative; overflow: hidden;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 28px var(--primary-glow) !important;
        filter: brightness(1.08) !important;
    }
    .stButton > button[kind="primary"]:active { transform: translateY(0) !important; }
    .stButton > button:not([kind="primary"]) {
        background: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text) !important; font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        border-color: var(--primary) !important; color: var(--primary) !important;
        box-shadow: 0 0 0 1px var(--border-glow) !important;
    }
    .stDownloadButton > button {
        background: var(--success-bg) !important;
        border: 1px solid rgba(16,185,129,0.3) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--success) !important; font-weight: 700 !important;
    }
    .stDownloadButton > button:hover {
        background: rgba(16,185,129,0.15) !important;
        border-color: rgba(16,185,129,0.5) !important;
    }

    /* ── PROGRESS BAR ────────────────────────────────────────────────── */
    .stProgress > div > div { border-radius: 99px; }

    /* ── DIVIDER ─────────────────────────────────────────────────────── */
    hr { border-color: var(--border) !important; margin: 24px 0 !important; }

    /* ── DATA TABLE ──────────────────────────────────────────────────── */
    .stDataFrame { border-radius: var(--radius-md); overflow: hidden; border: 1px solid var(--border) !important; }
    .stDataFrame table { background: var(--surface); }
    .stDataFrame thead tr th {
        background: var(--surface-3) !important; color: var(--text-dim) !important;
        font-size: 0.72rem !important; text-transform: uppercase;
        letter-spacing: 1.2px; font-weight: 700 !important; padding: 12px 16px !important;
    }
    .stDataFrame tbody tr:hover td { background: rgba(79,142,247,0.05) !important; }

    /* ── EXPANDER ────────────────────────────────────────────────────── */
    .streamlit-expanderHeader {
        background: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
    }

    /* ── TABS ────────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--surface) !important;
        border-radius: var(--radius-md) !important;
        padding: 6px !important;
        border: 1px solid var(--border);
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-sm) !important;
        color: var(--text-dim) !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 8px 20px !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary), var(--indigo)) !important;
        color: #fff !important;
        box-shadow: 0 2px 10px var(--primary-glow) !important;
    }

    /* ── SPINNER ─────────────────────────────────────────────────────── */
    .stSpinner > div { border-top-color: var(--primary) !important; }

    /* ── TOOLTIPS on labels ─────────────────────────────────────────── */
    .stSlider p, .stNumberInput label, .stSelectbox label, .stTextArea label { 
        color: var(--text-dim) !important; font-size: 0.85rem !important; font-weight: 500 !important;
    }

    /* ── SUCCESS/ERROR/INFO/WARNING native ──────────────────────────── */
    .stAlert { border-radius: var(--radius-md) !important; }

    /* ── RADIO ───────────────────────────────────────────────────────── */
    .stRadio > div { gap: 8px; }
    .stRadio > div > label {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        padding: 10px 18px !important;
        transition: all 0.2s;
    }
    .stRadio > div > label:hover { border-color: var(--primary) !important; }

    /* ── METRIC (Streamlit native) ───────────────────────────────────── */
    [data-testid="stMetric"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        padding: 16px 20px !important;
        transition: all 0.2s !important;
    }
    [data-testid="stMetric"]:hover { border-color: var(--border-glow) !important; }
    [data-testid="stMetricValue"] {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.7rem !important; font-weight: 800 !important;
    }

    /* ── FILE UPLOADER ───────────────────────────────────────────────── */
    [data-testid="stFileUploader"] {
        border: 2px dashed rgba(79,142,247,0.25) !important;
        border-radius: var(--radius-md) !important;
        background: rgba(79,142,247,0.04) !important;
        padding: 16px !important; transition: all 0.2s !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(79,142,247,0.5) !important;
        background: rgba(79,142,247,0.08) !important;
    }

    /* ── TOAST ───────────────────────────────────────────────────────── */
    [data-testid="stToast"] {
        background: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        box-shadow: var(--shadow-lg) !important;
        color: var(--text) !important; font-weight: 600 !important;
    }

    /* ── TABS upgrade ────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-sm) !important;
        color: var(--text-dim) !important;
        font-weight: 600 !important; font-size: 0.86rem !important;
        padding: 9px 22px !important;
        background: transparent !important;
        transition: all 0.2s !important;
    }
    .stTabs [data-baseweb="tab"]:hover { color: var(--text) !important; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 24px !important; }

    /* ── GRADIENT TEXT UTILITY ───────────────────────────────────────── */
    .gradient-text {
        background: linear-gradient(135deg, var(--primary), var(--indigo));
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    </style>
    """, unsafe_allow_html=True)


# ─── SIDEBAR ────────────────────────────────────────────────────────────────────────────────
def render_sidebar(pages: list, active_page: str) -> str:
    """Render la sidebar premium avec navigation, statut IA et métriques système."""
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
            <span class="logo-icon">🏗️</span>
            <div class="logo-title">GC SAFETY AI</div>
            <div class="logo-sub">Risk Intelligence Platform</div>
            <span class="logo-version">v3.0 Enterprise</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="nav-section-label">Navigation Principale</div>',
                    unsafe_allow_html=True)

        selected = st.radio(
            "nav",
            pages,
            index=pages.index(active_page) if active_page in pages else 0,
            label_visibility="collapsed",
        )

        st.markdown('<div class="nav-section-label" style="padding-top:22px;">Statut Système</div>',
                    unsafe_allow_html=True)

        st.markdown("""
        <div class="sidebar-status">
            <div style="margin-bottom:10px;display:flex;align-items:center;">
                <span class="status-dot"></span>
                <span class="status-title">Système Opérationnel</span>
            </div>
            <p>🤖 Modèle : <strong style="color:var(--text);">MLP v2</strong></p>
            <p>🎯 F1-Score : <strong style="color:#10b981;">88.84 %</strong></p>
            <p>📦 Dataset : <strong style="color:var(--text);">2 400+ chantiers</strong></p>
            <p>⚡ Prédiction : <strong style="color:#10b981;">&lt; 200 ms</strong></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="sidebar-footer">
            <span>© 2026 ISET Génie Civil &nbsp;·&nbsp; v3.0.0</span>
        </div>
        """, unsafe_allow_html=True)

    return selected


# ─── PAGE HEADER ─────────────────────────────────────────────────────────────────
def page_header(title: str, subtitle: str, icon: str, crumb: str = "Accueil",
               badge: Optional[str] = None) -> None:
    """Affiche un en-tête de page premium avec breadcrumb et badge optionnel."""
    badge_html = (
        f'<span style="display:inline-flex;align-items:center;gap:6px;margin-top:8px;'
        f'padding:4px 14px;background:rgba(79,142,247,0.12);border:1px solid rgba(79,142,247,0.28);'
        f'border-radius:99px;font-size:0.7rem;color:#4f8ef7;font-weight:700;letter-spacing:0.5px;">'
        f'⚡ {badge}</span>'
    ) if badge else ""
    st.markdown(f"""
    <div class="page-header">
        <div class="page-header-left">
            <div class="page-breadcrumb">GC Safety AI &rsaquo; <span>{crumb}</span></div>
            <h1 class="page-title">{icon}&nbsp; {title}</h1>
            <p class="page-subtitle">{subtitle}</p>
            {badge_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── SECTION TITLE ────────────────────────────────────────────────────────────────
def section_title(title: str, icon: str = "") -> None:
    """Titre de section avec icône encadrée."""
    st.markdown(f"""
    <div class="section-header">
        <div class="sh-icon">{icon}</div>
        <span class="sh-text">{title}</span>
    </div>
    """, unsafe_allow_html=True)


# ─── KPI / METRIC CARD ───────────────────────────────────────────────────────────────────────
def dashboard_metric(
    label: str,
    value: str,
    color: str = "#4f8ef7",
    icon: str = "",
    delta: Optional[str] = None,
    variant: str = "",
) -> None:
    """Carte KPI premium glassmorphism avec icône, valeur et delta optionnel."""
    variant_cls = f"kpi-{variant}" if variant else ""
    delta_html = ""
    if delta:
        trend_color = "#10b981" if delta.startswith("+") else "#ef4444"
        arrow = "↑" if delta.startswith("+") else "↓"
        delta_html = f'<div class="kpi-delta" style="color:{trend_color};">{arrow} {delta}</div>'
    icon_html = f'<span class="kpi-icon">{icon}</span>' if icon else ""
    st.markdown(f"""
    <div class="kpi-card {variant_cls}">
        {icon_html}
        <div class="kpi-value" style="color:{color};">{value}</div>
        <div class="kpi-label">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


# ─── RISK BADGE ──────────────────────────────────────────────────────────────────
def risk_badge(label: str) -> None:
    """Badge niveau de risque coloré et lumineux."""
    cls_map = {
        "Critique": "rb-critique", "Élevé": "rb-eleve",
        "Moyen": "rb-moyen",       "Faible": "rb-faible",
    }
    icon_map = {
        "Critique": "🚨", "Élevé": "⚠️", "Moyen": "⚖️", "Faible": "✅",
    }
    cls  = cls_map.get(label, "rb-moyen")
    icon = icon_map.get(label, "🔹")
    st.markdown(
        f'<span class="risk-badge {cls}">{icon}&nbsp;Risque {label}</span>',
        unsafe_allow_html=True
    )


# ─── RISK RESULT CARD ────────────────────────────────────────────────────────────
def risk_result_card(label: str, conf: float) -> None:
    """Grande carte de résultat avec animation scalePop et barre grow-bar."""
    color_map = {
        "Critique": ("#ef4444", "rgba(239,68,68,0.12)", "rgba(239,68,68,0.38)"),
        "Élevé":    ("#f59e0b", "rgba(245,158,11,0.12)", "rgba(245,158,11,0.38)"),
        "Moyen":    ("#10b981", "rgba(16,185,129,0.12)", "rgba(16,185,129,0.38)"),
        "Faible":   ("#4f8ef7", "rgba(79,142,247,0.12)", "rgba(79,142,247,0.38)"),
    }
    icon_map = {"Critique": "🚨", "Élevé": "⚠️", "Moyen": "⚖️", "Faible": "✅"}
    desc_map = {
        "Critique": "Arrêt immédiat requis — Risques majeurs identifiés.",
        "Élevé":    "Surveillance renforcée obligatoire — Actions correctives urgentes.",
        "Moyen":    "Précautions additionnelles conseillées — Surveillance standard.",
        "Faible":   "Conditions satisfaisantes — Conformité vérifiée.",
    }
    text_col, bg, brd = color_map.get(label, ("#4f8ef7", "rgba(79,142,247,0.12)", "rgba(79,142,247,0.38)"))
    icon = icon_map.get(label, "🔹")
    desc = desc_map.get(label, "")
    bar_w = int(conf * 100)

    st.markdown(f"""
    <div style="background:{bg};border:1px solid {brd};border-radius:20px;padding:32px 28px;
         text-align:center;box-shadow:0 8px 32px rgba(0,0,0,0.3),0 0 0 1px {brd};
         animation:scalePop 0.4s cubic-bezier(0.34,1.56,0.64,1) both;">
        <div style="font-size:3rem;margin-bottom:10px;filter:drop-shadow(0 0 12px {brd});">{icon}</div>
        <div style="font-size:0.68rem;color:var(--text-dim);font-weight:700;text-transform:uppercase;
             letter-spacing:2.5px;margin-bottom:8px;">Niveau de Risque Prédit</div>
        <div style="font-size:2.4rem;font-weight:800;color:{text_col};
             font-family:'Space Grotesk',sans-serif;margin-bottom:6px;
             text-shadow:0 0 24px {brd};">{label}</div>
        <div style="font-size:0.82rem;color:var(--text-muted);margin-bottom:20px;font-style:italic;">{desc}</div>
        <div style="background:var(--track-bg);border-radius:99px;height:10px;
             overflow:hidden;margin-bottom:12px;border:1px solid var(--card-subtle-brd);">
            <div style="background:linear-gradient(90deg,{text_col}88,{text_col});
                 width:{bar_w}%;height:100%;border-radius:99px;
                 box-shadow:0 0 10px {brd};
                 animation:grow-bar 1s cubic-bezier(0.4,0,0.2,1) both;"></div>
        </div>
        <div style="font-size:0.88rem;color:{text_col};font-weight:800;
             letter-spacing:0.5px;">Confiance : {conf:.1%}</div>
    </div>
    """, unsafe_allow_html=True)


# ─── HIGHLIGHTED REPORT ──────────────────────────────────────────────────────────
def highlighted_report(text: str) -> None:
    """Affiche le rapport avec mise en évidence sémantique des mots-clés."""
    if not text or not text.strip():
        st.markdown("""
        <div style="background:var(--card-subtle-bg); border:1px dashed var(--card-subtle-brd); border-radius:12px; padding:24px; text-align:center; color:var(--text-muted); font-size:0.9rem;">
            📄 Aucun rapport d'inspection renseigné.
        </div>
        """, unsafe_allow_html=True)
        return

    highlighted = text
    for kw in sorted(DANGER_KEYWORDS, key=len, reverse=True):
        pat = re.compile(re.escape(kw), re.IGNORECASE)
        highlighted = pat.sub(
            lambda m: (
                f"<mark style='background:rgba(239,68,68,0.25);color:#fca5a5;"
                f"border-radius:4px;padding:1px 5px;font-weight:700;"
                f"border-bottom:2px solid rgba(239,68,68,0.5);'>{m.group()}</mark>"
            ),
            highlighted,
        )
    for kw in sorted(SAFETY_KEYWORDS, key=len, reverse=True):
        pat = re.compile(re.escape(kw), re.IGNORECASE)
        highlighted = pat.sub(
            lambda m: (
                f"<mark style='background:rgba(16,185,129,0.2);color:#6ee7b7;"
                f"border-radius:4px;padding:1px 5px;font-weight:700;"
                f"border-bottom:2px solid rgba(16,185,129,0.4);'>{m.group()}</mark>"
            ),
            highlighted,
        )

    st.markdown(f"""
    <div style="background:var(--card-subtle-bg); padding:22px 26px; border-radius:14px;
         border:1px solid var(--card-subtle-brd); line-height:1.9; font-size:0.91rem; color:var(--text-body);">
        {highlighted}
    </div>
    <div style="margin-top:10px;font-size:0.72rem;color:var(--text-muted);display:flex;gap:16px;">
        <span><mark style='background:rgba(239,68,68,0.2);color:#fca5a5;border-radius:3px;
              padding:0 5px;font-weight:700;'>mot</mark>&nbsp;Danger</span>
        <span><mark style='background:rgba(16,185,129,0.15);color:#6ee7b7;border-radius:3px;
              padding:0 5px;font-weight:700;'>mot</mark>&nbsp;Conformité</span>
    </div>
    """, unsafe_allow_html=True)


# ─── GC SIGNAL PILLS ─────────────────────────────────────────────────────────────
def gc_signal_pills(active_signals: list) -> None:
    """Affiche les signaux GC actifs sous forme de chips colorés."""
    if not active_signals:
        st.markdown(
            "<p style='color:#10b981;font-size:0.86rem;margin:6px 0;'>✅ Aucun signal de danger détecté dans le rapport</p>",
            unsafe_allow_html=True)
        return
    pills = " ".join(
        f"<span class='signal-pill'>⚡ {s.replace('_', ' ').title()}</span>"
        for s in active_signals[:14]
    )
    st.markdown(f"<div style='line-height:2.2;'>{pills}</div>", unsafe_allow_html=True)


# ─── SKELETON LOADER ─────────────────────────────────────────────────────────────
def skeleton_loader(lines: int = 4) -> None:
    """Chargeur skeleton animé (CSS injecté via inject_custom_css)."""
    heights = [32, 160, 20, 20, 120]
    widths  = ["45%", "100%", "65%", "55%", "100%"]
    html = ""
    for i in range(min(lines, len(heights))):
        html += f'<div class="skel" style="height:{heights[i]}px;width:{widths[i]};"></div>'
    st.markdown(html, unsafe_allow_html=True)


# ─── INLINE ALERT ───────────────────────────────────────────────────────────────────────────
def inline_alert(message: str, level: str = "warning") -> None:
    """Alerte inline stylisée (danger / warning / ok / info)."""
    css = {"danger": "alert-danger", "warning": "alert-warning",
           "ok": "alert-ok", "info": "alert-info"}.get(level, "alert-info")
    st.markdown(
        f'<div class="alert-box {css}"><div>{message}</div></div>',
        unsafe_allow_html=True)


# ─── ANIMATED PROBABILITY BARS ─────────────────────────────────────────────────────
def animated_prob_bars(proba: list, class_names: list) -> None:
    """Barres de probabilité animées avec gradient de couleur."""
    color_map = {
        "Critique": ("var(--danger)",  "rgba(239,68,68,0.5)"),
        "Élevé":    ("var(--warning)", "rgba(245,158,11,0.5)"),
        "Moyen":    ("var(--success)", "rgba(16,185,129,0.5)"),
        "Faible":   ("var(--primary)", "rgba(79,142,247,0.5)"),
    }
    bars_html = ""
    for name, pct in zip(class_names, proba):
        c1, c2 = color_map.get(name, ("var(--primary)", "rgba(79,142,247,0.5)"))
        width = f"{pct*100:.1f}%"
        bars_html += f"""
        <div class="progress-wrap">
            <div class="progress-label">
                <span>{name}</span>
                <span class="pct">{pct:.1%}</span>
            </div>
            <div class="progress-track">
                <div class="progress-fill"
                     style="background:linear-gradient(90deg,{c1},{c2});width:{width};--bar-width:{width};">
                </div>
            </div>
        </div>"""
    st.markdown(bars_html, unsafe_allow_html=True)


# ─── SCORE BREAKDOWN CARD ─────────────────────────────────────────────────────────────────
def score_breakdown_card(
    vent: float, temp: float, epi: int,
    effectif: int, risque_hist: float, score: float
) -> None:
    """Carte de décomposition du score de risque composite."""
    items = [
        ("💨 Vent", f"{vent:.0f} km/h",
         min(1.0, vent / 120), "#ef4444" if vent > 80 else "#f59e0b" if vent > 45 else "#10b981"),
        ("🌡️ Température", f"{temp:.1f} °C",
         max(0.0, min(1.0, abs(temp - 22) / 30)),
         "#f59e0b" if temp < 5 or temp > 35 else "#10b981"),
        ("🦺 EPI Manquants", str(epi),
         min(1.0, epi / 10), "#ef4444" if epi >= 5 else "#f59e0b" if epi > 0 else "#10b981"),
        ("👷 Effectif", str(effectif),
         min(1.0, effectif / 100), "#f59e0b" if effectif > 30 else "#10b981"),
        ("📈 Risque Hist.", f"{risque_hist:.0%}",
         risque_hist, "#ef4444" if risque_hist > 0.7 else "#f59e0b" if risque_hist > 0.4 else "#10b981"),
    ]
    score_color = "#ef4444" if score > 0.7 else "#f59e0b" if score > 0.4 else "#10b981"
    rows = ""
    for name, val, pct, col in items:
        w = f"{pct*100:.0f}%"
        rows += f"""
        <div style="margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;font-size:0.8rem;
                 font-weight:600;color:var(--text-muted);margin-bottom:5px;">
                <span>{name}</span>
                <span style="color:var(--text);">{val}</span>
            </div>
            <div style="background:var(--track-bg);border-radius:99px;height:6px;overflow:hidden;">
                <div style="background:{col};width:{w};height:100%;border-radius:99px;
                     animation:grow-bar 0.9s cubic-bezier(0.4,0,0.2,1) both;"></div>
            </div>
        </div>"""
    st.markdown(f"""
    <div class="gc-card">
        <div class="gc-card-title">📊 Décomposition du Score de Risque</div>
        {rows}
        <div style="border-top:1px solid var(--card-subtle-brd);margin-top:10px;padding-top:12px;
             display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:0.78rem;font-weight:700;color:var(--text-dim);text-transform:uppercase;
                  letter-spacing:1px;">Score Composite</span>
            <span style="font-size:1.5rem;font-weight:800;color:{score_color};
                  font-family:'Space Grotesk',sans-serif;">{score:.0%}</span>
        </div>
    </div>""", unsafe_allow_html=True)


# ─── INPUT VALIDATION BADGE ───────────────────────────────────────────────────────────
def input_validation_badge(vent: float, temp: float, epi: int, effectif: int) -> None:
    """Affiche des avertissements de validation temps-réel des inputs."""
    warnings_list = []
    if vent > 80:
        warnings_list.append(("⛔ Vent > 80 km/h : grutage impossible (Art. R4534-58)", "danger"))
    elif vent > 45:
        warnings_list.append(("⚠️ Vent > 45 km/h : surveillance travaux en hauteur", "warning"))
    if temp < 5:
        warnings_list.append(("🌡️ Température < 5 °C : risque de gel du béton", "warning"))
    elif temp > 35:
        warnings_list.append(("🌡️ Température > 35 °C : risque de stress thermique", "warning"))
    if epi >= 5:
        warnings_list.append(("🦺 5 EPI+ manquants : non-conformité CRITIQUE (Code Travail R4321-4)", "danger"))
    if effectif > 30:
        warnings_list.append(("👷 Effectif > 30 : coordinateur SPS requis", "warning"))
    for msg, level in warnings_list:
        inline_alert(msg, level)
