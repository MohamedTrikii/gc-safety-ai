"""
GC Safety AI — Générateur de présentation PowerPoint professionnelle
Exécuter : python generate_presentation.py
Sortie   : GC_Safety_AI_Presentation.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Cm
import pptx.oxml.ns as ns
from lxml import etree
import copy, io, os, sys

# ─── PALETTE COULEURS ────────────────────────────────────────────────────────
C_BG_DARK    = RGBColor(0x0A, 0x10, 0x1E)   # fond principal
C_BG_CARD    = RGBColor(0x0F, 0x16, 0x24)   # fond carte
C_BLUE       = RGBColor(0x4F, 0x8E, 0xF7)   # bleu accent
C_GREEN      = RGBColor(0x10, 0xB9, 0x81)   # vert succès
C_ORANGE     = RGBColor(0xE6, 0x51, 0x00)   # orange alerte
C_RED        = RGBColor(0xEF, 0x44, 0x44)   # rouge critique
C_YELLOW     = RGBColor(0xF5, 0x9E, 0x0B)   # jaune moyen
C_WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
C_LIGHT_GRAY = RGBColor(0x94, 0xA3, 0xB8)   # texte secondaire
C_ACCENT     = RGBColor(0x63, 0x66, 0xF1)   # indigo accent
C_BORDER     = RGBColor(0x1E, 0x2A, 0x45)   # bordure subtle

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

# ─── HELPER — Présentation base ─────────────────────────────────────────────
def new_prs():
    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H
    return prs

def blank_layout(prs):
    return prs.slide_layouts[6]  # complètement vide

# ─── HELPER — Fond dégradé simulé (rectangle plein) ─────────────────────────
def fill_bg(slide, color=None):
    """Rectangle plein couvrant tout le slide comme fond."""
    if color is None:
        color = C_BG_DARK
    bg = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        Inches(0), Inches(0), SLIDE_W, SLIDE_H
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background()
    # Remettre en arrière-plan
    sp = bg._element
    sp.getparent().remove(sp)
    slide.shapes._spTree.insert(2, sp)

def add_rect(slide, x, y, w, h, fill_color, line_color=None, alpha_sim=False):
    """Ajoute un rectangle coloré."""
    shp = slide.shapes.add_shape(1, x, y, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill_color
    if line_color:
        shp.line.color.rgb = line_color
        shp.line.width = Pt(1)
    else:
        shp.line.fill.background()
    return shp

def add_text_box(slide, text, x, y, w, h,
                 font_size=18, bold=False, italic=False,
                 color=None, align=PP_ALIGN.LEFT,
                 font_name="Calibri", wrap=True):
    """Ajoute une zone de texte."""
    if color is None:
        color = C_WHITE
    txb = slide.shapes.add_textbox(x, y, w, h)
    txb.word_wrap = wrap
    tf  = txb.text_frame
    tf.word_wrap = wrap
    p   = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    f = run.font
    f.size  = Pt(font_size)
    f.bold  = bold
    f.italic = italic
    f.color.rgb = color
    f.name  = font_name
    return txb

def add_para(tf, text, font_size=13, bold=False, color=None,
             align=PP_ALIGN.LEFT, space_before=None, italic=False, font_name="Calibri"):
    if color is None:
        color = C_WHITE
    p = tf.add_paragraph()
    p.alignment = align
    if space_before:
        p.space_before = Pt(space_before)
    run = p.add_run()
    run.text = text
    f = run.font
    f.size  = Pt(font_size)
    f.bold  = bold
    f.italic = italic
    f.color.rgb = color
    f.name  = font_name
    return p

def add_separator(slide, y, color=None):
    """Ligne horizontale décorative."""
    if color is None:
        color = C_BLUE
    ln = slide.shapes.add_shape(1, Inches(0.5), y, Inches(12.33), Pt(2))
    ln.fill.solid()
    ln.fill.fore_color.rgb = color
    ln.line.fill.background()

def add_badge(slide, text, x, y, bg_color, text_color=None):
    """Badge coloré avec texte."""
    if text_color is None:
        text_color = C_WHITE
    w = Inches(1.8)
    h = Inches(0.32)
    r = add_rect(slide, x, y, w, h, bg_color)
    add_text_box(slide, text, x, y, w, h,
                 font_size=9, bold=True, color=text_color,
                 align=PP_ALIGN.CENTER)

def add_header_bar(slide, title, subtitle=None, icon="", badge_text=None, badge_color=None):
    """Barre d'en-tête commune à toutes les slides internes."""
    # Bande de titre
    add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(1.2),
             RGBColor(0x0D, 0x1B, 0x35))

    # Ligne d'accent
    add_rect(slide, Inches(0), Inches(1.18), SLIDE_W, Pt(3), C_BLUE)

    # Icon + Titre
    add_text_box(slide, f"{icon}  {title}",
                 Inches(0.4), Inches(0.1), Inches(9), Inches(0.6),
                 font_size=24, bold=True, color=C_WHITE, font_name="Calibri")

    if subtitle:
        add_text_box(slide, subtitle,
                     Inches(0.4), Inches(0.65), Inches(9), Inches(0.45),
                     font_size=11, color=C_LIGHT_GRAY, font_name="Calibri")

    if badge_text:
        bc = badge_color or C_BLUE
        add_badge(slide, badge_text, Inches(11.1), Inches(0.43), bc)

# ─── SLIDE FACTORY ──────────────────────────────────────────────────────────

def slide_cover(prs):
    """Diapo 1 — Couverture."""
    slide = prs.slides.add_slide(blank_layout(prs))
    fill_bg(slide, C_BG_DARK)

    # Bande gauche accent
    add_rect(slide, Inches(0), Inches(0), Inches(0.08), SLIDE_H, C_BLUE)

    # Bloc central
    add_rect(slide, Inches(1.0), Inches(1.3), Inches(11.33), Inches(4.8),
             RGBColor(0x0D, 0x1B, 0x35), C_BORDER)

    # Titre principal
    add_text_box(slide, "GC Safety AI",
                 Inches(1.4), Inches(1.5), Inches(10.5), Inches(1.2),
                 font_size=52, bold=True, color=C_WHITE,
                 align=PP_ALIGN.LEFT, font_name="Calibri")

    add_text_box(slide, "Prédiction de Risque Chantier par Intelligence Artificielle",
                 Inches(1.4), Inches(2.6), Inches(10.5), Inches(0.7),
                 font_size=20, color=C_BLUE, bold=True,
                 align=PP_ALIGN.LEFT, font_name="Calibri")

    add_separator(slide, Inches(3.35), C_ACCENT)

    add_text_box(slide, "Système hybride ML + NLP · MLP Neural Network · F1-Score 88.84%",
                 Inches(1.4), Inches(3.5), Inches(10.5), Inches(0.45),
                 font_size=13, color=C_LIGHT_GRAY,
                 align=PP_ALIGN.LEFT, font_name="Calibri")

    # Tags
    tags = [("🏗️ Génie Civil", C_GREEN), ("🤖 Machine Learning", C_BLUE),
            ("📊 Streamlit", C_ACCENT), ("⚡ Python 3.10+", C_ORANGE)]
    tx = Inches(1.4)
    for tag, col in tags:
        add_badge(slide, tag, tx, Inches(4.05), col)
        tx += Inches(2.1)

    # Ligne bas
    add_rect(slide, Inches(0), Inches(6.8), SLIDE_W, Inches(0.7),
             RGBColor(0x0D, 0x1B, 0x35))
    add_text_box(slide, "Institut Supérieur des Études Technologiques  ·  Année 2024–2025  ·  Projet de Fin d'Études",
                 Inches(0.5), Inches(6.83), Inches(12.33), Inches(0.45),
                 font_size=10, color=C_LIGHT_GRAY,
                 align=PP_ALIGN.CENTER, font_name="Calibri")


