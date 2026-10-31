"""
Stage 3: Resistome-Guided Centered 900bp Chunking & Multi-Label Stratified Split
Directly replicates and enhances Cells 31 and 33 of the benchmark notebook.
Identifies genomic AMR determinants (blaTEM, blaCTX-M, gyrA QRDR, aac3, aadA, blaOXA)
on both forward and reverse complement strands, centers the 900bp window around the motif,
guarantees their inclusion alongside chromosomal background windows,
and performs MultilabelStratifiedShuffleSplit (80% Train, 10% Val, 10% Test).
"""

import re
import csv
import gzip
import time
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
from iterstrat.ml_stratifiers import MultilabelStratifiedShuffleSplit

CHUNK_SIZE = 900
MIN_CONTIG_LENGTH = 200
MAX_CHUNKS_PER_GENOME = 32
MAX_PER_LOCUS = 3

OUT_PROC = Path("data/processed")
COHORT_FILE = OUT_PROC / "curated_cohort_genomes.csv"
MANIFEST_FILE = OUT_PROC / "genome_sequence_download_manifest.csv"
VALIDATION_FILE = OUT_PROC / "genome_sequence_validation.csv"
RAW_CHUNKS_FILE = OUT_PROC / "ecoli_prokbert_chunks.csv.gz"
SPLIT_FILE = OUT_PROC / "genome_train_val_test_split.csv"
FINAL_CHUNKS_FILE = OUT_PROC / "ecoli_prokbert_chunks_with_split.csv.gz"

ANTIBIOTICS = [
    "ampicillin_label",
    "cefotaxime_label",
    "ceftazidime_label",
    "ciprofloxacin_label",
    "gentamicin_label"
]

# Conserved catalytic motifs for clinical AMR determinants
AMR_MOTIFS = {
    "blaTEM_penicillinase": [
        "GAGTACTCACCAG",
        "CACCCAGAAAC",
        "TGATGAGCACTTT",
        "TTACTCATGACC"
    ],
    "blaCTX_M_ESBL": [
        "TGATGAGCACCTT",
        "CGCCGCCATC",
        "GATGTTAAGCAG",
        "ACCGCGATATC"
    ],
    "blaOXA_beta_lactamase": [
        "ATATCTCTATTTC",
        "CAATCGCATTAG",
        "TTAGCCCAATTT"
    ],
    "gyrA_QRDR_mutation": [
        "ACTTAGCAGTTA",
        "TTCAGTTACGGT",
        "CCAGACTTAGCA"
    ],
    "gyrA_wildtype": [
        "ACTCGGCAGTC",
        "GACGGCCTGAAG",
        "TCTACGACACCA"
    ],
    "parC_QRDR": [
        "GTCGGTGACGTACT",
        "CAGTTCGGTGAC"
    ],
    "aac3_acetyltransferase": [
        "ATGAGCACAAA",
        "ATGCCCTGGCGG",
        "TGGTCTGCACCG"
    ],
    "aadA_nucleotidyltransferase": [
        "TGATTTGCTGG",
        "GGAGTGCCAAAG",
        "CATAGCCCGGAA"
    ],
    "core_essential_gene": [
        "ATGACTGTCAGAGTT",  # gapA
        "ATGGCTATCGACGAA"   # recA
    ]
}


def revcomp(seq: str) -> str:
    """Reverse complement a DNA string."""
    tr = str.maketrans("ACGTN", "TGCAN")
    return seq.translate(tr)[::-1]


# Compile forward and reverse complement motif queries
COMPILED_MOTIFS = []
for locus, motifs in AMR_MOTIFS.items():
    for m in motifs:
        COMPILED_MOTIFS.append((locus, m))
        COMPILED_MOTIFS.append((locus, revcomp(m)))


def read_fasta(path):
    """Yield (header, sequence) records without joining contigs."""
    header = None
    pieces = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    yield header, "".join(pieces).upper()
                header = line[1:].split()[0]
                pieces = []
            else:
                pieces.append(line)
        if header is not None:
            yield header, "".join(pieces).upper()


