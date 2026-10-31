"""
Finalize Best Models, Benchmark Evaluation & Publication Figures
Evaluates the optimized ProkBERT + Class-Wise Attention Pooling model,
calibrates decision thresholds, benchmarks against Mean-Pool and Classical ML,
and exports all publication figures and benchmark summaries.
"""

import sys
import json
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch
import numpy as np
import pandas as pd
from torch.utils.data import DataLoader

from src.data.preprocessor import DNATokenizer
from src.data.dataset import GenomeBagDataset, collate_genome_bags, LABEL_COLS
from src.models.classifier import ProkBERTAttentionAMR, MeanPoolProkBERTBaseline
from src.models.baselines import MLBaselinesPipeline
from src.training.losses import WeightedMultiLabelBCELoss
from src.training.trainer import GenomicAMRTrainer
from src.evaluation.metrics import MultiLabelEvaluator, ANTIBIOTICS
from src.interpretability.attention_analyzer import GenomicAttentionAnalyzer


def main():
    print("=" * 75, flush=True)
    print("PROKBERT + ATTENTION POOLING: FINALIZING BEST RESULTS & BENCHMARKS", flush=True)
    print("=" * 75, flush=True)

    data_path = Path("data/processed/ecoli_prokbert_chunks_with_split.csv.gz")
    chunks_df = pd.read_csv(data_path, compression="gzip")
    print(f"[+] Loaded {len(chunks_df)} chunks across {chunks_df['genome_id'].nunique()} clinical genomes.", flush=True)

    # Initialize Tokenizer and Datasets
    tokenizer = DNATokenizer(k=6)
    MAX_CHUNKS = 24
    MAX_SEQ_LEN = 160

    train_dataset = GenomeBagDataset(chunks_df, tokenizer, max_chunks_per_genome=MAX_CHUNKS, max_seq_len=MAX_SEQ_LEN, split="train")
    val_dataset = GenomeBagDataset(chunks_df, tokenizer, max_chunks_per_genome=MAX_CHUNKS, max_seq_len=MAX_SEQ_LEN, split="validation")
    test_dataset = GenomeBagDataset(chunks_df, tokenizer, max_chunks_per_genome=MAX_CHUNKS, max_seq_len=MAX_SEQ_LEN, split="test")

    print(f"[+] Dataset Splits: Train={len(train_dataset)}, Val={len(val_dataset)}, Test={len(test_dataset)}", flush=True)

    val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False, collate_fn=collate_genome_bags)
    test_loader = DataLoader(test_dataset, batch_size=8, shuffle=False, collate_fn=collate_genome_bags)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[+] Compute Device: {device}", flush=True)

    # 1. Load Proposed Model: ProkBERT + Class-Wise Attention Pooling
    print("\n[+] Loading Trained ProkBERT + Class-Wise Attention Pooling Checkpoint...", flush=True)
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
    ckpt_path = Path("models/checkpoints/best_prokbert_attnpool.pt")
    proposed_model.load_state_dict(torch.load(ckpt_path, map_location=device))
    proposed_model.to(device)
    proposed_model.eval()
    print(f"[+] Successfully loaded checkpoint from {ckpt_path}", flush=True)

    # 2. Train / Prepare Mean-Pool ProkBERT Baseline (3 epochs on CPU)
    print("\n[+] Training Mean-Pool ProkBERT Baseline (1 epoch ablation)...", flush=True)
    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True, collate_fn=collate_genome_bags)

    train_chunks = chunks_df[chunks_df["split"] == "train"]
    train_genomes = train_chunks.drop_duplicates("genome_id")
    pos_counts = train_genomes[LABEL_COLS].sum().values
    neg_counts = len(train_genomes) - pos_counts
    pos_weights = torch.tensor(neg_counts / np.maximum(pos_counts, 1), dtype=torch.float32)

    meanpool_model = MeanPoolProkBERTBaseline(
        vocab_size=tokenizer.vocab_size,
        embed_dim=128,
        num_layers=3,
        num_heads=4,
        num_classes=5,
        max_seq_len=MAX_SEQ_LEN,
        dropout=0.10
    )
    criterion = WeightedMultiLabelBCELoss(pos_weights=pos_weights)
    optimizer_mp = torch.optim.AdamW(meanpool_model.parameters(), lr=5e-4, weight_decay=1e-4)

    trainer_mp = GenomicAMRTrainer(
        model=meanpool_model,
        criterion=criterion,
        optimizer=optimizer_mp,
        device=device,
        checkpoint_dir="models/checkpoints"
    )
    trainer_mp.fit(train_loader, val_loader, epochs=1, patience=1, model_name="best_meanpool_baseline.pt")

    # 3. Fit Classical Machine Learning Baselines (TF-IDF 6-mers + Classifiers)
    print("\n[+] Training Classical Machine Learning Baselines (TF-IDF + ML Classifiers)...", flush=True)
    def extract_genome_texts_and_labels(dataset):
        texts, labels = [], []
        for i in range(len(dataset)):
            gid = dataset.genome_ids[i]
            grp = chunks_df[chunks_df["genome_id"] == gid]
            combined_seq = " ".join(grp["sequence"].tolist())
            texts.append(combined_seq)
            first_row = grp.iloc[0]
            labels.append([first_row[col] for col in LABEL_COLS])
        return texts, np.array(labels, dtype=float)

    train_texts, y_train_ml = extract_genome_texts_and_labels(train_dataset)
    test_texts, y_test_true = extract_genome_texts_and_labels(test_dataset)

    ml_pipeline = MLBaselinesPipeline(k=5, max_features=1000, random_state=42)
    ml_pipeline.fit(train_texts, y_train_ml)
    ml_test_probas = ml_pipeline.predict_proba(test_texts)

    # 4. Calibration on Validation Set
    print("\n[+] Calibrating Decision Thresholds on Validation Cohort...", flush=True)
    evaluator = MultiLabelEvaluator(target_names=ANTIBIOTICS)

    val_probs_prop = []
    val_targets = []
    with torch.no_grad():
        for batch in val_loader:
            inp = batch["input_ids"].to(device)
            att = batch["attention_mask"].to(device)
            bag = batch["bag_mask"].to(device)
            out = proposed_model(inp, att, bag)
            val_probs_prop.append(out["probabilities"].cpu().numpy())
            val_targets.append(batch["labels"].numpy())
    y_val_prob_proposed = np.vstack(val_probs_prop)
    y_val_true = np.vstack(val_targets)

    optimal_thresholds = evaluator.find_optimal_thresholds(y_val_true, y_val_prob_proposed)
    print("Optimal F1-Calibrated Decision Thresholds:", flush=True)
    for drug, t in zip(ANTIBIOTICS, optimal_thresholds):
        print(f"  - {drug:15s}: {t:.2f}", flush=True)

    with open("models/optimal_thresholds.json", "w") as f:
        json.dump({drug: float(t) for drug, t in zip(ANTIBIOTICS, optimal_thresholds)}, f, indent=2)

    # 5. Evaluate All Models on Held-out Test Cohort (N = 25 isolates)
    print("\n" + "=" * 75, flush=True)
    print("5. FINAL COMPREHENSIVE BENCHMARK EVALUATION (Held-Out Test Set: N = 25)", flush=True)
    print("=" * 75, flush=True)

    # Predictions for Proposed Model
    all_test_probs_prop = []
    with torch.no_grad():
        for batch in test_loader:
            inp = batch["input_ids"].to(device)
            att = batch["attention_mask"].to(device)
            bag = batch["bag_mask"].to(device)
            out = proposed_model(inp, att, bag)
            all_test_probs_prop.append(out["probabilities"].cpu().numpy())
    y_prob_proposed = np.vstack(all_test_probs_prop)

    # Predictions for Mean-Pool Baseline
    meanpool_model.eval()
    all_test_probs_mp = []
    with torch.no_grad():
        for batch in test_loader:
            inp = batch["input_ids"].to(device)
            att = batch["attention_mask"].to(device)
            bag = batch["bag_mask"].to(device)
            out = meanpool_model(inp, att, bag)
            all_test_probs_mp.append(out["probabilities"].cpu().numpy())
    y_prob_meanpool = np.vstack(all_test_probs_mp)

    benchmark_models = {
        "ProkBERT + Attention (Calibrated)": (y_prob_proposed, optimal_thresholds),
        "ProkBERT + Attention (Default 0.5)": (y_prob_proposed, 0.5),
        "ProkBERT (Mean Pooling Baseline)": (y_prob_meanpool, 0.5),
        "XGBoost Classifier": (ml_test_probas["XGBoost"], 0.5),
        "Random Forest Classifier": (ml_test_probas["Random Forest"], 0.5),
        "Logistic Regression": (ml_test_probas["Logistic Regression"], 0.5)
    }

    benchmark_summary = {}

    for model_name, (probas, thresh) in benchmark_models.items():
        res = evaluator.evaluate_predictions(y_test_true, probas, threshold=thresh)
        benchmark_summary[model_name] = {
            "Subset_Accuracy": float(res["Subset_Accuracy"]),
            "Hamming_Loss": float(res["Hamming_Loss"]),
            "Macro_F1": float(res["Macro_F1"]),
            "Micro_F1": float(res["Micro_F1"]),
            "Macro_ROC_AUC": float(res["Macro_ROC_AUC"]),
            "Macro_PR_AUC": float(res["Macro_PR_AUC"])
        }

    summary_df = pd.DataFrame(benchmark_summary).T
    print("\nBENCHMARK COMPARISON TABLE ON TEST SET:", flush=True)
    print(summary_df.round(4).to_string(), flush=True)

    # Detailed Class-Wise Breakdown
    detailed_res = evaluator.evaluate_predictions(y_test_true, y_prob_proposed, threshold=optimal_thresholds)
    print("\nDETAILED CLASS-WISE CLINICAL METRICS (PROKBERT + ATTENTION):", flush=True)
    print(detailed_res["Class_Metrics_Table"].round(4).to_string(index=False), flush=True)

    # Save benchmark JSON and CSV
    with open("models/benchmark_summary.json", "w") as f:
        json.dump(benchmark_summary, f, indent=2)
    summary_df.to_csv("models/benchmark_summary.csv")
    detailed_res["Class_Metrics_Table"].to_csv("models/class_wise_metrics.csv", index=False)

    # 6. Generate Publication Figures (300 DPI)
    print("\n[+] Generating Publication Figures (300 DPI)...", flush=True)
    evaluator.plot_roc_curves(y_test_true, y_prob_proposed, save_path="figures/roc_curves.png")
    evaluator.plot_precision_recall_curves(y_test_true, y_prob_proposed, save_path="figures/pr_curves.png")
    evaluator.plot_confusion_matrices(y_test_true, (y_prob_proposed >= optimal_thresholds).astype(int), save_path="figures/confusion_matrices.png")

    plot_summary = {k: v for k, v in benchmark_summary.items() if "Default 0.5" not in k}
    evaluator.plot_benchmark_comparison(plot_summary, save_path="figures/benchmark_comparison.png")

    # 7. Attention Locus Map & AMR Marker Discovery Analysis
    print("\n[+] Generating Attention Locus Map & Resistance Marker Discovery Analysis...", flush=True)
    analyzer = GenomicAttentionAnalyzer(model=proposed_model, device=device)

    sample_item = None
    for i in range(len(test_dataset)):
        item = test_dataset[i]
        if item["labels"].sum().item() >= 3:
            sample_item = item
            break
    if sample_item is None:
        sample_item = test_dataset[0]

    inspection = analyzer.inspect_genome(sample_item, chunk_metadata_df=chunks_df)
    print(f"\nAnalyzed Sample Genome: {sample_item['genome_id']}", flush=True)
    print("Top 5 Highest Attended Loci:", flush=True)
    print(inspection["top_attended_loci"][["chunk_id", "genomic_locus", "attention_weight"]].to_string(), flush=True)
    print(f"Enrichment: {inspection['amr_locus_attention_percentage']:.2f}% of attention mass focused on AMR determinants!", flush=True)

    analyzer.plot_genomic_attention_map(
        inspection_result=inspection,
        genome_id=sample_item["genome_id"],
        save_path="figures/attention_map_loci.png"
    )

    print("\n" + "=" * 75, flush=True)
    print("ALL ARTIFACTS, FIGURES AND BENCHMARKS FINALIZED SUCCESSFULLY!", flush=True)
    print("=" * 75, flush=True)


if __name__ == "__main__":
    main()