def slide_problematique(prs):
    """Diapo 2 — Problématique."""
    slide = prs.slides.add_slide(blank_layout(prs))
    fill_bg(slide)
    add_header_bar(slide, "Problématique", "Le secteur BTP face au risque accidentel", "⚠️")

    # 3 colonnes de faits
    cols = [
        ("🇹🇳\nContexte\nTunisien",
         "Les accidents du travail dans le BTP figurent parmi les plus fréquents tous secteurs confondus en Tunisie.",
         C_RED),
        ("🔍\nCauses\nIdentifiées",
         "Absence ou non-conformité des EPI · Conditions météo extrêmes · Travail en hauteur · Sur-effectif",
         C_YELLOW),
        ("❌\nProblème\nCentral",
         "Absence d'outil d'aide à la décision en temps réel pour les inspecteurs et chefs de chantier.",
         C_ORANGE),
    ]

    col_w = Inches(3.9)
    for i, (title, body, col) in enumerate(cols):
        cx = Inches(0.4 + i * 4.2)
        cy = Inches(1.4)
        add_rect(slide, cx, cy, col_w, Inches(4.8), RGBColor(0x0F, 0x16, 0x24), col)
        # Accent top
        add_rect(slide, cx, cy, col_w, Pt(4), col)
        # Titre colonne
        add_text_box(slide, title, cx + Inches(0.15), cy + Inches(0.1),
                     col_w - Inches(0.3), Inches(0.8),
                     font_size=13, bold=True, color=col,
                     align=PP_ALIGN.CENTER, font_name="Calibri")
        # Séparateur
        add_rect(slide, cx + Inches(0.3), cy + Inches(0.95),
                 col_w - Inches(0.6), Pt(1), col)
        # Corps
        add_text_box(slide, body,
                     cx + Inches(0.15), cy + Inches(1.05),
                     col_w - Inches(0.3), Inches(3.5),
                     font_size=12, color=C_LIGHT_GRAY,
                     align=PP_ALIGN.LEFT, wrap=True, font_name="Calibri")

    # Pied de slide — solution
    add_rect(slide, Inches(0.4), Inches(6.3), Inches(12.53), Inches(0.7),
             RGBColor(0x0D, 0x2A, 0x4A), C_BLUE)
    add_text_box(slide,
                 "💡  Solution proposée : GC Safety AI — système de prédiction automatique du niveau de risque "
                 "combinant données structurées et rapports textuels d'inspection",
                 Inches(0.55), Inches(6.35), Inches(12.2), Inches(0.55),
                 font_size=11, color=C_WHITE, bold=False,
                 align=PP_ALIGN.LEFT, font_name="Calibri")


def slide_types_travaux(prs):
    """Diapo 3 — Types de travaux & facteurs de risque."""
    slide = prs.slides.add_slide(blank_layout(prs))
    fill_bg(slide)
    add_header_bar(slide, "Types de Travaux & Facteurs de Risque",
                   "Domaines couverts par le système de prédiction", "🏗️")

    rows = [
        ("Travaux en Hauteur",   "Chute de personne / objet",          C_RED),
        ("Grutage & Levage",     "Effondrement, collision",             C_RED),
        ("Excavation / Tranchée","Éboulement, asphyxie",               C_ORANGE),
        ("Démolition",           "Projection, instabilité structurelle",C_ORANGE),
        ("Coffrage / Béton",     "Chute, risque électrique",            C_YELLOW),
        ("VRD",                  "Risque chimique, coupure de réseaux", C_YELLOW),
        ("Charpente / Toiture",  "Chute de hauteur, glissade",         C_YELLOW),
        ("Fondation / Maçonnerie","Effondrement partiel, surcharge",    C_GREEN),
        ("Soudure",              "Brûlures, fumes toxiques",            C_GREEN),
        ("Béton armé",           "Projections, vibrations",             C_GREEN),
    ]

    RH = Inches(0.44)
    sy = Inches(1.35)

    # Entêtes
    add_rect(slide, Inches(0.35), sy, Inches(4.2), RH, RGBColor(0x1A, 0x2A, 0x4A))
    add_text_box(slide, "TYPE DE TRAVAUX", Inches(0.35), sy, Inches(4.2), RH,
                 font_size=10, bold=True, color=C_BLUE, align=PP_ALIGN.CENTER)
    add_rect(slide, Inches(4.65), sy, Inches(5.5), RH, RGBColor(0x1A, 0x2A, 0x4A))
    add_text_box(slide, "RISQUE DOMINANT", Inches(4.65), sy, Inches(5.5), RH,
                 font_size=10, bold=True, color=C_BLUE, align=PP_ALIGN.CENTER)
    add_rect(slide, Inches(10.25), sy, Inches(2.6), RH, RGBColor(0x1A, 0x2A, 0x4A))
    add_text_box(slide, "NIVEAU", Inches(10.25), sy, Inches(2.6), RH,
                 font_size=10, bold=True, color=C_BLUE, align=PP_ALIGN.CENTER)

    level_map = {C_RED: "CRITIQUE", C_ORANGE: "ÉLEVÉ",
                 C_YELLOW: "MOYEN", C_GREEN: "FAIBLE"}

    for i, (trav, risque, col) in enumerate(rows):
        ry = sy + RH + Inches(0.02) + i * (RH + Inches(0.02))
        bg = RGBColor(0x12, 0x1D, 0x32) if i % 2 == 0 else RGBColor(0x0F, 0x16, 0x24)
        add_rect(slide, Inches(0.35), ry, Inches(4.2), RH, bg)
        add_rect(slide, Inches(4.65), ry, Inches(5.5), RH, bg)
        add_rect(slide, Inches(10.25), ry, Inches(2.6), RH, bg)
        # Indicateur couleur
        add_rect(slide, Inches(0.35), ry, Pt(4), RH, col)

        add_text_box(slide, f"  {trav}", Inches(0.38), ry, Inches(4.1), RH,
                     font_size=11, color=C_WHITE, align=PP_ALIGN.LEFT)
        add_text_box(slide, risque, Inches(4.68), ry, Inches(5.4), RH,
                     font_size=11, color=C_LIGHT_GRAY, align=PP_ALIGN.LEFT)

        niveau_text = level_map.get(col, "MOYEN")
        add_text_box(slide, niveau_text, Inches(10.28), ry, Inches(2.5), RH,
                     font_size=10, bold=True, color=col, align=PP_ALIGN.CENTER)


def slide_variables_risque(prs):
    """Diapo 4 — Variables instrumentées."""
    slide = prs.slides.add_slide(blank_layout(prs))
    fill_bg(slide)
    add_header_bar(slide, "Variables de Risque Instrumentées",
                   "Données structurées + NLP rapport d'inspection", "📡", "5 + NLP", C_BLUE)

    # Tableau variables numériques
    add_text_box(slide, "📊  Variables Structurées",
                 Inches(0.4), Inches(1.35), Inches(7), Inches(0.4),
                 font_size=13, bold=True, color=C_BLUE)

    headers_s = ["Variable", "Seuil Alerte", "Seuil Critique"]
    rows_s = [
        ("💨 Vent (km/h)",        "> 45 km/h",      "> 80 km/h"),
        ("🌡️ Température (°C)",   "< 5°C / > 35°C", "< -10°C / > 45°C"),
        ("🦺 EPI Manquants",      "> 0",             "≥ 5"),
        ("👷 Effectif",           "> 30 personnes",  "—"),
        ("📜 Risque Historique",  "> 0.5",           "> 0.8"),
    ]

    col_widths = [Inches(2.4), Inches(2.0), Inches(2.0)]
    col_starts = [Inches(0.4), Inches(2.9), Inches(4.95)]
    ry = Inches(1.8)
    RH = Inches(0.4)

    # Header row
    for j, (hdr, cw, cs) in enumerate(zip(headers_s, col_widths, col_starts)):
        add_rect(slide, cs, ry, cw, RH, RGBColor(0x1A, 0x2A, 0x4A))
        add_text_box(slide, hdr, cs, ry, cw, RH,
                     font_size=10, bold=True, color=C_BLUE, align=PP_ALIGN.CENTER)

    for i, row_data in enumerate(rows_s):
        ry += RH + Inches(0.02)
        bg = RGBColor(0x12, 0x1D, 0x32) if i % 2 == 0 else RGBColor(0x0F, 0x16, 0x24)
        for j, (val, cw, cs) in enumerate(zip(row_data, col_widths, col_starts)):
            add_rect(slide, cs, ry, cw, RH, bg)
            tc = C_RED if j == 2 and val != "—" else (C_YELLOW if j == 1 else C_WHITE)
            add_text_box(slide, val, cs + Inches(0.05), ry, cw - Inches(0.1), RH,
                         font_size=11, color=tc, align=PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT)

    # NLP section — droite
    add_rect(slide, Inches(7.2), Inches(1.35), Inches(5.7), Inches(5.5),
             RGBColor(0x0F, 0x16, 0x24), C_ACCENT)
    add_text_box(slide, "📝  Analyse NLP — Rapport d'Inspection",
                 Inches(7.3), Inches(1.45), Inches(5.5), Inches(0.4),
                 font_size=12, bold=True, color=C_ACCENT)

    nlp_items = [
        "🔍 Détection mots-clés métier GC",
        "  → harnais absent, chute d'objet,",
        "  → intervention urgente, canicule…",
        "",
        "📐 Regex extraction automatique",
        "  → vent à 95 km/h, 7 EPI manquants",
        "  → effectif de 45 travailleurs",
        "",
        "📊 TF-IDF Bigrams",
        "  → mesures préventives",
        "  → intervention corrective",
        "  → risque modéré",
        "",
        "⚖️ Alertes Code du Travail Tunisien",
        "  → Arrêt chantier automatique",
    ]

    nlp_y = Inches(1.95)
    for item in nlp_items:
        if item == "":
            nlp_y += Inches(0.05)
            continue
        col = C_GREEN if item.startswith("  →") else C_WHITE
        fsz = 10 if item.startswith("  →") else 11
        add_text_box(slide, item, Inches(7.35), nlp_y, Inches(5.3), Inches(0.28),
                     font_size=fsz, color=col)
        nlp_y += Inches(0.3)


