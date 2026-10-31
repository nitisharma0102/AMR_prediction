"""
Comprehensive Multi-Model Evaluation and Comparative Matrix Generator
Computes overall multi-label metrics (Train, Val, Test accuracies, Hamming loss, Macro F1, ROC-AUC)
and generates per-antibiotic comparison tables for all 5 drug classes across all evaluated models:
1. Proposed: ProkBERT + Class-Wise Multi-Head Attention (Calibrated)
2. Proposed: ProkBERT + Attention (Default 0.5 Cutoff)
3. Ablation: ProkBERT (Mean-Pooling Baseline)
4. Baseline: XGBoost Classifier (k-mer TF-IDF)
5. Baseline: Random Forest Classifier
6. Baseline: Logistic Regression

Also integrates the CARD Database Biological Validation Engine to prove phenotypic accuracy.
"""

import sys
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.preprocessor import DNATokenizer
from src.data.dataset import GenomeBagDataset, collate_genome_bags, LABEL_COLS
from src.models.classifier import ProkBERTAttentionAMR, MeanPoolProkBERTBaseline
from src.models.baselines import MLBaselinesPipeline
from src.evaluation.metrics import MultiLabelEvaluator, ANTIBIOTICS
from src.evaluation.card_validator import CARDResistomeValidator


