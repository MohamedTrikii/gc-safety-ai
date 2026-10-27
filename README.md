# 🏗️ GC Safety AI — Construction-Site Risk Prediction

> Predicts the safety-risk level of a construction site (**Critique / Élevé / Moyen**) from site measurements **and** the free-text inspection report, explains each prediction, and raises regulatory alerts in real time.

🇫🇷 [Version française](README.fr.md)

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8-F7931E?logo=scikitlearn&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-3.2-189FDD)
![SHAP](https://img.shields.io/badge/Explainability-SHAP%20·%20LIME-8A2BE2)
![Streamlit](https://img.shields.io/badge/Streamlit-1.56-FF4B4B?logo=streamlit&logoColor=white)

![Prediction](docs/screenshots/prediction.png)

---

## ✨ Features

- **Hybrid model** — structured features (workforce, temperature, wind, missing PPE, risk history) + **NLP** on the inspection report (TF-IDF, regex extraction of wind speed, temperature, PPE count, urgency keywords).
- **5 models compared** — MLP, XGBoost (tuned), Dual-Stream, Random Forest, Logistic Regression; stratified 80/20 split, `random_state=42`.
- **Explainability** — SHAP and LIME, plus a civil-engineering reading of each important feature.
- **Real-time regulatory alerts** — wind, temperature, PPE and workforce thresholds checked as you type.
- **Interactive dashboard** — risk distribution, feature importance, heat-map by work type, model comparison, confusion matrix, CSV batch prediction and export.
- **Robustness tests** — noise injection and analysis of critical errors (false "safe" predictions).

## 📊 Results (test set)

| Model | Accuracy | F1 (weighted) |
|---|---|---|
| **MLP Neural Network** | **0.890** | **0.888** |
| XGBoost (tuned) | 0.885 | 0.885 |
| Dual Stream | 0.890 | 0.884 |
| Random Forest | 0.865 | 0.863 |
| Logistic Regression | 0.850 | 0.865 |

| ROC curves | Confusion matrices |
|---|---|
| ![ROC](docs/figures/fig_3_5_courbes_roc.png) | ![Confusion](docs/figures/fig_3_4_matrices_confusion.png) |

## 🖥️ Dashboard

| Prediction form | Analytics |
|---|---|
| ![Home](docs/screenshots/home.png) | ![Dashboard](docs/screenshots/dashboard.png) |

## 🚀 Getting started

```bash
git clone https://github.com/MohamedTrikii/gc-safety-ai.git
cd gc-safety-ai
python -m venv .venv && .venv\Scripts\activate      # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app_dashboard.py
```

The trained models are included in [`models/`](models/), so the app runs immediately.
To retrain, run the notebooks in order: `preprocessing_chantier.ipynb` → `chantier_risque_prediction.ipynb`.

## 📁 Project structure

```
├── app_dashboard.py                 # Streamlit app (entry point)
├── core/ · components/ · pages/     # config & business rules, UI helpers, page modules
├── preprocessing_chantier.ipynb     # cleaning, NLP, feature engineering
├── chantier_risque_prediction.ipynb # training, evaluation, SHAP/LIME, export
├── projet.ipynb                     # ensemble-learning experiments (stacking, bagging, voting)
├── models/                          # trained models (joblib)
├── Dataset.csv                      # 1,000 inspections (structured data + report text)
├── docs/                            # specification, figures, screenshots, slides
└── scripts/                         # generate_presentation.py (slides) · retrain_balanced.py (class-balancing study)
```

## ⚠️ Limitations & next steps

- The labels are **heavily imbalanced** (877 *Critique*, 103 *Élevé*, 20 *Moyen*). Per-class results of the deployed MLP on the test split: recall **0.99** on *Critique*, but only 0.24 on *Élevé* and 0.25 on *Moyen*.
- **Balancing study** ([`scripts/retrain_balanced.py`](scripts/retrain_balanced.py)): oversampling, class-weighted logistic regression / random forest and threshold tuning were compared on the same split. A weighted logistic regression reaches a better macro-F1 (0.67 vs 0.55) and catches most *Élevé* cases, but misses 14 % of *Critique* sites. Since missing a critical site is the costliest error, the high-recall model is kept.
- The model relies heavily on the report text: the dashboard warns when the report is empty.
- 1,000 inspections only — results should be confirmed on real site data.

## 👤 Author

**Mohamed Triki** — [GitHub](https://github.com/MohamedTrikii)