def slide_niveaux_risque(prs):
    """Diapo 5 — Niveaux de risque définis."""
    slide = prs.slides.add_slide(blank_layout(prs))
    fill_bg(slide)
    add_header_bar(slide, "Niveaux de Risque Définis",
                   "Classification en 4 niveaux — base du système de prédiction", "🎯")

    levels = [
        ("🟢", "FAIBLE",   C_GREEN,  RGBColor(0x05, 0x2A, 0x10),
         "Conditions normales", "Conformité satisfaisante",
         "Suivi standard", "Visite planifiée"),
        ("🟡", "MOYEN",    C_YELLOW, RGBColor(0x2A, 0x1E, 0x05),
         "Vigilance requise", "Mesures préventives à envisager",
         "Visite de contrôle < 15 jours", "Rapport préventif"),
        ("🟠", "ÉLEVÉ",    C_ORANGE, RGBColor(0x2A, 0x12, 0x00),
         "Intervention corrective rapide", "Non-conformités détectées",
         "Action corrective < 48h", "Alerte chef de chantier"),
        ("🔴", "CRITIQUE", C_RED,    RGBColor(0x2A, 0x05, 0x05),
         "Arrêt de chantier immédiat", "Évacuation possible",
         "Arrêt immédiat + rapport ITT", "Intervention d'urgence"),
    ]

    cw = Inches(3.0)
    for i, (emoji, label, col, bg_col, cond1, cond2, action1, action2) in enumerate(levels):
        cx = Inches(0.35 + i * 3.2)
        cy = Inches(1.35)

        # Carte principale
        add_rect(slide, cx, cy, cw, Inches(5.7), bg_col, col)
        # Barre top
        add_rect(slide, cx, cy, cw, Pt(5), col)

        # Emoji + Label
        add_text_box(slide, emoji, cx, cy + Inches(0.1),
                     cw, Inches(0.5), font_size=28, align=PP_ALIGN.CENTER)
        add_text_box(slide, label, cx, cy + Inches(0.6),
                     cw, Inches(0.4), font_size=16, bold=True,
                     color=col, align=PP_ALIGN.CENTER)

        # Séparateur
        add_rect(slide, cx + Inches(0.2), cy + Inches(1.1),
                 cw - Inches(0.4), Pt(1), col)

        # Conditions
        add_text_box(slide, "DESCRIPTION",
                     cx + Inches(0.1), cy + Inches(1.2),
                     cw - Inches(0.2), Inches(0.3),
                     font_size=8, bold=True, color=col, align=PP_ALIGN.LEFT)
        add_text_box(slide, f"• {cond1}",
                     cx + Inches(0.1), cy + Inches(1.5),
                     cw - Inches(0.2), Inches(0.35),
                     font_size=10, color=C_WHITE)
        add_text_box(slide, f"• {cond2}",
                     cx + Inches(0.1), cy + Inches(1.85),
                     cw - Inches(0.2), Inches(0.35),
                     font_size=10, color=C_LIGHT_GRAY)

        # Actions
        add_rect(slide, cx + Inches(0.2), cy + Inches(2.35),
                 cw - Inches(0.4), Pt(1), RGBColor(0x2A, 0x3A, 0x55))
        add_text_box(slide, "PLAN D'ACTION",
                     cx + Inches(0.1), cy + Inches(2.45),
                     cw - Inches(0.2), Inches(0.3),
                     font_size=8, bold=True, color=col)
        add_text_box(slide, f"→ {action1}",
                     cx + Inches(0.1), cy + Inches(2.8),
                     cw - Inches(0.2), Inches(0.4),
                     font_size=10, color=C_WHITE)
        add_text_box(slide, f"→ {action2}",
                     cx + Inches(0.1), cy + Inches(3.2),
                     cw - Inches(0.2), Inches(0.4),
                     font_size=10, color=C_LIGHT_GRAY)


def slide_architecture(prs):
    """Diapo 6 — Architecture du système."""
    slide = prs.slides.add_slide(blank_layout(prs))
    fill_bg(slide)
    add_header_bar(slide, "Architecture du Système",
                   "Pipeline bout-en-bout : de la donnée brute à la décision", "⚙️",
                   "Pipeline ML+NLP", C_ACCENT)

    # Boites du pipeline
    boxes = [
        (Inches(0.4),  Inches(2.2), "📥\nDonnées\nd'Entrée",     "6 variables\nstructurées + texte", C_BLUE),
        (Inches(2.9),  Inches(2.2), "🔧\nFeature\nEngineering",  "48+ features\nNLP+GC lexicon",      C_ACCENT),
        (Inches(5.4),  Inches(2.2), "🤖\nMLP Neural\nNetwork",   "Best model\nF1=88.84%",             C_GREEN),
        (Inches(7.9),  Inches(2.2), "🎯\nPrédiction\n+ Confiance", "4 niveaux\nde risque",            C_ORANGE),
        (Inches(10.4), Inches(2.2), "📊\nDashboard\nStreamlit",  "Alertes +\nExplicabilité",          C_BLUE),
    ]

    BW = Inches(2.2)
    BH = Inches(2.5)

    for bx, by, title, sub, col in boxes:
        add_rect(slide, bx, by, BW, BH, RGBColor(0x0F, 0x16, 0x24), col)
        add_rect(slide, bx, by, BW, Pt(4), col)
        add_text_box(slide, title, bx, by + Inches(0.1), BW, Inches(0.9),
                     font_size=11, bold=True, color=col,
                     align=PP_ALIGN.CENTER, font_name="Calibri")
        add_text_box(slide, sub, bx, by + Inches(1.1), BW, Inches(1.2),
                     font_size=10, color=C_LIGHT_GRAY,
                     align=PP_ALIGN.CENTER, font_name="Calibri")

    # Flèches (simulées par rectangles fins)
    arrow_y = Inches(3.25)
    for ax in [Inches(2.65), Inches(5.15), Inches(7.65), Inches(10.15)]:
        add_rect(slide, ax, arrow_y, Inches(0.22), Pt(2), C_LIGHT_GRAY)
        # Pointe
        add_text_box(slide, "→", ax - Inches(0.05), arrow_y - Inches(0.12),
                     Inches(0.3), Inches(0.3), font_size=14, color=C_LIGHT_GRAY,
                     align=PP_ALIGN.CENTER)

    # 2 sous-flux dans Feature Engineering
    add_rect(slide, Inches(0.4), Inches(5.0), Inches(5.9), Inches(1.4),
             RGBColor(0x0D, 0x1B, 0x35), C_BORDER)
    add_text_box(slide, "🔢 Flux A — Structuré : Normalisation · Flags GC · One-Hot · Score Composite",
                 Inches(0.5), Inches(5.05), Inches(5.7), Inches(0.55),
                 font_size=10, color=C_BLUE)
    add_text_box(slide, "📝 Flux B — NLP : clean_text() · TF-IDF Bigrams · Lexique GC 20 indicateurs",
                 Inches(0.5), Inches(5.6), Inches(5.7), Inches(0.55),
                 font_size=10, color=C_GREEN)

    # Fusion symbol
    add_text_box(slide, "⊕ FUSION", Inches(6.35), Inches(5.2), Inches(1.2), Inches(0.4),
                 font_size=12, bold=True, color=C_ACCENT, align=PP_ALIGN.CENTER)


