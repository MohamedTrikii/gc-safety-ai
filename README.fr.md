# 🏗️ GC Safety AI — Prédiction du risque sur chantier

> Prédit le niveau de risque d'un chantier (**Critique / Élevé / Moyen**) à partir des mesures du site **et** du texte libre du rapport d'inspection, explique chaque prédiction et déclenche des alertes réglementaires en temps réel.

🇬🇧 [English version](README.md)

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8-F7931E?logo=scikitlearn&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-3.2-189FDD)
![SHAP](https://img.shields.io/badge/Explicabilité-SHAP%20·%20LIME-8A2BE2)
![Streamlit](https://img.shields.io/badge/Streamlit-1.56-FF4B4B?logo=streamlit&logoColor=white)

![Prédiction](docs/screenshots/prediction.png)

---

## ✨ Fonctionnalités

- **Modèle hybride** : variables structurées (effectif, température, vent, EPI manquants, historique de risque) + **NLP** sur le rapport d'inspection (TF-IDF, extraction par regex de la vitesse du vent, de la température, du nombre d'EPI, des mots d'urgence).
- **5 modèles comparés** : MLP, XGBoost (optimisé), Dual-Stream, Random Forest, régression logistique ; découpage stratifié 80/20, `random_state=42`.
- **Explicabilité** : SHAP et LIME, avec une interprétation « génie civil » de chaque variable importante.
- **Alertes réglementaires en temps réel** : seuils de vent, température, EPI et effectif vérifiés pendant la saisie.
- **Tableau de bord interactif** : distribution du risque, importance des variables, carte de chaleur par type de travaux, comparaison des modèles, matrice de confusion, prédiction par lot (CSV) et export.
- **Tests de robustesse** : injection de bruit et analyse des erreurs critiques (faux « sûr »).

## 📊 Résultats (jeu de test)

| Modèle | Accuracy | F1 (pondéré) |
|---|---|---|
| **Réseau de neurones MLP** | **0,890** | **0,888** |
| XGBoost (optimisé) | 0,885 | 0,885 |
| Dual Stream | 0,890 | 0,884 |
| Random Forest | 0,865 | 0,863 |
| Régression logistique | 0,850 | 0,865 |

| Courbes ROC | Matrices de confusion |
|---|---|
| ![ROC](docs/figures/fig_3_5_courbes_roc.png) | ![Confusion](docs/figures/fig_3_4_matrices_confusion.png) |

## 🖥️ Tableau de bord

| Formulaire de prédiction | Analyses |
|---|---|
| ![Accueil](docs/screenshots/home.png) | ![Tableau de bord](docs/screenshots/dashboard.png) |

## 🚀 Installation

```bash
git clone https://github.com/MohamedTrikii/gc-safety-ai.git
cd gc-safety-ai
python -m venv .venv && .venv\Scripts\activate      # Linux/macOS : source .venv/bin/activate
pip install -r requirements.txt
streamlit run app_dashboard.py
```

Les modèles entraînés sont fournis dans [`models/`](models/) : l'application se lance immédiatement.
Pour réentraîner, exécutez les notebooks dans l'ordre : `preprocessing_chantier.ipynb` → `chantier_risque_prediction.ipynb`.

## 📁 Structure

```
├── app_dashboard.py                 # application Streamlit (point d'entrée)
├── core/ · components/ · pages/     # configuration et règles métier, composants UI, pages
├── preprocessing_chantier.ipynb     # nettoyage, NLP, feature engineering
├── chantier_risque_prediction.ipynb # entraînement, évaluation, SHAP/LIME, export
├── projet.ipynb                     # expériences d'ensemble learning (stacking, bagging, voting)
├── models/                          # modèles entraînés (joblib)
├── Dataset.csv                      # 1 000 inspections (données structurées + texte du rapport)
├── docs/                            # cahier des charges, figures, captures, présentation
└── scripts/                         # generate_presentation.py (présentation) · retrain_balanced.py (étude de rééquilibrage)
```

## ⚠️ Limites et suite

- Les étiquettes sont **très déséquilibrées** (877 *Critique*, 103 *Élevé*, 20 *Moyen*). Résultats par classe du MLP déployé sur le jeu de test : rappel de **0,99** sur *Critique*, mais seulement 0,24 sur *Élevé* et 0,25 sur *Moyen*.
- **Étude de rééquilibrage** ([`scripts/retrain_balanced.py`](scripts/retrain_balanced.py)) : sur-échantillonnage, régression logistique et forêt aléatoire pondérées, ajustement du seuil, comparés sur le même découpage. Une régression logistique pondérée obtient un meilleur macro-F1 (0,67 contre 0,55) et repère la plupart des cas *Élevé*, mais rate 14 % des chantiers *Critique*. Rater un chantier critique étant l'erreur la plus coûteuse, le modèle à fort rappel est conservé.
- Le modèle s'appuie beaucoup sur le texte du rapport : le tableau de bord avertit quand le rapport est vide.
- 1 000 inspections seulement : résultats à confirmer sur des données réelles de chantier.

## 👤 Auteur

**Mohamed Triki** — [GitHub](https://github.com/MohamedTrikii)