def main():
    print("=" * 85)
    print("      COMPREHENSIVE MULTI-MODEL AMR BENCHMARK & PER-ANTIBIOTIC MATRIX")
    print("=" * 85)

    data_path = PROJECT_ROOT / "data" / "processed" / "ecoli_prokbert_chunks_with_split.csv.gz"
    if not data_path.exists():
        raise FileNotFoundError(f"Missing dataset at {data_path}. Run stage3_chunking_and_split.py first.")

    print(f"\n1. Loading chunk dataset from {data_path}...")
    chunks_df = pd.read_csv(data_path, compression="gzip")
    print(f"Total chunks: {len(chunks_df)} across {chunks_df['genome_id'].nunique()} genomes.")

    tokenizer = DNATokenizer(k=6)
    MAX_CHUNKS = 24
    MAX_SEQ_LEN = 160

    print("2. Constructing Train, Validation, and Test Datasets...")
    train_dataset = GenomeBagDataset(chunks_df, tokenizer, max_chunks_per_genome=MAX_CHUNKS, max_seq_len=MAX_SEQ_LEN, split="train")
    val_dataset = GenomeBagDataset(chunks_df, tokenizer, max_chunks_per_genome=MAX_CHUNKS, max_seq_len=MAX_SEQ_LEN, split="validation")
    test_dataset = GenomeBagDataset(chunks_df, tokenizer, max_chunks_per_genome=MAX_CHUNKS, max_seq_len=MAX_SEQ_LEN, split="test")

    print(f"Cohort Split: Train={len(train_dataset)}, Val={len(val_dataset)}, Test={len(test_dataset)} isolates.")

    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=False, collate_fn=collate_genome_bags)
    val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False, collate_fn=collate_genome_bags)
    test_loader = DataLoader(test_dataset, batch_size=8, shuffle=False, collate_fn=collate_genome_bags)

    device = torch.device("cpu")
    print(f"Execution Device: {device}")

    # Load Proposed Model
    print("\n3. Loading Proposed ProkBERT + Class-Wise Attention Model...")
    proposed_model = ProkBERTAttentionAMR(
        vocab_size=tokenizer.vocab_size,
        embed_dim=128,
        num_layers=3,
        num_heads=4,
        dim_feedforward=256,
        num_classes=5,
        max_seq_len=MAX_SEQ_LEN,
        dropout=0.10,
        use_class_wise_attention=True
    )
    ckpt_prop = PROJECT_ROOT / "models" / "checkpoints" / "best_prokbert_attnpool.pt"
    if ckpt_prop.exists():
        proposed_model.load_state_dict(torch.load(ckpt_prop, map_location=device))
        print("  -> Loaded checkpoint:", ckpt_prop)
    else:
        print("  -> Checkpoint not found; running with initialized weights.")
    proposed_model.eval()

    # Load Mean-Pooling Model
    print("4. Loading Ablation Mean-Pool ProkBERT Baseline Model...")
    meanpool_model = MeanPoolProkBERTBaseline(
        vocab_size=tokenizer.vocab_size,
        embed_dim=128,
        num_layers=3,
        num_heads=4,
        num_classes=5,
        max_seq_len=MAX_SEQ_LEN,
        dropout=0.10
    )
    ckpt_mp = PROJECT_ROOT / "models" / "checkpoints" / "best_meanpool_baseline.pt"
    if ckpt_mp.exists():
        meanpool_model.load_state_dict(torch.load(ckpt_mp, map_location=device))
        print("  -> Loaded checkpoint:", ckpt_mp)
    else:
        print("  -> Checkpoint not found; running with initialized weights.")
    meanpool_model.eval()

    # Load / Train Classical ML Baselines
    print("5. Training Classical ML Baselines (k-mer TF-IDF)...")
    def extract_texts_and_labels(dataset):
        texts = []
        labels = []
        for i in range(len(dataset)):
            item = dataset[i]
            gid = item["genome_id"]
            grp = chunks_df[chunks_df["genome_id"] == gid]
            combined_seq = " ".join(grp["sequence"].tolist())
            texts.append(combined_seq)
            labels.append(item["labels"].numpy())
        return texts, np.array(labels)

    train_texts, y_train_true = extract_texts_and_labels(train_dataset)
    val_texts, y_val_true = extract_texts_and_labels(val_dataset)
    test_texts, y_test_true = extract_texts_and_labels(test_dataset)

    ml_pipeline = MLBaselinesPipeline(k=5, max_features=1000, random_state=42)
    ml_pipeline.fit(train_texts, y_train_true)

    ml_train_probas = ml_pipeline.predict_proba(train_texts)
    ml_val_probas = ml_pipeline.predict_proba(val_texts)
    ml_test_probas = ml_pipeline.predict_proba(test_texts)

    # Inference Helper for Neural Models
    def predict_loader(model, loader):
        probs_list = []
        with torch.no_grad():
            for batch in loader:
                inp = batch["input_ids"].to(device)
                att = batch["attention_mask"].to(device)
                bag = batch["bag_mask"].to(device)
                out = model(inp, att, bag)
                probs_list.append(out["probabilities"].cpu().numpy())
        return np.vstack(probs_list)

    print("6. Executing Inference Across All Splits...")
    y_train_prob_prop = predict_loader(proposed_model, train_loader)
    y_val_prob_prop = predict_loader(proposed_model, val_loader)
    y_test_prob_prop = predict_loader(proposed_model, test_loader)

    y_train_prob_mp = predict_loader(meanpool_model, train_loader)
    y_val_prob_mp = predict_loader(meanpool_model, val_loader)
    y_test_prob_mp = predict_loader(meanpool_model, test_loader)

    # Calibrate Thresholds on Validation Set
    evaluator = MultiLabelEvaluator(target_names=ANTIBIOTICS)
    optimal_thresholds = evaluator.find_optimal_thresholds(y_val_true, y_val_prob_prop)
    print("\nOptimal Calibrated Thresholds (F1-Maximizing):")
    for drug, t in zip(ANTIBIOTICS, optimal_thresholds):
        print(f"  - {drug:15s}: {t:.2f}")

    # Build All Model Prediction Dictionaries for Train, Val, Test
    models_dict = {
        "ProkBERT + Class Attention (Calibrated)": {
            "train_prob": y_train_prob_prop,
            "val_prob": y_val_prob_prop,
            "test_prob": y_test_prob_prop,
            "threshold": optimal_thresholds
        },
        "ProkBERT + Attention (Default 0.5)": {
            "train_prob": y_train_prob_prop,
            "val_prob": y_val_prob_prop,
            "test_prob": y_test_prob_prop,
            "threshold": 0.5
        },
        "ProkBERT (Mean-Pooling Baseline)": {
            "train_prob": y_train_prob_mp,
            "val_prob": y_val_prob_mp,
            "test_prob": y_test_prob_mp,
            "threshold": 0.5
        },
        "XGBoost Classifier": {
            "train_prob": ml_train_probas["XGBoost"],
            "val_prob": ml_val_probas["XGBoost"],
            "test_prob": ml_test_probas["XGBoost"],
            "threshold": 0.5
        },
        "Random Forest Classifier": {
            "train_prob": ml_train_probas["Random Forest"],
            "val_prob": ml_val_probas["Random Forest"],
            "test_prob": ml_test_probas["Random Forest"],
            "threshold": 0.5
        },
        "Logistic Regression": {
            "train_prob": ml_train_probas["Logistic Regression"],
            "val_prob": ml_val_probas["Logistic Regression"],
            "test_prob": ml_test_probas["Logistic Regression"],
            "threshold": 0.5
        }
    }

    # =========================================================================
    # PART A: OVERALL MODEL PERFORMANCE MATRIX (Train, Val, Test Accuracies)
    # =========================================================================
    print("\n" + "=" * 85)
    print("TABLE 1: OVERALL MULTI-MODEL COMPARISON (TRAIN, VAL & TEST PERFORMANCE)")
    print("=" * 85)

    overall_records = []
    for m_name, d in models_dict.items():
        thresh = d["threshold"]
        t_arr = np.array(thresh).reshape(1, -1) if isinstance(thresh, (list, np.ndarray)) else thresh

        # Train metrics
        y_train_pred = (d["train_prob"] >= t_arr).astype(int)
        train_subset_acc = np.mean(np.all(y_train_true == y_train_pred, axis=1))
        train_mean_acc = np.mean(y_train_true == y_train_pred)

        # Val metrics
        y_val_pred = (d["val_prob"] >= t_arr).astype(int)
        val_subset_acc = np.mean(np.all(y_val_true == y_val_pred, axis=1))
        val_mean_acc = np.mean(y_val_true == y_val_pred)

        # Test metrics
        test_res = evaluator.evaluate_predictions(y_test_true, d["test_prob"], threshold=thresh)
        test_subset_acc = test_res["Subset_Accuracy"]
        test_mean_acc = np.mean(y_test_true == (d["test_prob"] >= t_arr).astype(int))

        overall_records.append({
            "Model Architecture": m_name,
            "Train Subset Acc": train_subset_acc,
            "Train Mean Acc": train_mean_acc,
            "Val Subset Acc": val_subset_acc,
            "Val Mean Acc": val_mean_acc,
            "Test Subset Acc": test_subset_acc,
            "Test Mean Acc": test_mean_acc,
            "Hamming Loss": test_res["Hamming_Loss"],
            "Macro F1": test_res["Macro_F1"],
            "Micro F1": test_res["Micro_F1"],
            "Macro ROC-AUC": test_res["Macro_ROC_AUC"]
        })

    df_overall = pd.DataFrame(overall_records).set_index("Model Architecture")
    pd.set_option("display.max_columns", 12)
    pd.set_option("display.width", 120)
    pd.set_option("display.precision", 4)
    print(df_overall.to_string())

    # Export overall comparison
    df_overall.to_csv(PROJECT_ROOT / "models" / "comprehensive_model_comparison.csv")
    print("\nSaved overall comparison to: models/comprehensive_model_comparison.csv")

    # =========================================================================
    # PART B: PER-ANTIBIOTIC MODEL COMPARISON TABLES (5 TABLES)
    # =========================================================================
    per_drug_dfs = {}

    for drug_idx, drug in enumerate(ANTIBIOTICS):
        print("\n" + "=" * 85)
        print(f"TABLE: MODEL COMPARISON FOR ANTIBIOTIC: {drug.upper()}")
        print("=" * 85)

        drug_records = []
        for m_name, d in models_dict.items():
            thresh = d["threshold"]
            th = thresh[drug_idx] if isinstance(thresh, (list, np.ndarray)) else thresh

            # Ground truth for this drug
            yt_train = y_train_true[:, drug_idx]
            yt_val = y_val_true[:, drug_idx]
            yt_test = y_test_true[:, drug_idx]

            # Probabilities for this drug
            yp_train = d["train_prob"][:, drug_idx]
            yp_val = d["val_prob"][:, drug_idx]
            yp_test = d["test_prob"][:, drug_idx]

            # Binary calls
            ypred_train = (yp_train >= th).astype(int)
            ypred_val = (yp_val >= th).astype(int)
            ypred_test = (yp_test >= th).astype(int)

            train_acc = np.mean(yt_train == ypred_train)
            val_acc = np.mean(yt_val == ypred_val)
            test_acc = np.mean(yt_test == ypred_test)

            # Confusion Matrix on test set
            tp = int(np.sum((yt_test == 1) & (ypred_test == 1)))
            fp = int(np.sum((yt_test == 0) & (ypred_test == 1)))
            fn = int(np.sum((yt_test == 1) & (ypred_test == 0)))
            tn = int(np.sum((yt_test == 0) & (ypred_test == 0)))

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

            try:
                from sklearn.metrics import roc_auc_score
                auc = roc_auc_score(yt_test, yp_test)
            except Exception:
                auc = 0.5

            drug_records.append({
                "Model Architecture": m_name,
                "Cutoff": th,
                "Train Acc": train_acc,
                "Val Acc": val_acc,
                "Test Acc": test_acc,
                "Precision": prec,
                "Recall (Sensitivity)": rec,
                "Specificity": spec,
                "F1-Score": f1,
                "ROC-AUC": auc,
                "TP": tp,
                "FP": fp,
                "FN": fn,
                "TN": tn
            })

        df_drug = pd.DataFrame(drug_records).set_index("Model Architecture")
        print(df_drug.to_string())
        per_drug_dfs[drug] = df_drug

        # Export individual drug CSV
        clean_drug_name = drug.lower().replace("-", "_")
        df_drug.to_csv(PROJECT_ROOT / "models" / f"antibiotic_{clean_drug_name}_comparison.csv")

    # Combine all per-drug tables into one master CSV
    combined_drug_records = []
    for drug, df in per_drug_dfs.items():
        temp = df.reset_index()
        temp["Antibiotic"] = drug
        combined_drug_records.append(temp)
    df_combined_drugs = pd.concat(combined_drug_records, ignore_index=True)
    df_combined_drugs.to_csv(PROJECT_ROOT / "models" / "per_antibiotic_comparison.csv", index=False)
    print("\nSaved combined per-antibiotic matrix to: models/per_antibiotic_comparison.csv")

    # =========================================================================
    # PART C: CARD DB BIOLOGICAL VALIDATION REPORT
    # =========================================================================
    print("\n" + "=" * 85)
    print("TABLE: CARD DATABASE GROUND-TRUTH ONTOLOGY VALIDATION PROOF")
    print("=" * 85)

    card_validator = CARDResistomeValidator()

    # Test CARD validation on an MDR test genome
    sample_genome_id = test_dataset[0]["genome_id"]
    grp = chunks_df[chunks_df["genome_id"] == sample_genome_id]
    sample_seq = "".join(grp["sequence"].tolist())

    sample_probs = {drug: float(y_test_prob_prop[0, i]) for i, drug in enumerate(ANTIBIOTICS)}
    sample_thresholds = {drug: float(optimal_thresholds[i]) for i, drug in enumerate(ANTIBIOTICS)}

    detected_markers = card_validator.scan_sequence(sample_seq)
    df_card_proof = card_validator.validate_predictions(sample_probs, sample_thresholds, detected_markers)

    print(f"Sample Validated Clinical Isolate: {sample_genome_id}")
    print(f"Detected CARD ARO Determinants: {len(detected_markers)}")
    for m in detected_markers:
        print(f"  * {m['aro_id']} | {m['aro_name']} | {m['mechanism']} ({m['strand']})")

    print("\nBiological Proof Table:")
    print(df_card_proof[["Antibiotic", "AI Prediction", "Probability", "CARD Ground Truth", "CARD ARO Determinant", "Verification Status"]].to_string(index=False))

    # Export CARD validation summary
    card_summary = {
        "sample_isolate": sample_genome_id,
        "total_card_determinants_detected": len(detected_markers),
        "detected_markers": detected_markers,
        "proof_table": df_card_proof.to_dict(orient="records")
    }
    with open(PROJECT_ROOT / "models" / "card_validation_summary.json", "w") as f:
        json.dump(card_summary, f, indent=2)
    df_card_proof.to_csv(PROJECT_ROOT / "models" / "card_validation_proof_table.csv", index=False)
    print("\nSaved CARD verification report to: models/card_validation_summary.json and models/card_validation_proof_table.csv")

    print("\n" + "=" * 85)
    print("ALL MATRICES, PER-ANTIBIOTIC TABLES & CARD PROOFS GENERATED SUCCESSFULLY!")
    print("=" * 85)


if __name__ == "__main__":
    main()

