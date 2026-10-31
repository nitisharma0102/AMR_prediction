"""
Stage 2: High-Throughput Real E. coli Whole-Genome Sequence Download & Validation
Directly replicates Cells 18, 27, 28, 30 of the benchmark notebook.
Downloads authentic contig FASTA files from BV-BRC in optimized batches,
validates IUPAC nucleotide integrity, and generates the sequence manifest.
"""

import re
import time
import requests
import numpy as np
import pandas as pd
from pathlib import Path
from urllib.parse import quote

BASE_URL = "https://www.bv-brc.org/api/genome_sequence/"
FASTA_DIR = Path("data/fastas")
OUT_PROC = Path("data/processed")
FASTA_DIR.mkdir(parents=True, exist_ok=True)
OUT_PROC.mkdir(parents=True, exist_ok=True)

SELECTED_CSV = OUT_PROC / "selected_5_antibiotic_genomes.csv"
if not SELECTED_CSV.exists():
    raise FileNotFoundError("Run stage1_bvbrc_data_extraction.py first.")

selected_df = pd.read_csv(SELECTED_CSV, dtype={"genome_id": str})
print(f"Loaded {len(selected_df):,} complete-label genomes from {SELECTED_CSV}")

# Stratified selection to ensure rich representation across all 5 drugs
LABEL_COLS = ["ampicillin_label", "cefotaxime_label", "ceftazidime_label", "ciprofloxacin_label", "gentamicin_label"]

# Target: 250 diverse genomes with high representation of minority resistant classes
TARGET_GENOMES = 250
np.random.seed(42)

# Prioritize isolates that are resistant to rare drugs (gentamicin, ceftazidime, cefotaxime)
is_rare_resistant = (
    (selected_df["gentamicin_label"] == 1) |
    (selected_df["ceftazidime_label"] == 1) |
    (selected_df["cefotaxime_label"] == 1) |
    (selected_df["ciprofloxacin_label"] == 1)
)

rare_resistant_df = selected_df[is_rare_resistant]
other_df = selected_df[~is_rare_resistant]

n_rare = min(len(rare_resistant_df), 160)
n_other = min(len(other_df), TARGET_GENOMES - n_rare)

sampled_rare = rare_resistant_df.sample(n=n_rare, random_state=42)
sampled_other = other_df.sample(n=n_other, random_state=42)

cohort_df = pd.concat([sampled_rare, sampled_other]).sample(frac=1.0, random_state=42).reset_index(drop=True)
COHORT_IDS = cohort_df["genome_id"].tolist()

cohort_csv = OUT_PROC / "curated_cohort_genomes.csv"
cohort_df.to_csv(cohort_csv, index=False)

print(f"\nCurated Stratified Cohort of {len(COHORT_IDS)} isolates saved to {cohort_csv}")
print("Class Resistance Frequencies in Selected Cohort:")
for col in LABEL_COLS:
    r_count = int((cohort_df[col] == 1).sum())
    print(f"  {col:20s}: {r_count:3d} resistant ({r_count/len(cohort_df):.1%})")

# -------------------------------------------------------------
# Batch Download from BV-BRC
# -------------------------------------------------------------
BATCH_SIZE = 20
PAGE_SIZE = 5000
PAUSE = 0.2

session = requests.Session()
session.headers.update({"Accept": "application/json", "User-Agent": "ProkBERT-AMR-Downloader/1.0"})

def clean_id(value):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(value))

def get_page(ids, offset):
    id_list = ",".join(ids)
    query = (
        f"in(genome_id,({id_list}))"
        f"&select(genome_id,sequence_id,length,sequence)"
        f"&sort(+sequence_id)"
        f"&limit({PAGE_SIZE},{offset})"
        f"&http_accept=application/json"
    )
    url = BASE_URL + "?" + quote(query, safe="(),&+=")
    resp = session.get(url, timeout=180)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise ValueError("API did not return a JSON list")
    return data

manifest = []
download_errors = []
total_genomes = len(COHORT_IDS)
num_batches = (total_genomes + BATCH_SIZE - 1) // BATCH_SIZE

print("\n" + "=" * 70)
print(f"DOWNLOADING {total_genomes} WHOLE GENOMES ({num_batches} BATCHES) FROM BV-BRC")
print("=" * 70)

t_start = time.time()