def slide_stack_tech(prs):
    """Diapo 7 — Stack technologique."""
    slide = prs.slides.add_slide(blank_layout(prs))
    fill_bg(slide)
    add_header_bar(slide, "Stack Technologique",
                   "Technologies sélectionnées pour robustesse et reproductibilité", "🛠️",
                   "Python 3.10+", C_GREEN)

    stack = [
        ("Langage",       "🐍 Python 3.10+",                                  C_GREEN),
        ("ML / DL",       "scikit-learn 1.8 · XGBoost 3.2 · imbalanced-learn",C_BLUE),
        ("NLP",           "NLTK 3.9 · TF-IDF (bigrams) · Regex · Lexique GC", C_ACCENT),
        ("Explicabilité", "SHAP 0.51 · LIME 0.2",                             C_ORANGE),
        ("Dashboard",     "Streamlit 1.56 · Plotly 7.0",                      C_BLUE),
        ("Données",       "Pandas 3.0 · NumPy 2.4 · joblib 1.5",             C_GREEN),
        ("Stats",         "SciPy 1.17 · statsmodels 0.14",                    C_LIGHT_GRAY),
        ("Persistance",   ".joblib — modèles sérialisés (random_state=42)",   C_YELLOW),
    ]

    # Section gauche — tableau
    RH = Inches(0.5)
    sy = Inches(1.38)

    add_rect(slide, Inches(0.35), sy, Inches(2.2), RH, RGBColor(0x1A, 0x2A, 0x4A))
    add_text_box(slide, "COUCHE", Inches(0.35), sy, Inches(2.2), RH,
                 font_size=10, bold=True, color=C_BLUE, align=PP_ALIGN.CENTER)
    add_rect(slide, Inches(2.65), sy, Inches(5.8), RH, RGBColor(0x1A, 0x2A, 0x4A))
    add_text_box(slide, "TECHNOLOGIES", Inches(2.65), sy, Inches(5.8), RH,
                 font_size=10, bold=True, color=C_BLUE, align=PP_ALIGN.CENTER)

    for i, (couche, tech, col) in enumerate(stack):
        ry = sy + RH + Inches(0.02) + i * (RH + Inches(0.02))
        bg = RGBColor(0x12, 0x1D, 0x32) if i % 2 == 0 else RGBColor(0x0F, 0x16, 0x24)
        add_rect(slide, Inches(0.35), ry, Inches(2.2), RH, bg)
        add_rect(slide, Inches(0.35), ry, Pt(4), RH, col)
        add_text_box(slide, couche, Inches(0.4), ry, Inches(2.1), RH,
                     font_size=11, bold=True, color=col)
        add_rect(slide, Inches(2.65), ry, Inches(5.8), RH, bg)
        add_text_box(slide, tech, Inches(2.7), ry, Inches(5.7), RH,
                     font_size=11, color=C_WHITE)

    # Section droite — chiffres clés
    add_rect(slide, Inches(8.7), Inches(1.35), Inches(4.2), Inches(5.75),
             RGBColor(0x0D, 0x1B, 0x35), C_BLUE)
    add_text_box(slide, "📈  Chiffres Clés du Projet",
                 Inches(8.8), Inches(1.45), Inches(4.0), Inches(0.4),
                 font_size=13, bold=True, color=C_BLUE)

    kpis = [
        ("2 400+",  "Inspections dans le dataset",     C_WHITE),
        ("48+",     "Features engineered",              C_GREEN),
        ("5",       "Modèles évalués",                  C_BLUE),
        ("89.0 %",  "Accuracy du modèle champion",      C_GREEN),
        ("88.84 %", "F1-Score (mesuré sur classes déséq.)", C_GREEN),
        ("±1.2 %",  "Stabilité cross-validation k=5",  C_YELLOW),
        ("4",       "Niveaux de risque classifiés",     C_ACCENT),
        ("4",       "Modules dashboard déployés",       C_BLUE),
    ]

    kpiy = Inches(1.95)
    for val, label, col in kpis:
        add_text_box(slide, val, Inches(8.8), kpiy, Inches(1.3), Inches(0.45),
                     font_size=16, bold=True, color=col)
        add_text_box(slide, label, Inches(10.15), kpiy + Inches(0.05),
                     Inches(2.6), Inches(0.35), font_size=10, color=C_LIGHT_GRAY)
        kpiy += Inches(0.6)


def slide_comparaison_modeles(prs):
    """Diapo 8 — Comparaison des modèles."""
    slide = prs.slides.add_slide(blank_layout(prs))
    fill_bg(slide)
    add_header_bar(slide, "Comparaison des Modèles ML",
                   "5 algorithmes évalués — sélection par F1-Score pondéré", "📊",
                   "MLP ← Champion", C_GREEN)

    models = [
        ("MLP Neural Network", 0.8900, 0.8884, 0.8870, 0.8900, True),
        ("XGBoost (tuned)",    0.8850, 0.8847, 0.8878, 0.8850, False),
        ("Dual Stream",        0.8900, 0.8840, 0.8829, 0.8900, False),
        ("Random Forest",      0.8650, 0.8632, 0.8631, 0.8650, False),
        ("Régression Log.",    0.8500, 0.8649, 0.8902, 0.8500, False),
    ]

    headers = ["Modèle", "Accuracy", "F1-Score", "Précision", "Rappel"]
    col_starts = [Inches(0.35), Inches(3.9), Inches(5.9), Inches(7.9), Inches(9.9)]
    col_widths  = [Inches(3.5),  Inches(1.9), Inches(1.9), Inches(1.9), Inches(1.9)]
    RH = Inches(0.52)
    sy = Inches(1.38)

    # Headers
    for hdr, cs, cw in zip(headers, col_starts, col_widths):
        add_rect(slide, cs, sy, cw, RH, RGBColor(0x1A, 0x2A, 0x4A))
        add_text_box(slide, hdr, cs, sy, cw, RH,
                     font_size=10, bold=True, color=C_BLUE, align=PP_ALIGN.CENTER)

    # Rows
    for i, (name, acc, f1, prec, rec, is_best) in enumerate(models):
        ry = sy + RH + Inches(0.04) + i * (RH + Inches(0.04))
        bg = RGBColor(0x0A, 0x1D, 0x12) if is_best else (
             RGBColor(0x12, 0x1D, 0x32) if i % 2 == 0 else RGBColor(0x0F, 0x16, 0x24))
        border_col = C_GREEN if is_best else None

        for j, (cs, cw) in enumerate(zip(col_starts, col_widths)):
            add_rect(slide, cs, ry, cw, RH, bg, border_col if j == 0 else None)

        # Left accent for best
        if is_best:
            add_rect(slide, col_starts[0], ry, Pt(4), RH, C_GREEN)

        # Name
        label = f"⭐ {name}" if is_best else f"   {name}"
        add_text_box(slide, label, col_starts[0] + Inches(0.08), ry,
                     col_widths[0] - Inches(0.1), RH,
                     font_size=12, bold=is_best, color=C_GREEN if is_best else C_WHITE)

        for j, val in enumerate([acc, f1, prec, rec]):
            col = C_GREEN if is_best else C_WHITE
            cs = col_starts[j + 1]
            cw = col_widths[j + 1]
            add_text_box(slide, f"{val:.2%}", cs, ry, cw, RH,
                         font_size=13, bold=is_best, color=col, align=PP_ALIGN.CENTER)

    # Barre de progression F1
    sy2 = Inches(4.7)
    add_text_box(slide, "F1-Score comparatif (visuellement)",
                 Inches(0.35), sy2, Inches(12), Inches(0.35),
                 font_size=11, bold=True, color=C_BLUE)

    bar_models = [("MLP", 0.8884, C_GREEN), ("XGBoost", 0.8847, C_BLUE),
                  ("Dual", 0.8840, C_ACCENT), ("RF", 0.8632, C_YELLOW),
                  ("Log.", 0.8649, C_LIGHT_GRAY)]

    max_bar = Inches(8.0)
    for i, (nm, f1v, col) in enumerate(bar_models):
        bx = Inches(0.35)
        by = sy2 + Inches(0.45) + i * Inches(0.42)
        bar_len = max_bar * f1v
        add_text_box(slide, nm, bx, by, Inches(0.9), Inches(0.35),
                     font_size=10, color=C_LIGHT_GRAY)
        add_rect(slide, Inches(1.3), by + Inches(0.04), bar_len, Inches(0.3), col)
        add_text_box(slide, f"{f1v:.2%}", Inches(1.35) + bar_len,
                     by, Inches(0.8), Inches(0.35),
                     font_size=10, bold=True, color=col)

    # Note F1
    add_rect(slide, Inches(0.35), Inches(6.95), Inches(12.6), Inches(0.45),
             RGBColor(0x0A, 0x1D, 0x12))
    add_text_box(slide,
                 "📌  Pourquoi le F1-Score ? Les classes sont déséquilibrées (peu de cas Critique) "
                 "→ le F1 est l'indicateur de référence, pas l'Accuracy.",
                 Inches(0.45), Inches(6.97), Inches(12.4), Inches(0.4),
                 font_size=10, color=C_GREEN)


