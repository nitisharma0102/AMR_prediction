"""
Generates clean, annotated, runnable Jupyter Notebooks for all 4 project stages.
"""

import json
from pathlib import Path

def make_notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.10.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

def md_cell(text):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.split("\n")]
    }

def code_cell(code):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in code.split("\n")]
    }

# -------------------------------------------------------------
# Notebook 1: Data Extraction & Audit
# -------------------------------------------------------------
nb1_cells = [
    md_cell("""# Stage 1: BV-BRC Data Acquisition & Antimicrobial Susceptibility Audit
### Capstone Project: ProkBERT with Attention Pooling for Multi-Label AMR Prediction

**Objective:** Extract experimental AST phenotypes for *Escherichia coli* (Taxon 562) across 5 target antibiotic classes from BV-BRC (PATRIC), filter strictly for laboratory-verified phenotypes, audit conflicting measurements, and build the multi-label ground truth database."""),

    code_cell("""import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path("..").resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.bvbrc_client import BVBRCClient, TARGET_ANTIBIOTICS, ANTIBIOTIC_CLASSES

print("Target Antibiotics:")
for drug, drug_class in ANTIBIOTIC_CLASSES.items():
    print(f"  - {drug.capitalize()}: {drug_class}")"""),

    md_cell("""## 1.1 Load and Inspect BV-BRC AST Metadata
We retain provenance and exclusively filter for `evidence == 'Laboratory Method'` to eliminate genotypic predictions and ensure strict clinical ground truth."""),

    code_cell("""raw_csv = PROJECT_ROOT / "data" / "raw" / "expanded_amr_records_raw.csv"
if raw_csv.exists():
    df_raw = pd.read_csv(raw_csv)
    print(f"Loaded {len(df_raw)} raw AST records across {df_raw['genome_id'].nunique()} genomes.")
    display(df_raw.head())
else:
    print(f"Raw CSV not found at {raw_csv}. Generating via BVBRCClient...")
    client = BVBRCClient()
    df_raw = client.fetch_amr_records(max_records_per_drug=100)
    display(df_raw.head())"""),

    md_cell("""## 1.2 Antibiotic Genome Coverage Audit
Evaluate the number of unique bacterial genomes tested for each drug class."""),

    code_cell("""coverage = df_raw.groupby("antibiotic").agg(
    AST_Records=("id", "count"),
    Unique_Genomes=("genome_id", "nunique")
).reset_index()
display(coverage)"""),

    md_cell("""## 1.3 Phenotype Harmonization & Conflict Resolution
- Resistant -> 1
- Susceptible -> 0
- Intermediate / Missing -> Excluded
- Conflicting results for the same isolate-antibiotic pair are audited and resolved conservatively."""),

    code_cell("""client = BVBRCClient()
clean_labels, conflicts = client.clean_and_harmonize_labels(df_raw)
print(f"Clean multi-label matrix shape: {clean_labels.shape}")
print(f"Conflicting isolate-drug pairs detected: {len(conflicts)}")
display(clean_labels.head(10))"""),

    md_cell("""## 1.4 Export Verified Clean Multi-Label Matrix""")
]

# -------------------------------------------------------------
# Notebook 2: Genomic Preprocessing & Chunking
# -------------------------------------------------------------
nb2_cells = [
    md_cell("""# Stage 2: Genomic Preprocessing, 900bp Window Chunking & Stratified Split
### Capstone Project: ProkBERT with Attention Pooling for Multi-Label AMR Prediction

**Objective:** Implement contig-aware sliding window fragmentation (900 bp length, 800 bp stride = 100 bp overlap), IUPAC nucleotide quality control, overlapping 6-mer tokenization, and multi-label stratified train/val/test splitting."""),

    code_cell("""import sys
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path("..").resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.preprocessor import DNATokenizer, GenomicPreprocessor
from src.data.dataset import create_multilabel_stratified_split, LABEL_COLS

tokenizer = DNATokenizer(k=6)
print(f"Initialized DNA Tokenizer: Vocab size = {tokenizer.vocab_size} (4096 6-mers + 5 special tokens)")"""),

    md_cell("""## 2.1 Sliding Window Genomic Fragmentation
We extract 900bp windows with 100bp overlap. Windows strictly respect contig boundaries."""),

    code_cell("""preprocessor = GenomicPreprocessor(chunk_size=900, stride=800, max_chunks_per_genome=16)
print(f"Chunk size: {preprocessor.chunk_size} bp | Stride: {preprocessor.stride} bp (Overlap: 100 bp)")

test_dna = "ATGC" * 300  # 1200 bp test contig
kmers = tokenizer.tokenize_sequence(test_dna[:20])
print("Sample 6-mers from sequence:", kmers)

enc = tokenizer.encode(test_dna[:900], max_length=150, padding="max_length")
print("Encoded token IDs (first 10):", enc["input_ids"][:10])
print("Attention mask (first 10):", enc["attention_mask"][:10])"""),

    md_cell("""## 2.2 Inspect Processed Chunks & Multi-Label Stratified Split
Load the benchmark chunk database and verify that resistance proportions are balanced across splits with zero genome leakage."""),

    code_cell("""chunks_path = PROJECT_ROOT / "data" / "processed" / "ecoli_prokbert_chunks_with_split.csv.gz"
chunks_df = pd.read_csv(chunks_path, compression="gzip")
print(f"Total Chunks: {len(chunks_df)} across {chunks_df['genome_id'].nunique()} genomes.")

split_summary = chunks_df.drop_duplicates("genome_id")["split"].value_counts()
print("\nGenome Split Counts:")
print(split_summary)

print("\nResistance Proportions Across Splits:")
display(chunks_df.drop_duplicates("genome_id").groupby("split")[LABEL_COLS].mean().round(3))""")
]