def extract_genome_chunks(fasta_path: str):
    """
    Extract centered AMR determinant chunks (both strands)
    and evenly-spaced chromosomal background chunks.
    """
    locus_chunks = defaultdict(list)
    bg_chunks = []

    for contig_id, seq in read_fasta(fasta_path):
        if len(seq) < MIN_CONTIG_LENGTH:
            continue

        # 1. Scan for AMR & essential marker motifs
        occupied_spans = []
        for locus, motif in COMPILED_MOTIFS:
            pos = 0
            while True:
                idx = seq.find(motif, pos)
                if idx == -1:
                    break
                # Center the 900bp chunk around motif: start ~120bp before motif
                start = max(0, idx - 120)
                end = min(len(seq), start + CHUNK_SIZE)
                if (end - start) < MIN_CONTIG_LENGTH:
                    break
                chunk = seq[start:end]
                if re.fullmatch(r"[ACGTRYSWKMBDHVN]+", chunk):
                    # Check overlap with existing in same locus
                    if not any(abs(start - prev_start) < 400 for prev_start, _ in locus_chunks[locus]):
                        locus_chunks[locus].append((start, (contig_id, start, chunk, locus)))
                        occupied_spans.append((start, end))
                pos = idx + len(motif) + 300

        # 2. Extract background chunks avoiding dense AMR regions
        stride = 60000  # sample every ~60kb along chromosome
        for bg_start in range(1000, len(seq), stride):
            bg_end = min(len(seq), bg_start + CHUNK_SIZE)
            if (bg_end - bg_start) < MIN_CONTIG_LENGTH:
                continue
            # avoid overlapping an AMR chunk
            if any(max(bg_start, o_start) < min(bg_end, o_end) for o_start, o_end in occupied_spans):
                continue
            chunk = seq[bg_start:bg_end]
            if re.fullmatch(r"[ACGTRYSWKMBDHVN]+", chunk):
                bg_chunks.append((contig_id, bg_start, chunk, "chromosomal_background"))

    # Balance and assemble final chunks
    chosen = []
    # Add AMR & essential marker chunks (capped per locus)
    for locus, items in locus_chunks.items():
        for _, item in items[:MAX_PER_LOCUS]:
            chosen.append(item)

    amr_count = len(chosen)

    # Fill remainder with chromosomal background
    remaining_quota = MAX_CHUNKS_PER_GENOME - len(chosen)
    if remaining_quota > 0 and bg_chunks:
        n_bg = min(remaining_quota, len(bg_chunks))
        indices = np.linspace(0, len(bg_chunks) - 1, num=n_bg, dtype=int)
        indices = sorted(set(indices))
        for idx in indices:
            chosen.append(bg_chunks[idx])

    return chosen, amr_count


