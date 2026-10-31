"""
End-to-End Training, Benchmarking & Evaluation Pipeline
Trains ProkBERT + Multi-Head Class-Wise Attention Pooling, Mean-Pool Baseline,
and Classical ML Baselines on the E. coli AMR cohort, performs threshold calibration,
evaluates comprehensive clinical metrics, and exports all publication figures.
"""

import sys
import json
import time
from pathlib import Path

# Add project root to sys.path
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
    print("=" * 75)
    print("OPTIMIZED PROKBERT + ATTENTION POOLING FOR MULTI-LABEL AMR PREDICTION")
    print("=" * 75)

    data_path = Path("data/processed/ecoli_prokbert_chunks_with_split.csv.gz")
    if not data_path.exists():
        raise FileNotFoundError(f"Missing dataset at {data_path}. Run stage3_chunking_and_split.py first.")

    print(f"\n1. Loading chunk dataset from {data_path}...")
    chunks_df = pd.read_csv(data_path, compression="gzip")
    print(f"Total chunks loaded: {len(chunks_df)} across {chunks_df['genome_id'].nunique()} genomes.")
    print("Annotated Loci Breakdown:")
    print(chunks_df["marker_annotation"].value_counts().to_string())

    # Calculate class positive weights for imbalance handling
    train_chunks = chunks_df[chunks_df["split"] == "train"]
    train_genomes = train_chunks.drop_duplicates("genome_id")
    pos_counts = train_genomes[LABEL_COLS].sum().values
    neg_counts = len(train_genomes) - pos_counts
    pos_weights = torch.tensor(neg_counts / np.maximum(pos_counts, 1), dtype=torch.float32)
    print("\nCalculated Class Positive Weights for Loss Function:")
    for drug, w in zip(ANTIBIOTICS, pos_weights):
        print(f"  - {drug}: {w.item():.2f}")

    # Build Datasets
    print("\n2. Initializing DNA Tokenizer (6-mers) and Genome Bag Datasets...")
    tokenizer = DNATokenizer(k=6)
    print(f"DNA Tokenizer Vocab Size: {tokenizer.vocab_size} tokens")

    MAX_CHUNKS = 24
    MAX_SEQ_LEN = 160

    train_dataset = GenomeBagDataset(chunks_df, tokenizer, max_chunks_per_genome=MAX_CHUNKS, max_seq_len=MAX_SEQ_LEN, split="train")
    val_dataset = GenomeBagDataset(chunks_df, tokenizer, max_chunks_per_genome=MAX_CHUNKS, max_seq_len=MAX_SEQ_LEN, split="validation")
    test_dataset = GenomeBagDataset(chunks_df, tokenizer, max_chunks_per_genome=MAX_CHUNKS, max_seq_len=MAX_SEQ_LEN, split="test")

    print(f"Cohort Sizes: Train={len(train_dataset)}, Val={len(val_dataset)}, Test={len(test_dataset)} isolates")

    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True, collate_fn=collate_genome_bags)
    val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False, collate_fn=collate_genome_bags)
    test_loader = DataLoader(test_dataset, batch_size=8, shuffle=False, collate_fn=collate_genome_bags)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Compute Device: {device}")

    # 3. Train Proposed Model: ProkBERT + Class-Wise Multi-Head Attention Pooling
    print("\n" + "-" * 60)
    print("3. Training Proposed Architecture: ProkBERT + Class-Wise Attention")
    print("-" * 60)

    torch.manual_seed(42)
    np.random.seed(42)

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

    criterion = WeightedMultiLabelBCELoss(pos_weights=pos_weights)
    optimizer = torch.optim.AdamW(proposed_model.parameters(), lr=5e-4, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=12, eta_min=1e-5)

    trainer_proposed = GenomicAMRTrainer(
        model=proposed_model,
        criterion=criterion,
        optimizer=optimizer,
        scheduler=scheduler,
        device=device,
        checkpoint_dir="models/checkpoints"
    )

    trainer_proposed.fit(
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=12,
        patience=4,
        model_name="best_prokbert_attnpool.pt"
    )

    # 4. Train Ablation Baseline: Mean-Pool ProkBERT (No Attention Pooling)
    print("\n" + "-" * 60)
    print("4. Training Ablation Baseline: Mean-Pool ProkBERT (No Attention Pooling)")
    print("-" * 60)

    torch.manual_seed(43)
    meanpool_model = MeanPoolProkBERTBaseline(
        vocab_size=tokenizer.vocab_size,
        embed_dim=128,
        num_layers=3,
        num_heads=4,
        num_classes=5,
        max_seq_len=MAX_SEQ_LEN,
        dropout=0.10
    )

    optimizer_mp = torch.optim.AdamW(meanpool_model.parameters(), lr=5e-4, weight_decay=1e-4)
    scheduler_mp = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer_mp, T_max=12, eta_min=1e-5)

    trainer_mp = GenomicAMRTrainer(
        model=meanpool_model,
        criterion=criterion,
        optimizer=optimizer_mp,
        scheduler=scheduler_mp,
        device=device,
        checkpoint_dir="models/checkpoints"
    )

    trainer_mp.fit(
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=10,
        patience=4,
        model_name="best_meanpool_baseline.pt"
    )

    # 5. Train Classical ML Baselines
    print("\n" + "-" * 60)
    print("5. Training Classical ML Baselines (k-mer TF-IDF + ML Classifiers)")
    print("-" * 60)

    def extract_genome_texts_and_labels(dataset):
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

    train_texts, y_train_ml = extract_genome_texts_and_labels(train_dataset)
    val_texts, y_val_ml = extract_genome_texts_and_labels(val_dataset)
    test_texts, y_test_true = extract_genome_texts_and_labels(test_dataset)

    ml_pipeline = MLBaselinesPipeline(k=5, max_features=1000, random_state=42)
    ml_pipeline.fit(train_texts, y_train_ml)
    ml_val_probas = ml_pipeline.predict_proba(val_texts)
    ml_test_probas = ml_pipeline.predict_proba(test_texts)

    # 6. Inference on Validation Set for Threshold Calibration
    print("\n" + "=" * 75)
    print("6. Decision Threshold Calibration on Validation Set (N = 25 Genomes)")
    print("=" * 75)

    evaluator = MultiLabelEvaluator(target_names=ANTIBIOTICS)

    # Collect Validation Probabilities for Proposed Model
    proposed_model.eval()
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

    # Optimal Thresholds for Proposed Model
    optimal_thresholds = evaluator.find_optimal_thresholds(y_val_true, y_val_prob_proposed)
    print("Calibrated Optimal Decision Thresholds (F1-Maximizing):")
    for drug, t in zip(ANTIBIOTICS, optimal_thresholds):
        print(f"  - {drug:15s}: {t:.2f}")

    with open("models/optimal_thresholds.json", "w") as f:
        json.dump({drug: float(t) for drug, t in zip(ANTIBIOTICS, optimal_thresholds)}, f, indent=2)

    # 7. Comprehensive Evaluation on Held-out Test Cohort
    print("\n" + "=" * 75)
    print("7. Comprehensive Evaluation on Held-Out Test Cohort (N = 25 Genomes)")
    print("=" * 75)

    # Get predictions on Test Set for Proposed Model
    all_test_probs_prop = []
    with torch.no_grad():
        for batch in test_loader:
            inp = batch["input_ids"].to(device)
            att = batch["attention_mask"].to(device)
            bag = batch["bag_mask"].to(device)
            out = proposed_model(inp, att, bag)
            all_test_probs_prop.append(out["probabilities"].cpu().numpy())
    y_prob_proposed = np.vstack(all_test_probs_prop)

    # Get predictions on Test Set for Mean-Pool Baseline
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

    # Compile benchmark models
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
            "Subset_Accuracy": res["Subset_Accuracy"],
            "Hamming_Loss": res["Hamming_Loss"],
            "Macro_F1": res["Macro_F1"],
            "Micro_F1": res["Micro_F1"],
            "Macro_ROC_AUC": res["Macro_ROC_AUC"],
            "Macro_PR_AUC": res["Macro_PR_AUC"]
        }

    summary_df = pd.DataFrame(benchmark_summary).T
    print("\nBENCHMARK COMPARISON TABLE ON TEST SET:")
    print(summary_df.round(4).to_string())

    # Detailed Class-Wise Breakdown of Proposed Model
    detailed_res = evaluator.evaluate_predictions(y_test_true, y_prob_proposed, threshold=optimal_thresholds)
    print("\nDETAILED CLASS-WISE CLINICAL METRICS (PROKBERT + ATTENTION):")
    print(detailed_res["Class_Metrics_Table"].round(4).to_string(index=False))

    # Save benchmark JSON and CSV
    with open("models/benchmark_summary.json", "w") as f:
        json.dump(benchmark_summary, f, indent=2)
    summary_df.to_csv("models/benchmark_summary.csv")
    detailed_res["Class_Metrics_Table"].to_csv("models/class_wise_metrics.csv", index=False)

    # 8. Generate Publication Figures
    print("\n8. Generating Publication Figures (300 DPI)...")
    evaluator.plot_roc_curves(y_test_true, y_prob_proposed, save_path="figures/roc_curves.png")
    evaluator.plot_precision_recall_curves(y_test_true, y_prob_proposed, save_path="figures/pr_curves.png")
    evaluator.plot_confusion_matrices(y_test_true, (y_prob_proposed >= optimal_thresholds).astype(int), save_path="figures/confusion_matrices.png")

    # Benchmark comparison plot (filter top 4 models for clean visualization)
    plot_summary = {k: v for k, v in benchmark_summary.items() if "Default 0.5" not in k}
    evaluator.plot_benchmark_comparison(plot_summary, save_path="figures/benchmark_comparison.png")

    # 9. Attention-Based Interpretability & Loci Mapping
    print("\n9. Generating Multi-Head Attention Locus Map & AMR Marker Discovery Analysis...")
    analyzer = GenomicAttentionAnalyzer(model=proposed_model, device=device)

    # Find an MDR test isolate with multiple resistance markers
    sample_item = None
    for i in range(len(test_dataset)):
        item = test_dataset[i]
        if item["labels"].sum().item() >= 3:
            sample_item = item
            break
    if sample_item is None:
        sample_item = test_dataset[0]

    inspection = analyzer.inspect_genome(sample_item, chunk_metadata_df=chunks_df)
    print(f"\nAnalyzed Sample Genome: {sample_item['genome_id']}")
    print(f"Top 5 Highest Attended Loci:")
    print(inspection["top_attended_loci"][["chunk_id", "genomic_locus", "attention_weight"]].to_string())
    print(f"Enrichment: {inspection['amr_locus_attention_percentage']:.2f}% of attention mass focused on AMR determinants!")

    analyzer.plot_genomic_attention_map(
        inspection_result=inspection,
        genome_id=sample_item["genome_id"],
        save_path="figures/attention_map_loci.png"
    )

    print("\n" + "=" * 75)
    print("ALL PIPELINE BENCHMARKS AND FIGURES UPDATED SUCCESSFULLY!")
    print("Checkpoints: models/checkpoints/")
    print("Figures: figures/")
    print("Metrics: models/benchmark_summary.json, models/class_wise_metrics.csv")
    print("=" * 75)


if __name__ == "__main__":
    main()