def slide_validation_croisee(prs):
    """Diapo 9 — Validation croisée."""
    slide = prs.slides.add_slide(blank_layout(prs))
    fill_bg(slide)
    add_header_bar(slide, "Validation Croisée (k=5)",
                   "Robustesse et stabilité des algorithmes sur 5 partitions", "🔄",
                   "k-Fold Stratifié", C_ACCENT)

    cv_data = [
        ("XGBoost (tuned)",    "89.97 %", "±1.7 %", "Runner-up",  C_BLUE),
        ("Random Forest",      "88.55 %", "±1.9 %", "Backup",      C_YELLOW),
        ("MLP Neural Network", "85.36 %", "±1.2 %", "✅ Champion", C_GREEN),
        ("SVM (RBF)",          "82.10 %", "±2.3 %", "Évalué",     C_LIGHT_GRAY),
        ("Log. Regression",    "78.40 %", "±2.1 %", "Référence",   C_LIGHT_GRAY),
    ]

    headers = ["Algorithme", "F1 Moyen", "Stabilité", "Statut"]
    col_w = [Inches(4.0), Inches(2.0), Inches(1.8), Inches(2.5)]
    col_x = [Inches(0.35), Inches(4.45), Inches(6.55), Inches(8.45)]
    RH = Inches(0.52)
    sy = Inches(1.38)

    for hdr, cx, cw in zip(headers, col_x, col_w):
        add_rect(slide, cx, sy, cw, RH, RGBColor(0x1A, 0x2A, 0x4A))
        add_text_box(slide, hdr, cx, sy, cw, RH, font_size=10, bold=True,
                     color=C_BLUE, align=PP_ALIGN.CENTER)

    for i, (name, f1, stab, status, col) in enumerate(cv_data):
        ry = sy + RH + Inches(0.04) + i * (RH + Inches(0.04))
        is_champ = "Champion" in status
        bg = RGBColor(0x0A, 0x1D, 0x12) if is_champ else (
             RGBColor(0x12, 0x1D, 0x32) if i % 2 == 0 else RGBColor(0x0F, 0x16, 0x24))
        for cx, cw in zip(col_x, col_w):
            add_rect(slide, cx, ry, cw, RH, bg)
        if is_champ:
            add_rect(slide, col_x[0], ry, Pt(4), RH, C_GREEN)

        add_text_box(slide, f"{'⭐ ' if is_champ else '   '}{name}",
                     col_x[0] + Inches(0.08), ry, col_w[0], RH,
                     font_size=12, bold=is_champ, color=C_GREEN if is_champ else C_WHITE)
        add_text_box(slide, f1, col_x[1], ry, col_w[1], RH,
                     font_size=13, bold=is_champ, color=col, align=PP_ALIGN.CENTER)
        add_text_box(slide, stab, col_x[2], ry, col_w[2], RH,
                     font_size=12, color=C_YELLOW if "±" in stab else C_LIGHT_GRAY,
                     align=PP_ALIGN.CENTER)
        add_text_box(slide, status, col_x[3], ry, col_w[3], RH,
                     font_size=11, bold=is_champ, color=col, align=PP_ALIGN.CENTER)

    # Justification
    add_rect(slide, Inches(0.35), Inches(5.1), Inches(12.6), Inches(1.5),
             RGBColor(0x0A, 0x1D, 0x12), C_GREEN)
    add_text_box(slide, "💡  Pourquoi le MLP est sélectionné malgré un CV moyen légèrement inférieur à XGBoost ?",
                 Inches(0.45), Inches(5.15), Inches(12.4), Inches(0.4),
                 font_size=11, bold=True, color=C_GREEN)

    reasons = [
        "✅  Meilleure stabilité : ±1.2% vs ±1.7% → moins de sur-apprentissage sur partitions difficiles",
        "✅  Supériorité sur les rapports textuels complexes (combinaison TF-IDF + structuré)",
        "✅  Performance test-set supérieure : 89.0% Accuracy vs 88.5% — validée sur données hors-échantillon",
    ]
    ry = Inches(5.6)
    for r in reasons:
        add_text_box(slide, r, Inches(0.5), ry, Inches(12.3), Inches(0.35),
                     font_size=11, color=C_WHITE)
        ry += Inches(0.37)


def slide_feature_engineering(prs):
    """Diapo 10 — Feature Engineering."""
    slide = prs.slides.add_slide(blank_layout(prs))
    fill_bg(slide)
    add_header_bar(slide, "Feature Engineering",
                   "Construction des 48+ variables — moteur de la prédiction", "🔧",
                   "48+ features", C_BLUE)

    groups = [
        ("🔢\n5\nNumériques",     "StandardScaler\nEffectif · Temp · Vent\nEPI · Risque Hist.",  C_BLUE,   Inches(0.35)),
        ("🚩\n11\nFlags Binaires", "Alertes météo\nEPI critique\nEffectif élevé",                  C_YELLOW, Inches(2.85)),
        ("🏗️\n7\nOne-Hot",        "Type de travaux\nCoffrage / Excav.\nGrutage / Hauteur…",       C_ACCENT, Inches(5.35)),
        ("🔍\n9\nRégex",          "Extraction texte\nVitesse vent / Temp.\nEffectif / Urgence",    C_GREEN,  Inches(7.85)),
        ("📚\n20\nLexique GC",    "Indicateurs binaires\nHarnais · EPI · Vent\nRisque_elev_txt…", C_ORANGE, Inches(10.35)),
    ]

    GW = Inches(2.3)
    GH = Inches(3.2)
    gy = Inches(1.38)

    for title, desc, col, gx in groups:
        add_rect(slide, gx, gy, GW, GH, RGBColor(0x0F, 0x16, 0x24), col)
        add_rect(slide, gx, gy, GW, Pt(4), col)
        add_text_box(slide, title, gx, gy + Inches(0.05), GW, Inches(0.85),
                     font_size=11, bold=True, color=col, align=PP_ALIGN.CENTER)
        add_rect(slide, gx + Inches(0.2), gy + Inches(0.95),
                 GW - Inches(0.4), Pt(1), col)
        add_text_box(slide, desc, gx + Inches(0.1), gy + Inches(1.05),
                     GW - Inches(0.2), GH - Inches(1.1),
                     font_size=10, color=C_LIGHT_GRAY, align=PP_ALIGN.CENTER)

    # Score composite + TF-IDF
    sy2 = Inches(4.75)
    add_rect(slide, Inches(0.35), sy2, Inches(5.9), Inches(1.5),
             RGBColor(0x0D, 0x1B, 0x35), C_ORANGE)
    add_text_box(slide, "⚖️  Score Composite Pondéré",
                 Inches(0.45), sy2 + Inches(0.08), Inches(5.7), Inches(0.35),
                 font_size=11, bold=True, color=C_ORANGE)
    add_text_box(slide,
                 "Risque Historique ×40%  +  EPI ×25%  +  Vent ×20%  +  Effectif ×10%  +  Température ×5%",
                 Inches(0.45), sy2 + Inches(0.5), Inches(5.7), Inches(0.4),
                 font_size=11, color=C_WHITE)
    add_text_box(slide, "→  Signal composite unique synthétisant les 5 dimensions de risque",
                 Inches(0.45), sy2 + Inches(0.95), Inches(5.7), Inches(0.4),
                 font_size=10, color=C_LIGHT_GRAY)

    add_rect(slide, Inches(6.45), sy2, Inches(6.5), Inches(1.5),
             RGBColor(0x0D, 0x1B, 0x35), C_ACCENT)
    add_text_box(slide, "📝  TF-IDF Bigrams — Rapport d'Inspection",
                 Inches(6.55), sy2 + Inches(0.08), Inches(6.3), Inches(0.35),
                 font_size=11, bold=True, color=C_ACCENT)
    add_text_box(slide,
                 "Top features : « mesures préventives » · « intervention corrective » · « risque modéré »",
                 Inches(6.55), sy2 + Inches(0.5), Inches(6.3), Inches(0.4),
                 font_size=11, color=C_WHITE)
    add_text_box(slide, "→  50 features TF-IDF sélectionnées par importance sur corpus GC",
                 Inches(6.55), sy2 + Inches(0.95), Inches(6.3), Inches(0.4),
                 font_size=10, color=C_LIGHT_GRAY)


