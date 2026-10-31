"""
Stage 1: Live BV-BRC AMR Data Retrieval & Harmonization
Replicates Cells 11-14 of the benchmark notebook to query all experimental AST records,
audit data coverage and conflicts, and extract the complete 5-antibiotic genome cohort.
"""

import time
import requests
import numpy as np
import pandas as pd
from pathlib import Path
from urllib.parse import quote

BASE_URL = "https://www.bv-brc.org/api/genome_amr/"
ANTIBIOTICS = [
    "ampicillin",
    "cefotaxime",
    "ceftazidime",
    "ciprofloxacin",
    "gentamicin"
]
PAGE_SIZE = 10000

out_raw = Path("data/raw")
out_proc = Path("data/processed")
out_raw.mkdir(parents=True, exist_ok=True)
out_proc.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("STAGE 1: RETRIEVING LIVE CANDIDATE AMR RECORDS FROM BV-BRC (PATRIC)")
print("=" * 70)

all_records = []
session = requests.Session()
session.headers.update({
    "Accept": "application/json",
    "User-Agent": "Ecoli-AMR-Capstone-Dataset-Expansion/1.0"
})

for antibiotic in ANTIBIOTICS:
    print(f"\n[+] Fetching {antibiotic} AST records...")
    start = 0

    while True:
        query = (
            f"eq(taxon_id,562)"
            f"&eq(antibiotic,{antibiotic})"
            f'&eq(evidence,"Laboratory Method")'
            f"&select(id,genome_id,antibiotic,resistant_phenotype,"
            f"evidence,testing_standard,testing_standard_year,"
            f"laboratory_typing_method,measurement,measurement_value)"
            f"&sort(+id)"
            f"&limit({PAGE_SIZE},{start})"
            f"&http_accept=application/json"
        )

        url = BASE_URL + "?" + quote(query, safe='(),&+="')
        resp = session.get(url, timeout=180)
        resp.raise_for_status()

        page = resp.json()
        print(f"  Offset: {start:5d} | Received: {len(page):5d} records")

        if not page:
            break

        all_records.extend(page)

        if len(page) < PAGE_SIZE:
            break

        start += PAGE_SIZE
        time.sleep(0.3)

raw_amr = pd.DataFrame(all_records)
if raw_amr.empty:
    raise RuntimeError("No records collected from BV-BRC. Aborting.")

raw_amr = raw_amr.drop_duplicates(subset=["id"])
raw_csv_path = out_raw / "expanded_amr_records_raw.csv"
raw_amr.to_csv(raw_csv_path, index=False)

print("\n" + "=" * 70)
print(f"RAW RETRIEVAL SUMMARY: {len(raw_amr):,} total records saved to {raw_csv_path}")
print("=" * 70)
print(raw_amr.groupby("antibiotic").size().rename("Records").to_frame())
print("\nPhenotype Counts per Drug:")
print(pd.crosstab(raw_amr["antibiotic"], raw_amr["resistant_phenotype"].fillna("<Missing>")))

# -------------------------------------------------------------
# Phenotype Harmonization & Conflict Resolution (Cell 12 & 13)
# -------------------------------------------------------------
print("\n" + "=" * 70)
print("AUDITING COVERAGE & RESOLVING CONFLICTS")
print("=" * 70)

coverage = (
    raw_amr.dropna(subset=["genome_id"])
    .groupby("antibiotic")
    .agg(
        AMR_records=("id", "nunique"),
        Unique_genomes=("genome_id", "nunique")
    )
    .reset_index()
)
coverage.to_csv(out_raw / "antibiotic_genome_coverage.csv", index=False)

df = raw_amr.copy()
df["phenotype_clean"] = df["resistant_phenotype"].astype("string").str.strip().str.lower()
phenotype_map = {"resistant": 1, "susceptible": 0}
df["binary_label"] = df["phenotype_clean"].map(phenotype_map)

df = df[df["antibiotic"].str.lower().isin(ANTIBIOTICS) & df["genome_id"].notna()].copy()
df["antibiotic"] = df["antibiotic"].str.lower()

pair_summary = (
    df.dropna(subset=["binary_label"])
      .groupby(["genome_id", "antibiotic"])
      .agg(distinct_binary_labels=("binary_label", "nunique"))
      .reset_index()
)
conflict_pairs = pair_summary[pair_summary["distinct_binary_labels"] > 1].copy()
print(f"Genome-antibiotic pairs with conflicting phenotypes: {len(conflict_pairs)}")

conflict_details = df.merge(
    conflict_pairs[["genome_id", "antibiotic"]],
    on=["genome_id", "antibiotic"],
    how="inner"
).sort_values(["genome_id", "antibiotic"])
conflict_details.to_csv(out_raw / "genome_antibiotic_conflict_details.csv", index=False)

# Resolve conservatively: only retain if single unambiguous binary label
def resolve_pair(group):
    labels = set(group["binary_label"].dropna().astype(int))
    return float(next(iter(labels))) if len(labels) == 1 else np.nan

resolved = (
    df.groupby(["genome_id", "antibiotic"])
      .apply(resolve_pair, include_groups=False)
      .rename("label")
      .reset_index()
)

all_genomes = pd.Index(df["genome_id"].unique(), name="genome_id")
labels_wide = (
    resolved.pivot(index="genome_id", columns="antibiotic", values="label")
    .reindex(index=all_genomes, columns=ANTIBIOTICS)
)
labels_wide.columns = [f"{a}_label" for a in labels_wide.columns]
labels_wide = labels_wide.reset_index()

labels_wide.to_csv(out_proc / "genome_labels_multilabel_clean.csv", index=False)

# Select complete 5-drug cohort
label_cols = [f"{a}_label" for a in ANTIBIOTICS]
complete_labels = labels_wide.dropna(subset=label_cols).copy()
valid_binary = complete_labels[label_cols].isin([0, 1]).all(axis=1)
complete_labels = complete_labels[valid_binary].drop_duplicates("genome_id").copy()

selected_csv = out_proc / "selected_5_antibiotic_genomes.csv"
complete_labels.to_csv(selected_csv, index=False)

print(f"\nTotal genomes in database: {len(labels_wide):,}")
print(f"Genomes with ALL 5 verified binary labels: {len(complete_labels):,}")
print(f"Saved complete 5-drug cohort to {selected_csv}")

print("\nUsable Label Breakdown in 5-Drug Cohort:")
for col in label_cols:
    res = int((complete_labels[col] == 1).sum())
    sus = int((complete_labels[col] == 0).sum())
    print(f"  {col:20s} | Resistant: {res:5d} ({res/len(complete_labels):.1%}) | Susceptible: {sus:5d} ({sus/len(complete_labels):.1%})")

print("\nStage 1 Completed Successfully!")