# -------------------------------------------------------------
# Notebook 3: ProkBERT + Attention Pooling Model
# -------------------------------------------------------------
nb3_cells = [
    md_cell("""# Stage 3: ProkBERT Transformer Backbone & Attention Pooling Layer
### Capstone Project: ProkBERT with Attention Pooling for Multi-Label AMR Prediction

**Objective:** Build the PyTorch genomic transformer backbone, implement the Attention Pooling layer, and train the multi-label AMR classifier using weighted binary cross-entropy loss."""),

    code_cell("""import sys
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from pathlib import Path
from torch.utils.data import DataLoader

PROJECT_ROOT = Path("..").resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.preprocessor import DNATokenizer
from src.data.dataset import GenomeBagDataset, collate_genome_bags, LABEL_COLS
from src.models.classifier import ProkBERTAttentionAMR
from src.training.losses import WeightedMultiLabelBCELoss
from src.training.trainer import GenomicAMRTrainer

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using compute device: {device}")"""),

    md_cell("""## 3.1 Initialize Model Architecture
The architecture consists of:
1. Bidirectional DNA Transformer blocks processing 6-mer tokens into chunk embeddings $\mathbf{h}_i \in \mathbb{R}^d$.
2. Attention Pooling layer aggregating chunks: $\mathbf{c} = \sum \alpha_i \mathbf{h}_i$.
3. Multi-label classification head predicting Sigmoid probabilities for 5 antibiotic classes."""),

    code_cell("""tokenizer = DNATokenizer(k=6)
model = ProkBERTAttentionAMR(
    vocab_size=tokenizer.vocab_size,
    embed_dim=128,
    num_layers=3,
    num_heads=4,
    dim_feedforward=256,
    num_classes=5,
    max_seq_len=120,
    dropout=0.15
).to(device)

total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"Total Trainable Parameters: {total_params:,}")"""),

    md_cell("""## 3.2 Load Pre-Trained Best Checkpoint"""),

    code_cell("""ckpt_path = PROJECT_ROOT / "models" / "checkpoints" / "best_prokbert_attnpool.pt"
if ckpt_path.exists():
    model.load_state_dict(torch.load(ckpt_path, map_location=device))
    print(f"Successfully loaded best checkpoint from {ckpt_path}")
else:
    print("Checkpoint not found. Run scripts/run_full_training_and_benchmark.py to train.")""")
]

# -------------------------------------------------------------
# Notebook 4: Evaluation & Interpretability
# -------------------------------------------------------------
nb4_cells = [
    md_cell("""# Stage 4: Multi-Model Benchmark & Attention-Based Interpretability
### Capstone Project: ProkBERT with Attention Pooling for Multi-Label AMR Prediction

**Objective:** Benchmark the proposed model against Mean-Pooling ablation and ML baselines (XGBoost, Random Forest, Logistic Regression), generate publication figures (ROC, PR, Confusion Matrices), and visualize learned attention weights over genomic resistance loci."""),

    code_cell("""import sys
import json
import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

PROJECT_ROOT = Path("..").resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.metrics import MultiLabelEvaluator, ANTIBIOTICS
from src.interpretability.attention_analyzer import GenomicAttentionAnalyzer"""),

    md_cell("""## 4.1 Multi-Model Benchmark Comparison Table"""),

    code_cell("""summary_file = PROJECT_ROOT / "models" / "benchmark_summary.json"
if summary_file.exists():
    with open(summary_file, "r") as f:
        summary_data = json.load(f)
    df_summary = pd.DataFrame(summary_data).T
    display(df_summary.round(4))
else:
    print("Benchmark summary not found. Run scripts/run_full_training_and_benchmark.py.")"""),

    md_cell("""## 4.2 Display Publication Figures
We inspect the generated ROC curves, Precision-Recall curves, and 5-panel Confusion Matrices."""),

    code_cell("""fig_dir = PROJECT_ROOT / "figures"
roc_path = fig_dir / "roc_curves.png"
pr_path = fig_dir / "pr_curves.png"
cm_path = fig_dir / "confusion_matrices.png"
bench_path = fig_dir / "benchmark_comparison.png"
attn_path = fig_dir / "attention_map_loci.png"

for p in [roc_path, pr_path, cm_path, bench_path, attn_path]:
    if p.exists():
        print(f"Found: {p.name}")"""),

    md_cell("""## 4.3 Attention-Based Interpretation: AMR Locus Mapping
Verify that attention weights peak specifically on known resistance genes (*blaTEM-1*, *blaCTX-M-15*, *gyrA* QRDR, *aac(3)-IIa*)."""),

    code_cell("""if attn_path.exists():
    from IPython.display import Image
    display(Image(filename=str(attn_path)))
else:
    print("Attention map figure not yet generated.")""")
]

# Write notebooks
out_dir = Path("notebooks")
out_dir.mkdir(parents=True, exist_ok=True)

with open(out_dir / "01_data_extraction_audit.ipynb", "w", encoding="utf-8") as f:
    json.dump(make_notebook(nb1_cells), f, indent=2)

with open(out_dir / "02_genomic_preprocessing_and_chunking.ipynb", "w", encoding="utf-8") as f:
    json.dump(make_notebook(nb2_cells), f, indent=2)

with open(out_dir / "03_prokbert_attention_pooling_model.ipynb", "w", encoding="utf-8") as f:
    json.dump(make_notebook(nb3_cells), f, indent=2)

with open(out_dir / "04_evaluation_and_interpretability.ipynb", "w", encoding="utf-8") as f:
    json.dump(make_notebook(nb4_cells), f, indent=2)

print("Generated all 4 Jupyter notebooks successfully in notebooks/")

