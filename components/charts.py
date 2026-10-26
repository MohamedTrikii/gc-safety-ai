import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Palette de couleurs Premium
PREMIUM_PALETTE = {
    "Critique": "#ef4444",
    "Élevé": "#f59e0b",
    "Moyen": "#10b981",
    "Faible": "#3b82f6",
    "Primary": "#4f8ef7",
    "Secondary": "#6366f1",
    "Grid": "rgba(255, 255, 255, 0.1)",
    "Text": "#f8fafc"
}

def plot_prediction_confidence(proba: np.ndarray, class_names: list):
    """Graphe de barres horizontales pour les probabilités (Plotly)."""
    df = pd.DataFrame({
        "Risque": class_names,
        "Probabilité": proba
    })
    
    # Matching colors to classes
    colors = [PREMIUM_PALETTE.get(name, PREMIUM_PALETTE["Primary"]) for name in class_names]
    
    fig = px.bar(
        df, x="Probabilité", y="Risque", 
        orientation='h',
        text_auto='.1%',
        color="Risque",
        color_discrete_map=PREMIUM_PALETTE,
        template="plotly_dark"
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20),
        height=300,
        xaxis=dict(range=[0, 1.1], showgrid=True, gridcolor=PREMIUM_PALETTE["Grid"]),
        yaxis=dict(showgrid=False)
    )
    return fig

def plot_historical_distribution(df: pd.DataFrame):
    """Distribution des risques historiques (Plotly)."""
    if df.empty or "Prediction" not in df.columns:
        return None
        
    counts = df["Prediction"].value_counts().reset_index()
    counts.columns = ["Risque", "Nombre"]
    
    fig = px.bar(
        counts, x="Risque", y="Nombre",
        color="Risque",
        color_discrete_map=PREMIUM_PALETTE,
        template="plotly_dark",
        text_auto=True
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="",
        yaxis_title="Nombre d'inspections",
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor=PREMIUM_PALETTE["Grid"])
    )
    return fig

def plot_risk_heatmap(df: pd.DataFrame):
    """Heatmap descriptive de risque (Plotly)."""
    if df.empty or "Type_Travaux" not in df.columns or "Prediction" not in df.columns:
        return None
        
    pivot = pd.crosstab(df["Type_Travaux"], df["Prediction"])
    # Order columns
    ordered = [c for c in ["Critique", "Élevé", "Moyen", "Faible"] if c in pivot.columns]
    pivot = pivot.reindex(columns=ordered)
    
    fig = px.imshow(
        pivot,
        labels=dict(x="Niveau de Risque", y="Type de Travaux", color="Nombre"),
        color_continuous_scale="RdYlGn_r",
        text_auto=True,
        template="plotly_dark"
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20),
        coloraxis_showscale=False
    )
    return fig

def plot_feature_importance_plotly(rf_model, feature_names: list, top_n: int = 15):
    """Importance des variables (Plotly)."""
    importances = rf_model.feature_importances_
    # Adjust feature names if they don't match length
    names = feature_names[:len(importances)]
    
    df = pd.DataFrame({
        "Feature": names,
        "Importance": importances
    }).nlargest(top_n, "Importance")
    
    # Sort for display
    df = df.sort_values("Importance", ascending=True)
    
    fig = px.bar(
        df, x="Importance", y="Feature",
        orientation='h',
        color="Importance",
        color_continuous_scale="Blues",
        template="plotly_dark"
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20),
        coloraxis_showscale=False,
        xaxis_title="Importance (Gini)",
        yaxis_title=""
    )
    return fig