def slide_preprocessing(prs):
    """Diapo — Prétraitement & Flags GC Réglementaires."""
    slide = prs.slides.add_slide(blank_layout(prs))
    fill_bg(slide)
    add_header_bar(slide, "Prétraitement des Données",
                   "Imputation · Flags réglementaires GC · Winsorisation · Standardisation", "🔧",
                   "Section 2 Notebook", C_ORANGE)

    # Left — pipeline steps
    steps = [
        ("1", "Imputation Médiane",   "SimpleImputer(strategy='median')\nRobuste aux outliers — aucune fuite de données", C_BLUE),
        ("2", "6 Flags Binaires GC",  "Créés AVANT winsorisation pour capturer\nles vraies valeurs extrêmes réglementaires", C_RED),
        ("3", "Winsorisation IQR",    "Bornes : Q1 – 1.5×IQR  /  Q3 + 1.5×IQR\nRemplacement (pas suppression) des extrêmes", C_ORANGE),
        ("4", "Standardisation",      "StandardScaler → μ=0 σ=1\nObligatoire pour MLP et distance-based models", C_GREEN),
        ("5", "One-Hot Encoding",     "Type_Travaux → 7 colonnes binaires\nCoffrage / Excavation / Grutage / Hauteur…", C_ACCENT),
    ]

    RH = Inches(0.85)
    sy = Inches(1.35)
    for i, (num, title, desc, col) in enumerate(steps):
        ry = sy + i * (RH + Inches(0.06))
        add_rect(slide, Inches(0.35), ry, Inches(6.0), RH, RGBColor(0x0F, 0x16, 0x24), col)
        add_rect(slide, Inches(0.35), ry, Pt(4), RH, col)
        # Numéro
        add_text_box(slide, num, Inches(0.4), ry, Inches(0.4), RH,
                     font_size=16, bold=True, color=col, align=PP_ALIGN.CENTER)
        # Title + desc
        add_text_box(slide, title, Inches(0.85), ry + Inches(0.05),
                     Inches(5.3), Inches(0.3), font_size=12, bold=True, color=col)
        add_text_box(slide, desc, Inches(0.85), ry + Inches(0.35),
                     Inches(5.3), Inches(0.45), font_size=9.5, color=C_LIGHT_GRAY)

    # Right — 6 flags GC table
    add_rect(slide, Inches(6.7), Inches(1.35), Inches(6.2), Inches(5.45),
             RGBColor(0x0D, 0x1B, 0x35), C_RED)
    add_text_box(slide, "🚩  6 Flags GC Réglementaires (EN 13000 + Code du Travail)",
                 Inches(6.8), Inches(1.42), Inches(6.0), Inches(0.38),
                 font_size=11, bold=True, color=C_RED)

    flags = [
        ("flag_vent_alerte",   "Vent ≥ 45 km/h",    "Arrêt grutage",      C_ORANGE),
        ("flag_vent_danger",   "Vent ≥ 80 km/h",    "Arrêt total",        C_RED),
        ("flag_temp_froid",    "Temp < 5 °C",        "Hypothermie/verglas",C_BLUE),
        ("flag_temp_chaleur",  "Temp > 35 °C",       "Coup de chaleur",    C_YELLOW),
        ("flag_epi_critique",  "EPI ≥ 5 manquants",  "Non-conformité DREAL",C_RED),
        ("flag_effectif_eleve","Effectif > 30",       "Ratio chef dégradé", C_ORANGE),
    ]

    fy = Inches(1.9)
    FRH = Inches(0.65)
    for fname, seuil, impact, col in flags:
        add_rect(slide, Inches(6.7), fy, Inches(6.2), FRH,
                 RGBColor(0x12, 0x1D, 0x32))
        add_rect(slide, Inches(6.7), fy, Pt(4), FRH, col)
        add_text_box(slide, fname, Inches(6.75), fy + Inches(0.04),
                     Inches(2.5), Inches(0.28), font_size=9.5, bold=True, color=col)
        add_text_box(slide, seuil, Inches(9.35), fy + Inches(0.04),
                     Inches(1.6), Inches(0.28), font_size=9.5, color=C_YELLOW, align=PP_ALIGN.CENTER)
        add_text_box(slide, f"→ {impact}", Inches(11.0), fy + Inches(0.04),
                     Inches(1.8), Inches(0.28), font_size=9.5, color=C_LIGHT_GRAY)
        add_text_box(slide, f"= 1 si {seuil.lower()}, 0 sinon", Inches(6.75), fy + Inches(0.33),
                     Inches(4.0), Inches(0.25), font_size=8.5, color=RGBColor(0x55, 0x65, 0x80))
        fy += FRH + Inches(0.04)

    # Bottom note
    add_rect(slide, Inches(0.35), Inches(6.85), Inches(12.6), Inches(0.42),
             RGBColor(0x12, 0x1D, 0x32))
    add_text_box(slide,
                 "⚠️  Ordre critique : Flags créés sur données brutes → Winsorisation → Standardisation  |  "
                 "Empêche la perte d'information réglementaire lors du clipping IQR",
                 Inches(0.45), Inches(6.88), Inches(12.4), Inches(0.35),
                 font_size=9.5, color=C_ORANGE)


def slide_explainability(prs):
    """Diapo — Explicabilité SHAP & LIME."""
    slide = prs.slides.add_slide(blank_layout(prs))
    fill_bg(slide)
    add_header_bar(slide, "Explicabilité des Prédictions",
                   "SHAP + LIME — Auditabilité totale requise par le cahier des charges Safety-First", "🔍",
                   "SHAP 0.51 + LIME 0.2", C_ORANGE)

    # Left column — SHAP
    add_rect(slide, Inches(0.35), Inches(1.35), Inches(6.0), Inches(5.4),
             RGBColor(0x0F, 0x16, 0x24), C_ORANGE)
    add_rect(slide, Inches(0.35), Inches(1.35), Inches(6.0), Pt(4), C_ORANGE)
    add_text_box(slide, "📊  SHAP — TreeExplainer",
                 Inches(0.45), Inches(1.42), Inches(5.8), Inches(0.38),
                 font_size=13, bold=True, color=C_ORANGE)

    shap_items = [
        ("Global (Summary Plot)", "Top-20 features pour la classe Critique\nIndique l'importance relative de chaque variable"),
        ("Local (Waterfall Plot)", "Décortique 1 inspection individuelle\nContribution feature par feature à la décision"),
        ("Top facteurs Critique", "alerte_vent · harnais_endommage\nintervention_urgente · EPI_Manquants · Vent_kmh"),
    ]

    sy_s = Inches(1.88)
    for title, desc in shap_items:
        add_rect(slide, Inches(0.45), sy_s, Inches(5.75), Inches(0.98),
                 RGBColor(0x12, 0x1D, 0x32))
        add_rect(slide, Inches(0.45), sy_s, Pt(3), Inches(0.98), C_ORANGE)
        add_text_box(slide, title, Inches(0.55), sy_s + Inches(0.05),
                     Inches(5.5), Inches(0.3), font_size=11, bold=True, color=C_WHITE)
        add_text_box(slide, desc, Inches(0.55), sy_s + Inches(0.38),
                     Inches(5.5), Inches(0.55), font_size=9.5, color=C_LIGHT_GRAY)
        sy_s += Inches(1.05)

    # SHAP formula
    add_rect(slide, Inches(0.45), sy_s + Inches(0.1), Inches(5.75), Inches(0.55),
             RGBColor(0x0A, 0x1D, 0x12))
    add_text_box(slide, "f(x) = φ₀ + Σ φᵢ xᵢ  (valeurs Shapley)",
                 Inches(0.55), sy_s + Inches(0.15), Inches(5.5), Inches(0.4),
                 font_size=11, color=C_GREEN, italic=True, align=PP_ALIGN.CENTER)

    # Right column — LIME + Interprétation métier
    add_rect(slide, Inches(6.6), Inches(1.35), Inches(6.1), Inches(5.4),
             RGBColor(0x0F, 0x16, 0x24), C_BLUE)
    add_rect(slide, Inches(6.6), Inches(1.35), Inches(6.1), Pt(4), C_BLUE)
    add_text_box(slide, "🔬  LIME + Interprétation Métier GC",
                 Inches(6.7), Inches(1.42), Inches(5.9), Inches(0.38),
                 font_size=13, bold=True, color=C_BLUE)

    lime_desc = (
        "LimeTabularExplainer entraîné sur X_train_res (SMOTE)\n"
        "• Mode classification · 10 features explicatives\n"
        "• Perturbation locale autour de l'instance cible\n"
        "• Modèle linéaire approximant le MLP localement"
    )
    add_text_box(slide, lime_desc, Inches(6.7), Inches(1.88),
                 Inches(5.9), Inches(1.05), font_size=10, color=C_LIGHT_GRAY)

    # Interpretation table
    add_text_box(slide, "📋  Interprétation Métier — Top Features",
                 Inches(6.7), Inches(3.05), Inches(5.9), Inches(0.32),
                 font_size=11, bold=True, color=C_BLUE)

    gc_interp = [
        ("Vent_kmh_scaled",     "↑ risque", "Arrêt grue > 45 km/h (EN 13000)",  C_RED),
        ("EPI_Manquants_scaled","↑ risque", "Exposition directe vie humaine",     C_RED),
        ("alerte_vent",         "Flag txt",  "Alerte auto chef de chantier",       C_ORANGE),
        ("harnais_endommage",   "Flag txt",  "Remplacement immédiat obligatoire",  C_RED),
        ("intervention_urgente","Flag txt",  "Escalade responsable sécurité <2h",  C_ORANGE),
        ("travail_hauteur",     "Flag txt",  "Habilitation + filet de sécurité",   C_YELLOW),
    ]

    gy = Inches(3.42)
    for feat, impact, action, col in gc_interp:
        add_rect(slide, Inches(6.7), gy, Inches(6.0), Inches(0.37),
                 RGBColor(0x12, 0x1D, 0x32))
        add_rect(slide, Inches(6.7), gy, Pt(3), Inches(0.37), col)
        add_text_box(slide, feat, Inches(6.74), gy + Inches(0.04),
                     Inches(2.4), Inches(0.28), font_size=9, bold=True, color=col)
        add_text_box(slide, impact, Inches(9.2), gy + Inches(0.04),
                     Inches(0.9), Inches(0.28), font_size=9, color=C_YELLOW, align=PP_ALIGN.CENTER)
        add_text_box(slide, action, Inches(10.15), gy + Inches(0.04),
                     Inches(2.45), Inches(0.28), font_size=8.5, color=C_LIGHT_GRAY)
        gy += Inches(0.4)

    # Bottom
    add_rect(slide, Inches(0.35), Inches(6.85), Inches(12.6), Inches(0.42),
             RGBColor(0x0A, 0x1D, 0x12), C_GREEN)
    add_text_box(slide,
                 "✅  Conformité cahier des charges : chaque décision du modèle est traçable, explicable et actionnable "
                 "→ Validation terrain possible sans compétences ML",
                 Inches(0.45), Inches(6.88), Inches(12.4), Inches(0.35),
                 font_size=10, color=C_GREEN)