for b_idx in range(num_batches):
    start = b_idx * BATCH_SIZE
    batch_ids = COHORT_IDS[start:start + BATCH_SIZE]
    b_num = b_idx + 1

    # Check if all FASTAs in batch already exist on disk
    all_exist = all((FASTA_DIR / f"{clean_id(gid)}.fna").exists() and (FASTA_DIR / f"{clean_id(gid)}.fna").stat().st_size > 1000 for gid in batch_ids)
    if all_exist:
        print(f"Batch {b_num:2d}/{num_batches:2d} (genomes {start+1}-{start+len(batch_ids)}): FASTAs already on disk. Skipping.")
        for gid in batch_ids:
            fp = FASTA_DIR / f"{clean_id(gid)}.fna"
            manifest.append({
                "genome_id": gid,
                "status": "downloaded",
                "fasta_path": str(fp)
            })
        continue

    print(f"Batch {b_num:2d}/{num_batches:2d} | Genomes {start+1:3d}-{start+len(batch_ids):3d}...", end=" ", flush=True)
    t_b0 = time.time()

    records = []
    offset = 0

    try:
        while True:
            page = get_page(batch_ids, offset)
            if not page:
                break
            records.extend(page)
            if len(page) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
            time.sleep(PAUSE)

        # Group sequence contigs by genome_id
        grouped = {gid: [] for gid in batch_ids}
        for r in records:
            gid = str(r.get("genome_id", ""))
            seq = "".join(str(r.get("sequence") or "").split()).upper()
            if gid in grouped and seq and re.fullmatch(r"[ACGTRYSWKMBDHVN]+", seq):
                grouped[gid].append((r, seq))

        # Write FASTA files
        for gid in batch_ids:
            fasta_path = FASTA_DIR / f"{clean_id(gid)}.fna"
            contigs = grouped.get(gid, [])

            if not contigs:
                manifest.append({"genome_id": gid, "status": "no_sequence", "contigs": 0, "total_bases": 0, "fasta_path": ""})
                continue

            total_bases = 0
            seen_ids = set()

            with open(fasta_path, "w", encoding="utf-8") as f:
                for rec, seq in contigs:
                    sid = str(rec.get("sequence_id") or f"{gid}.contig{len(seen_ids)+1}")
                    if sid in seen_ids:
                        continue
                    seen_ids.add(sid)
                    f.write(f">{sid} genome_id={gid}\n")
                    for i in range(0, len(seq), 80):
                        f.write(seq[i:i+80] + "\n")
                    total_bases += len(seq)

            manifest.append({
                "genome_id": gid,
                "status": "downloaded",
                "contigs": len(seen_ids),
                "total_bases": total_bases,
                "fasta_path": str(fasta_path)
            })

        print(f"Done ({len(records)} contigs in {time.time() - t_b0:.1f}s)")

    except Exception as e:
        print(f"FAILED: {e}")
        download_errors.append({"batch": b_num, "error": repr(e)})
        for gid in batch_ids:
            manifest.append({"genome_id": gid, "status": "error", "contigs": 0, "total_bases": 0, "fasta_path": ""})

    time.sleep(PAUSE)

manifest_df = pd.DataFrame(manifest).drop_duplicates("genome_id", keep="last")
manifest_path = OUT_PROC / "genome_sequence_download_manifest.csv"
manifest_df.to_csv(manifest_path, index=False)

# Sequence Validation (Cell 28)
validation_results = []
for _, row in manifest_df.iterrows():
    fp = Path(str(row.get("fasta_path", "")))
    exists = fp.exists() and fp.stat().st_size > 0
    contigs = 0
    bases = 0
    valid_dna = True

    if exists:
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(">"):
                    contigs += 1
                elif line:
                    bases += len(line)
                    if any(c not in "ACGTNRYKMSWBDHV-" for c in line.upper()):
                        valid_dna = False

    passed = exists and contigs > 0 and bases > 100_000 and valid_dna
    validation_results.append({
        "genome_id": row["genome_id"],
        "valid": passed,
        "contigs": contigs,
        "total_bases": bases,
        "fasta_path": str(fp) if exists else ""
    })

val_df = pd.DataFrame(validation_results)
val_path = OUT_PROC / "genome_sequence_validation.csv"
val_df.to_csv(val_path, index=False)

n_valid = int(val_df["valid"].sum())
total_bp = int(val_df["total_bases"].sum())
elapsed_total = time.time() - t_start

print("\n" + "=" * 70)
print(f"STAGE 2 SUMMARY: DOWNLOAD & VALIDATION COMPLETE ({elapsed_total:.1f}s)")
print("=" * 70)
print(f"Total Genomes in Cohort: {len(COHORT_IDS)}")
print(f"Valid FASTA Genomes:    {n_valid} ({n_valid/len(COHORT_IDS):.1%})")
print(f"Total DNA Bases Checked: {total_bp:,} bp (~{total_bp/(1024**3):.2f} Gbp)")
print(f"Saved Manifest:          {manifest_path}")
print(f"Saved Validation:        {val_path}")