def main():
    print("=" * 70)
    print("STAGE 3: RESISTOME-GUIDED CENTERED 900bp CHUNKING & STRATIFIED SPLIT")
    print("=" * 70)

    labels = pd.read_csv(COHORT_FILE, dtype={"genome_id": str}).drop_duplicates("genome_id").set_index("genome_id")
    manifest = pd.read_csv(MANIFEST_FILE, dtype={"genome_id": str}).drop_duplicates("genome_id").set_index("genome_id")
    validation = pd.read_csv(VALIDATION_FILE, dtype={"genome_id": str}).drop_duplicates("genome_id").set_index("genome_id")

    valid_gids = [gid for gid in labels.index if gid in validation.index and bool(validation.loc[gid, "valid"])]
    print(f"Genomes with validated FASTA sequences: {len(valid_gids)}/{len(labels)}")

    fields = [
        "genome_id", "chunk_id", "contig_id", "start_bp",
        "chunk_length", "sequence", "marker_annotation"
    ] + ANTIBIOTICS

    summary = []
    total_chunks = 0
    total_amr_chunks = 0
    t0 = time.time()

    print(f"\n[+] Extracting centered 900bp chunks (both strands + background)...")

    with gzip.open(RAW_CHUNKS_FILE, "wt", newline="", encoding="utf-8") as gz:
        writer = csv.DictWriter(gz, fieldnames=fields)
        writer.writeheader()

        for i, gid in enumerate(valid_gids, start=1):
            fasta_path = str(manifest.loc[gid, "fasta_path"])
            if not fasta_path or not Path(fasta_path).exists():
                summary.append({"genome_id": gid, "status": "missing_fasta", "saved_chunks": 0, "amr_chunks": 0})
                continue

            chosen, amr_count = extract_genome_chunks(fasta_path)

            if not chosen:
                summary.append({"genome_id": gid, "status": "no_chunks", "saved_chunks": 0, "amr_chunks": 0})
                continue

            total_amr_chunks += amr_count
            total_chunks += len(chosen)

            for j, (contig_id, start, seq, locus) in enumerate(chosen):
                row_dict = {
                    "genome_id": gid,
                    "chunk_id": f"{gid}_chunk_{j:03d}",
                    "contig_id": contig_id,
                    "start_bp": start,
                    "chunk_length": len(seq),
                    "sequence": seq,
                    "marker_annotation": locus
                }
                for col in ANTIBIOTICS:
                    row_dict[col] = int(labels.loc[gid, col])
                writer.writerow(row_dict)

            summary.append({
                "genome_id": gid,
                "status": "ok",
                "saved_chunks": len(chosen),
                "amr_chunks": amr_count
            })

            if i % 25 == 0 or i == len(valid_gids):
                print(f"  Processed {i:3d}/{len(valid_gids)} genomes | Total Chunks: {total_chunks:,} (AMR loci: {total_amr_chunks}) [{time.time()-t0:.1f}s]")

    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(OUT_PROC / "prokbert_chunk_generation_summary.csv", index=False)

    print(f"\nTotal 900bp chunks written: {total_chunks:,} (Identified AMR Determinants: {total_amr_chunks})")
    print(f"Saved raw chunks: {RAW_CHUNKS_FILE}")

    # -------------------------------------------------------------
    # Multi-Label Stratified Split
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("PERFORMING MULTI-LABEL STRATIFIED SPLIT (80% Train, 10% Val, 10% Test)")
    print("=" * 70)

    split_labels = labels.loc[valid_gids].reset_index()
    X = np.zeros((len(split_labels), 1))
    Y = split_labels[ANTIBIOTICS].astype(int).to_numpy()

    split1 = MultilabelStratifiedShuffleSplit(n_splits=1, test_size=0.10, random_state=42)
    trainval_idx, test_idx = next(split1.split(X, Y))

    trainval_labels = split_labels.iloc[trainval_idx].reset_index(drop=True)
    Y_tv = trainval_labels[ANTIBIOTICS].astype(int).to_numpy()
    X_tv = np.zeros((len(trainval_labels), 1))

    split2 = MultilabelStratifiedShuffleSplit(n_splits=1, test_size=(1/9), random_state=43)
    train_idx_rel, val_idx_rel = next(split2.split(X_tv, Y_tv))

    train_ids = set(trainval_labels.iloc[train_idx_rel]["genome_id"])
    val_ids = set(trainval_labels.iloc[val_idx_rel]["genome_id"])
    test_ids = set(split_labels.iloc[test_idx]["genome_id"])

    assert not (train_ids & val_ids)
    assert not (train_ids & test_ids)
    assert not (val_ids & test_ids)
    assert len(train_ids | val_ids | test_ids) == len(split_labels)

    split_map = {gid: "train" for gid in train_ids}
    split_map.update({gid: "validation" for gid in val_ids})
    split_map.update({gid: "test" for gid in test_ids})

    split_df = split_labels[["genome_id"] + ANTIBIOTICS].copy()
    split_df["split"] = split_df["genome_id"].map(split_map)
    split_df.to_csv(SPLIT_FILE, index=False)

    print("Genome Split Counts:")
    print(split_df["split"].value_counts())
    print("\nResistance Proportions Across Splits (1 = Resistant):")
    print(split_df.groupby("split")[ANTIBIOTICS].mean().round(3))

    # Stream final dataset with split tag
    print(f"\n[+] Streaming split tags into final dataset: {FINAL_CHUNKS_FILE}...")
    chunk_count = 0
    unmatched = 0

    with gzip.open(RAW_CHUNKS_FILE, "rt", newline="", encoding="utf-8") as src, \
         gzip.open(FINAL_CHUNKS_FILE, "wt", newline="", encoding="utf-8") as dst:

        reader = csv.DictReader(src)
        output_fields = reader.fieldnames + ["split"]
        writer = csv.DictWriter(dst, fieldnames=output_fields)
        writer.writeheader()

        for row in reader:
            gid = row["genome_id"]
            row["split"] = split_map.get(gid, "")
            if not row["split"]:
                unmatched += 1
            writer.writerow(row)
            chunk_count += 1

    print(f"Final Dataset Ready: {chunk_count:,} chunks with split tags.")
    print(f"Chunks with missing split: {unmatched}")
    assert unmatched == 0, "Some chunks did not match a split"
    print("\nStage 3 Completed Successfully!")


if __name__ == "__main__":
    main()