def slide_dashboard(prs):
    """Diapo 11 — Dashboard GC Safety AI."""
    slide = prs.slides.add_slide(blank_layout(prs))
    fill_bg(slide)
    add_header_bar(slide, "Dashboard GC Safety AI",
                   "Application Streamlit — 4 modules opérationnels déployés", "📊",
                   "Streamlit 1.56", C_BLUE)

    modules = [
        ("🔮", "Analyse de Risque",  C_BLUE,
         ["Prédiction IA temps réel",
          "Mode scénario prédéfini",
          "Comparaison de scénarios",
          "Alertes réglementaires GC",
          "Radar & jauge de confiance"]),
        ("📊", "Tableau de Bord",    C_GREEN,
         ["KPIs : inspections, critiques",
          "Heatmap risques × travaux",
          "Top features Random Forest",
          "Tendances temporelles",
          "Filtres dynamiques"]),
        ("🏆", "Performance IA",    C_ACCENT,
         ["Métriques comparatives",
          "Validation croisée k=5",
          "Architecture Dual-Stream",
          "Notes méthodologiques",
          "Graphiques Plotly interactifs"]),
        ("📤", "Import / Export",   C_ORANGE,
         ["Traitement batch CSV",
          "Export résultats annotés",
          "Rapport PDF généré",
          "Historique des prédictions",
          "Téléchargement Excel"]),
    ]

    MW = Inches(3.1)
    MH = Inches(4.8)
    my = Inches(1.38)

    for i, (icon, name, col, features) in enumerate(modules):
        mx = Inches(0.35 + i * 3.25)
        add_rect(slide, mx, my, MW, MH, RGBColor(0x0F, 0x16, 0x24), col)
        add_rect(slide, mx, my, MW, Pt(4), col)

        add_text_box(slide, icon, mx, my + Inches(0.05), MW, Inches(0.5),
                     font_size=24, align=PP_ALIGN.CENTER)
        add_text_box(slide, name, mx, my + Inches(0.55), MW, Inches(0.4),
                     font_size=12, bold=True, color=col, align=PP_ALIGN.CENTER)
        add_rect(slide, mx + Inches(0.2), my + Inches(1.05),
                 MW - Inches(0.4), Pt(1), col)

        fy = my + Inches(1.15)
        for feat in features:
            add_text_box(slide, f"• {feat}", mx + Inches(0.12), fy,
                         MW - Inches(0.2), Inches(0.38),
                         font_size=10, color=C_LIGHT_GRAY)
            fy += Inches(0.38)

    # Bas — URL demo
    add_rect(slide, Inches(0.35), Inches(6.35), Inches(12.6), Inches(0.7),
             RGBColor(0x0D, 0x1B, 0x35))
    add_text_box(slide, "🚀  Déploiement : Streamlit Cloud · Docker ready · API FastAPI intégrable",
                 Inches(0.45), Inches(6.42), Inches(12.4), Inches(0.45),
                 font_size=11, color=C_BLUE, align=PP_ALIGN.CENTER)