def plot_model_comparison_plotly(metrics_dict: dict):
    """Comparaison de performance des modèles (Plotly)."""
    data = []
    for name, m in metrics_dict.items():
        data.append({"Modèle": name, "Métrique": "Accuracy", "Score": m["acc"]})
        data.append({"Modèle": name, "Métrique": "F1-Score", "Score": m["f1"]})

    df = pd.DataFrame(data)

    fig = px.bar(
        df, x="Modèle", y="Score",
        color="Métrique",
        barmode="group",
        template="plotly_dark",
        color_discrete_sequence=[PREMIUM_PALETTE["Primary"], PREMIUM_PALETTE["Moyen"]],
        text_auto='.1%'
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis=dict(range=[0.75, 1.0], gridcolor=PREMIUM_PALETTE["Grid"]),
        xaxis_title=""
    )
    return fig


def plot_confidence_gauge(conf: float, label: str):
    """Gauge chart circulaire pour la confiance de prédiction."""
    color_map = {
        "Critique": "#ef4444", "Élevé": "#f59e0b",
        "Moyen": "#10b981",    "Faible": "#4f8ef7",
    }
    color = color_map.get(label, "#4f8ef7")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=conf * 100,
        number={"suffix": "%", "font": {"size": 28, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#475569",
                     "tickfont": {"color": "#64748b", "size": 11}},
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  40], "color": "rgba(255,255,255,0.03)"},
                {"range": [40, 70], "color": "rgba(255,255,255,0.06)"},
                {"range": [70, 100], "color": "rgba(255,255,255,0.09)"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.8,
                "value": conf * 100,
            },
        },
        title={"text": "Confiance IA", "font": {"size": 13, "color": "#64748b"}},
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
        height=200,
        font={"color": "#e2e8f0"},
    )
    return fig


def plot_risk_radar(inputs_dict: dict):
    """Graphe radar (spider) des facteurs de risque normalisés."""
    vent   = min(1.0, inputs_dict.get("vent",     0) / 120)
    temp   = min(1.0, abs(inputs_dict.get("temp", 22) - 22) / 30)
    epi    = min(1.0, inputs_dict.get("epi",      0) / 10)
    eff    = min(1.0, inputs_dict.get("effectif", 0) / 100)
    hist   = inputs_dict.get("hist", 0)

    categories = ["Vent", "Température", "EPI", "Effectif", "Hist. Risque"]
    values     = [vent, temp, epi, eff, hist]
    values_closed = values + [values[0]]
    cats_closed   = categories + [categories[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=cats_closed,
        fill="toself",
        fillcolor="rgba(79,142,247,0.18)",
        line=dict(color="#4f8ef7", width=2),
        name="Profil de Risque",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True, range=[0, 1],
                tickfont=dict(size=9, color="#475569"),
                gridcolor="rgba(255,255,255,0.08)",
                linecolor="rgba(255,255,255,0.05)",
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color="#94a3b8"),
                gridcolor="rgba(255,255,255,0.06)",
                linecolor="rgba(255,255,255,0.05)",
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(l=30, r=30, t=30, b=30),
        height=260,
    )
    return fig


def plot_trend_timeline(df: pd.DataFrame):
    """Graphe d'évolution temporelle du risque (area chart)."""
    if df.empty or "Prediction" not in df.columns:
        return None

    # Si pas de colonne date, utiliser l'index
    if "Date" not in df.columns:
        df = df.copy()
        df["Date"] = range(len(df))

    counts = (
        df.groupby(["Date", "Prediction"])
        .size()
        .reset_index(name="Nombre")
    )
    order  = ["Critique", "Élevé", "Moyen", "Faible"]
    colors = ["#ef4444", "#f59e0b", "#10b981", "#4f8ef7"]

    fig = go.Figure()
    for lvl, col in zip(order, colors):
        sub = counts[counts["Prediction"] == lvl]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["Date"], y=sub["Nombre"],
            mode="lines",
            name=lvl,
            stackgroup="one",
            line=dict(color=col, width=1.5),
            fillcolor=col.replace("#", "rgba(").rstrip(")") + ",0.25)"
            if col.startswith("#") else col,
        ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8"),
        ),
        xaxis=dict(showgrid=False, color="#475569"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", color="#475569"),
        height=280,
    )
    return fig
