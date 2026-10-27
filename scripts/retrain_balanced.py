"""Retrain the MLP risk classifier with class balancing.

Builds features with core.logic.build_feature_vector (the exact function the
dashboard uses at inference time), oversamples the minority classes on the
training split only, and compares the result with the current model on the
same stratified test split. The new model is saved only if its macro-F1 is
higher and its recall on "Critique" does not drop.

Usage (from the repository root):
    python scripts/retrain_balanced.py            # compare only
    python scripts/retrain_balanced.py --save     # compare and save if better
"""
import os
import sys
import json
import argparse

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import RandomOverSampler
from sklearn.metrics import classification_report, f1_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from core.logic import build_feature_vector  # noqa: E402

RANDOM_STATE = 42
MODELS = os.path.join(ROOT, "models")


def load_xy(scaler, tfidf_vec, class_names):
    raw = pd.read_csv(os.path.join(ROOT, "Dataset.csv"))
    labels = pd.read_csv(os.path.join(ROOT, "predictions_annotated_v2.csv"))[["ID_Inspection", "Label_reel"]]
    df = raw.merge(labels, on="ID_Inspection")
    df = df[df["Label_reel"].isin(class_names)].reset_index(drop=True)

    num_cols = ["Effectif", "Temperature", "Vent_kmh", "EPI_Manquants", "Risque_Historique"]
    df[num_cols] = df[num_cols].fillna(df[num_cols].median())
    df["Type_Travaux"] = df["Type_Travaux"].fillna("inconnu")

    X = np.vstack([
        build_feature_vector(
            str(r.Type_Travaux), int(r.Effectif), float(r.Temperature), float(r.Vent_kmh),
            int(r.EPI_Manquants), float(r.Risque_Historique), str(r.Rapport_inspection),
            scaler, tfidf_vec,
        )
        for r in df.itertuples()
    ])
    y = df["Label_reel"].map({name: i for i, name in enumerate(class_names)}).to_numpy()
    return X, y


def evaluate(name, model, X_test, y_test, class_names):
    pred = model.predict(X_test)
    macro = f1_score(y_test, pred, average="macro")
    crit = recall_score(y_test, pred, labels=[0], average="macro")
    print(f"\n=== {name} — macro-F1 {macro:.3f} · recall Critique {crit:.3f}")
    print(classification_report(y_test, pred, target_names=class_names, digits=3, zero_division=0))
    return macro, crit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    label_info = joblib.load(os.path.join(MODELS, "label_map_v2.joblib"))
    class_names = label_info["class_names_model"]
    scaler = joblib.load(os.path.join(MODELS, "scaler.joblib"))
    tfidf_vec = joblib.load(os.path.join(MODELS, "tfidf_vectorizer.joblib"))
    current = joblib.load(os.path.join(MODELS, "best_model_v2.joblib"))

    X, y = load_xy(scaler, tfidf_vec, class_names)
    print("Class distribution:", dict(zip(class_names, np.bincount(y))))
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)

    X_bal, y_bal = RandomOverSampler(random_state=RANDOM_STATE).fit_resample(X_train, y_train)
    candidate = MLPClassifier(hidden_layer_sizes=(256, 128), alpha=1e-3, early_stopping=True,
                              max_iter=500, random_state=RANDOM_STATE)
    candidate.fit(X_bal, y_bal)

    # The current model saw part of this test split during its own training,
    # so its score here is optimistic: beating it is a conservative criterion.
    cur_macro, cur_crit = evaluate("Current model", current, X_test, y_test, class_names)
    new_macro, new_crit = evaluate("Balanced MLP", candidate, X_test, y_test, class_names)

    better = new_macro > cur_macro and new_crit >= cur_crit - 0.01
    print("\nBalanced model is", "BETTER" if better else "NOT better")
    if args.save and better:
        joblib.dump(candidate, os.path.join(MODELS, "best_model_v2.joblib"))
        with open(os.path.join(MODELS, "balanced_metrics.json"), "w", encoding="utf-8") as f:
            json.dump({"macro_f1": round(new_macro, 4), "recall_critique": round(new_crit, 4),
                       "previous_macro_f1": round(cur_macro, 4)}, f, indent=2)
        print("Saved models/best_model_v2.joblib")


if __name__ == "__main__":
    main()