def slide_recommandations_gc(prs):
    """Diapo 12 — Recommandations Opérationnelles GC."""
    slide = prs.slides.add_slide(blank_layout(prs))
    fill_bg(slide)
    add_header_bar(slide, "Recommandations Opérationnelles",
                   "Plan d'action par niveau de risque — à destination des chefs de chantier", "🏗️",
                   "Côté GC", C_GREEN)

    recs = [
        ("📱\n01", "Intégration au Protocole\nd'Inspection",
         "Saisir le rapport directement sur tablette après chaque visite chantier. "
         "L'IA prédit le niveau en < 1 seconde.",
         C_BLUE),
        ("📋\n02", "Plan d'Action\npar Niveau",
         "🟢 Faible → suivi standard\n"
         "🟡 Moyen → visite contrôle < 15j\n"
         "🟠 Élevé → action corrective < 48h\n"
         "🔴 Critique → arrêt + rapport ITT",
         C_ORANGE),
        ("📈\n03", "Capitalisation\ndes Données",
         "Chaque inspection annotée améliore les prédictions futures. "
         "Pipeline d'apprentissage continu intégré.",
         C_GREEN),
        ("🎓\n04", "Formation\ndes Équipes",
         "Former les chefs de chantier à la lecture des alertes réglementaires "
         "générées automatiquement (Code du Travail Tunisien).",
         C_ACCENT),
    ]

    RW = Inches(2.9)
    RH = Inches(4.6)
    ry = Inches(1.38)

    for i, (num, title, body, col) in enumerate(recs):
        rx = Inches(0.35 + i * 3.2)
        add_rect(slide, rx, ry, RW, RH, RGBColor(0x0F, 0x16, 0x24), col)
        add_rect(slide, rx, ry, RW, Pt(4), col)

        add_text_box(slide, num, rx, ry + Inches(0.05), RW, Inches(0.6),
                     font_size=18, bold=True, color=col, align=PP_ALIGN.CENTER)
        add_text_box(slide, title, rx, ry + Inches(0.65), RW, Inches(0.55),
                     font_size=12, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
        add_rect(slide, rx + Inches(0.2), ry + Inches(1.28),
                 RW - Inches(0.4), Pt(1), col)
        add_text_box(slide, body, rx + Inches(0.12), ry + Inches(1.38),
                     RW - Inches(0.2), RH - Inches(1.45),
                     font_size=10, color=C_LIGHT_GRAY, wrap=True)


def slide_recommandations_tech(prs):
    """Diapo 13 — Recommandations Techniques."""
    slide = prs.slides.add_slide(blank_layout(prs))
    fill_bg(slide)
    add_header_bar(slide, "Recommandations Techniques",
                   "Roadmap d'amélioration du système IA", "⚙️",
                   "Côté Info", C_ACCENT)

    recs = [
        ("📊", "Enrichissement\nDataset",
         "Passer de 2 400 à 10 000+ inspections pour améliorer la robustesse "
         "sur les classes rares (Critique). Collecte automatisée via API.",
         C_BLUE, "Court terme"),
        ("🧠", "NLP Avancé\nCamemBERT",
         "Intégrer CamemBERT (optionnel — nécessite GPU) pour une analyse NLP "
         "plus fine des rapports rédigés en français.",
         C_ACCENT, "Moyen terme"),
        ("🔄", "CI/CD\nPipeline",
         "Automatiser le ré-entraînement mensuel avec les nouvelles données "
         "collectées. Tests de régression automatiques.",
         C_GREEN, "Court terme"),
        ("📡", "Monitoring\nData Drift",
         "Détecter la dérive de données (data drift) via alertes statistiques. "
         "Tableau de bord de monitoring MLOps.",
         C_YELLOW, "Moyen terme"),
        ("🔌", "API REST\nFastAPI",
         "Exposer le moteur de prédiction via FastAPI pour intégration dans des "
         "systèmes tiers (ERP BTP, logiciels de gestion de chantier).",
         C_ORANGE, "Long terme"),
    ]

    RW = Inches(2.35)
    RH = Inches(4.6)
    ry = Inches(1.38)

    for i, (icon, title, body, col, term) in enumerate(recs):
        rx = Inches(0.35 + i * 2.55)
        add_rect(slide, rx, ry, RW, RH, RGBColor(0x0F, 0x16, 0x24), col)
        add_rect(slide, rx, ry, RW, Pt(4), col)

        add_text_box(slide, icon, rx, ry + Inches(0.05), RW, Inches(0.4),
                     font_size=20, align=PP_ALIGN.CENTER)
        add_text_box(slide, title, rx, ry + Inches(0.5), RW, Inches(0.55),
                     font_size=11, bold=True, color=col, align=PP_ALIGN.CENTER)
        add_text_box(slide, body, rx + Inches(0.1), ry + Inches(1.15),
                     RW - Inches(0.2), RH - Inches(1.75),
                     font_size=9.5, color=C_LIGHT_GRAY, wrap=True)

        # Badge terme
        badge_col = C_BLUE if "Court" in term else (C_YELLOW if "Moyen" in term else C_RED)
        add_badge(slide, term, rx + Inches(0.25), ry + RH - Inches(0.42), badge_col)


def slide_perspectives(prs):
    """Diapo 14 — Perspectives d'évolution."""
    slide = prs.slides.add_slide(blank_layout(prs))
    fill_bg(slide)
    add_header_bar(slide, "Perspectives d'Évolution",
                   "Feuille de route 3 horizons — Court / Moyen / Long terme", "🚀")

    horizons = [
        ("⚡", "Court terme\n(< 6 mois)",  C_GREEN, C_GREEN,
         ["☁️  Déploiement Streamlit Cloud / Azure",
          "🔌  API REST FastAPI v1.0",
          "📦  Docker + CI/CD GitHub Actions",
          "📊  Monitoring data drift actif",
          "📚  Enrichissement dataset 5 000+",
          "🔄  Ré-entraînement automatique"]),
        ("📡", "Moyen terme\n(6-18 mois)", C_BLUE, C_BLUE,
         ["🌡️  Capteurs IoT météo en temps réel",
          "🧠  CamemBERT NLP (GPU cloud)",
          "📱  App mobile inspecteur",
          "🔗  Intégration ERP BTP Tunisien",
          "🌍  Dataset multi-régions",
          "📈  10 000+ inspections annotées"]),
        ("🌐", "Long terme\n(18 mois+)",   C_ACCENT, C_ACCENT,
         ["🏢  Plateforme SaaS multi-chantiers",
          "🔒  Apprentissage fédéré",
          "     (confidentialité entreprises)",
          "🤝  Partenariat CNAM Tunisie",
          "🌏  Extension Maghreb & Afrique",
          "🏆  Certification ISO 45001 ready"]),
    ]

    HW = Inches(4.0)
    HH = Inches(5.2)
    hy = Inches(1.35)

    for i, (icon, title, col, border, items) in enumerate(horizons):
        hx = Inches(0.35 + i * 4.45)
        add_rect(slide, hx, hy, HW, HH, RGBColor(0x0F, 0x16, 0x24), border)
        add_rect(slide, hx, hy, HW, Pt(5), col)

        add_text_box(slide, icon, hx, hy + Inches(0.05), HW, Inches(0.5),
                     font_size=28, align=PP_ALIGN.CENTER)
        add_text_box(slide, title, hx, hy + Inches(0.55), HW, Inches(0.55),
                     font_size=13, bold=True, color=col, align=PP_ALIGN.CENTER)
        add_rect(slide, hx + Inches(0.2), hy + Inches(1.2),
                 HW - Inches(0.4), Pt(1), col)

        iy = hy + Inches(1.3)
        for item in items:
            add_text_box(slide, item, hx + Inches(0.12), iy,
                         HW - Inches(0.2), Inches(0.42),
                         font_size=10, color=C_LIGHT_GRAY if not item.startswith("  ") else RGBColor(0x55, 0x65, 0x80))
            iy += Inches(0.42)


def slide_conclusion(prs):
    """Diapo 15 — Conclusion."""
    slide = prs.slides.add_slide(blank_layout(prs))
    fill_bg(slide)

    # Bande accent haute
    add_rect(slide, Inches(0), Inches(0), SLIDE_W, Pt(5), C_BLUE)

    add_text_box(slide, "GC Safety AI",
                 Inches(0.5), Inches(0.25), Inches(12.33), Inches(0.7),
                 font_size=36, bold=True, color=C_WHITE,
                 align=PP_ALIGN.CENTER, font_name="Calibri")
    add_text_box(slide, "Un système opérationnel de prédiction du risque chantier par Intelligence Artificielle",
                 Inches(0.5), Inches(0.9), Inches(12.33), Inches(0.45),
                 font_size=14, color=C_BLUE, bold=True,
                 align=PP_ALIGN.CENTER)

    add_separator(slide, Inches(1.45), C_BORDER)

    # Citation résultat principal
    add_rect(slide, Inches(0.5), Inches(1.55), Inches(12.33), Inches(1.1),
             RGBColor(0x0A, 0x1D, 0x12), C_GREEN)
    add_text_box(slide,
                 "\" GC Safety AI démontre qu'un système hybride ML+NLP peut atteindre une précision de 89 % "
                 "pour la prédiction du niveau de risque chantier — surpassant l'évaluation humaine "
                 "non assistée en rapidité et en cohérence. \"",
                 Inches(0.65), Inches(1.6), Inches(12.0), Inches(0.95),
                 font_size=12, color=C_GREEN, italic=True, align=PP_ALIGN.CENTER)

    # 3 blocs apport
    apports = [
        ("🏗️\nCôté GC",   C_BLUE,
         "Formalisation des critères de risque en variables quantifiables et actionnables"),
        ("💻\nCôté Info",  C_ACCENT,
         "Pipeline complet MLOps : de la donnée brute au dashboard interactif"),
        ("🤝\nEnsemble",   C_GREEN,
         "Outil opérationnel prêt à l'emploi, extensible, documenté et déployable"),
    ]

    AW = Inches(4.0)
    AH = Inches(2.1)
    ay = Inches(2.85)

    for i, (title, col, body) in enumerate(apports):
        ax = Inches(0.5 + i * 4.35)
        add_rect(slide, ax, ay, AW, AH, RGBColor(0x0F, 0x16, 0x24), col)
        add_rect(slide, ax, ay, AW, Pt(4), col)
        add_text_box(slide, title, ax, ay + Inches(0.05), AW, Inches(0.55),
                     font_size=14, bold=True, color=col, align=PP_ALIGN.CENTER)
        add_text_box(slide, body, ax + Inches(0.12), ay + Inches(0.65),
                     AW - Inches(0.2), AH - Inches(0.7),
                     font_size=11, color=C_LIGHT_GRAY, align=PP_ALIGN.CENTER, wrap=True)

    # KPIs finaux
    add_separator(slide, Inches(5.1), C_BORDER)

    kpis = [
        ("89 %",    "Accuracy",         C_GREEN),
        ("88.84 %", "F1-Score",         C_GREEN),
        ("48+",     "Features",         C_BLUE),
        ("2 400+",  "Inspections",      C_BLUE),
        ("5",       "Modèles testés",   C_ACCENT),
        ("4",       "Modules dashboard",C_ACCENT),
    ]

    kpw = Inches(2.0)
    kpy = Inches(5.25)
    for i, (val, label, col) in enumerate(kpis):
        kpx = Inches(0.5 + i * 2.15)
        add_text_box(slide, val, kpx, kpy, kpw, Inches(0.5),
                     font_size=22, bold=True, color=col, align=PP_ALIGN.CENTER)
        add_text_box(slide, label, kpx, kpy + Inches(0.48), kpw, Inches(0.3),
                     font_size=9, color=C_LIGHT_GRAY, align=PP_ALIGN.CENTER)

    # Pied
    add_rect(slide, Inches(0), Inches(6.8), SLIDE_W, Inches(0.7),
             RGBColor(0x0D, 0x1B, 0x35))
    add_text_box(slide,
                 "ISET  ·  Projet de Fin d'Études 2024–2025  ·  Merci pour votre attention 🙏",
                 Inches(0.5), Inches(6.85), Inches(12.33), Inches(0.45),
                 font_size=11, color=C_LIGHT_GRAY,
                 align=PP_ALIGN.CENTER)


# ─── MAIN ────────────────────────────────────────────────────────────────────
def build_presentation():
    prs = new_prs()

    print("🔨  Construction des slides...")
    slide_cover(prs)               ; print("  ✅  Slide 1  — Couverture")
    slide_problematique(prs)       ; print("  ✅  Slide 2  — Problématique")
    slide_types_travaux(prs)       ; print("  ✅  Slide 3  — Types de travaux")
    slide_variables_risque(prs)    ; print("  ✅  Slide 4  — Variables de risque")
    slide_niveaux_risque(prs)      ; print("  ✅  Slide 5  — Niveaux de risque")
    slide_architecture(prs)        ; print("  ✅  Slide 6  — Architecture système")
    slide_stack_tech(prs)          ; print("  ✅  Slide 7  — Stack technologique")
    slide_preprocessing(prs)       ; print("  ✅  Slide 8  — Prétraitement & Flags GC")
    slide_comparaison_modeles(prs) ; print("  ✅  Slide 9  — Comparaison modèles")
    slide_validation_croisee(prs)  ; print("  ✅  Slide 10 — Validation croisée")
    slide_feature_engineering(prs) ; print("  ✅  Slide 11 — Feature Engineering")
    slide_explainability(prs)      ; print("  ✅  Slide 12 — Explicabilité SHAP/LIME")
    slide_dashboard(prs)           ; print("  ✅  Slide 13 — Dashboard")
    slide_recommandations_gc(prs)  ; print("  ✅  Slide 14 — Reco. Opérationnelles")
    slide_recommandations_tech(prs); print("  ✅  Slide 15 — Reco. Techniques")
    slide_perspectives(prs)        ; print("  ✅  Slide 16 — Perspectives")
    slide_conclusion(prs)          ; print("  ✅  Slide 17 — Conclusion")

    out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "GC_Safety_AI_Presentation.pptx")
    prs.save(out_path)
    print(f"\n🎉  Présentation générée : {out_path}")
    print(f"    {len(prs.slides)} slides  ·  Format 16:9  ·  Thème dark professionnel")
    return out_path


if __name__ == "__main__":
    try:
        from pptx import Presentation as _chk
    except ImportError:
        print("📦  Installation de python-pptx…")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-pptx", "-q"])
        from pptx import Presentation

    build_presentation()
