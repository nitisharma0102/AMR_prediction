"""
BV-BRC Client & AMR Label Curator for E. coli
Handles querying the BV-BRC API, provenance filtering, phenotype harmonization,
conflict resolution, and sequence acquisition.
"""

import os
import re
import csv
import gzip
import time
import requests
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from urllib.parse import quote

BASE_API_URL = "https://www.bv-brc.org/api"
TARGET_ANTIBIOTICS = [
    "ampicillin",
    "cefotaxime",
    "ceftazidime",
    "ciprofloxacin",
    "gentamicin"
]
ANTIBIOTIC_CLASSES = {
    "ampicillin": "Beta-lactam (Aminopenicillin)",
    "cefotaxime": "Beta-lactam (3rd-gen Cephalosporin)",
    "ceftazidime": "Beta-lactam (3rd-gen Cephalosporin)",
    "ciprofloxacin": "Fluoroquinolone (DNA Gyrase / Topo IV inhibitor)",
    "gentamicin": "Aminoglycoside (30S Ribosome inhibitor)"
}


class BVBRCClient:
    """Client for querying BV-BRC bacterial antimicrobial resistance and sequence data."""

    def __init__(self, base_url: str = BASE_API_URL, user_agent: str = "ProkBERT-AMR-Capstone/1.0"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": user_agent
        })

    def fetch_amr_records(
        self,
        taxon_id: int = 562,
        antibiotics: Optional[List[str]] = None,
        page_size: int = 5000,
        max_records_per_drug: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch AST records for specified taxon and antibiotics.
        Strictly filters for 'Laboratory Method' evidence to exclude genotypic predictions.
        """
        antibiotics = antibiotics or TARGET_ANTIBIOTICS
        endpoint = f"{self.base_url}/genome_amr"
        all_records = []

        for drug in antibiotics:
            drug_lower = drug.lower()
            offset = 0
            drug_records = []

            while True:
                query = (
                    f"eq(taxon_id,{taxon_id})"
                    f"&eq(antibiotic,{drug_lower})"
                    f'&eq(evidence,"Laboratory Method")'
                    f"&select(id,genome_id,antibiotic,resistant_phenotype,evidence,"
                    f"testing_standard,testing_standard_year,laboratory_typing_method,"
                    f"measurement,measurement_value)"
                    f"&sort(+id)"
                    f"&limit({page_size},{offset})"
                    f"&http_accept=application/json"
                )
                url = f"{endpoint}/?{quote(query, safe='(),&+=\"')}"

                try:
                    resp = self.session.get(url, timeout=120)
                    resp.raise_for_status()
                    data = resp.json()
                    if not isinstance(data, list):
                        break
                    if not data:
                        break
                    drug_records.extend(data)
                    if len(data) < page_size:
                        break
                    if max_records_per_drug and len(drug_records) >= max_records_per_drug:
                        drug_records = drug_records[:max_records_per_drug]
                        break
                    offset += page_size
                    time.sleep(0.2)
                except Exception as e:
                    print(f"Error fetching {drug} at offset {offset}: {e}")
                    break

            all_records.extend(drug_records)
            print(f"Retrieved {len(drug_records)} records for {drug}")

        df = pd.DataFrame(all_records)
        if not df.empty:
            df = df.drop_duplicates(subset=["id"])
        return df

    def clean_and_harmonize_labels(
        self,
        raw_df: pd.DataFrame,
        antibiotics: Optional[List[str]] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Harmonizes phenotypes into binary multi-labels:
        - Resistant -> 1
        - Susceptible -> 0
        - Intermediate / Non-susceptible / Missing -> NaN
        Identifies and removes conflicting records per genome-antibiotic pair.
        Returns:
            clean_labels_df: Wide dataframe with columns [genome_id, {drug}_label...]
            conflict_details_df: Detailed audit of any conflicting entries
        """
        antibiotics = [a.lower() for a in (antibiotics or TARGET_ANTIBIOTICS)]
        df = raw_df.copy()

        df["phenotype_clean"] = (
            df["resistant_phenotype"]
            .astype(str)
            .str.strip()
            .str.lower()
        )
        phenotype_map = {"resistant": 1, "susceptible": 0}
        df["binary_label"] = df["phenotype_clean"].map(phenotype_map)

        df = df[
            df["antibiotic"].str.lower().isin(antibiotics)
            & df["genome_id"].notna()
        ].copy()
        df["antibiotic"] = df["antibiotic"].str.lower()

        # Audit conflicts
        pair_summary = (
            df.dropna(subset=["binary_label"])
            .groupby(["genome_id", "antibiotic"])
            .agg(
                distinct_labels=("binary_label", "nunique"),
                records_count=("binary_label", "size")
            )
            .reset_index()
        )
        conflict_pairs = pair_summary[pair_summary["distinct_labels"] > 1]
        conflict_details = df.merge(
            conflict_pairs[["genome_id", "antibiotic"]],
            on=["genome_id", "antibiotic"],
            how="inner"
        ).sort_values(["genome_id", "antibiotic"])

        # Resolve conservatively: only keep if unambiguous 0 or 1
        def resolve_group(grp):
            vals = set(grp["binary_label"].dropna().astype(int))
            return float(next(iter(vals))) if len(vals) == 1 else np.nan

        resolved = (
            df.groupby(["genome_id", "antibiotic"])
            .apply(resolve_group, include_groups=False)
            .rename("label")
            .reset_index()
        )

        all_genomes = pd.Index(df["genome_id"].unique(), name="genome_id")
        wide = resolved.pivot(
            index="genome_id",
            columns="antibiotic",
            values="label"
        ).reindex(index=all_genomes, columns=antibiotics)

        wide.columns = [f"{c}_label" for c in wide.columns]
        wide = wide.reset_index()
        return wide, conflict_details

    def fetch_genome_fasta(
        self,
        genome_id: str,
        output_dir: Path,
        page_size: int = 1000
    ) -> Tuple[bool, int, int, Path]:
        """
        Download all contigs for a specific genome and write to FASTA file.
        Validates standard IUPAC DNA characters.
        Returns:
            (success, contig_count, total_bases, fasta_path)
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", str(genome_id))
        fasta_path = output_dir / f"{safe_id}.fna"

        records = []
        offset = 0
        endpoint = f"{self.base_url}/genome_sequence"

        while True:
            query = (
                f"eq(genome_id,{genome_id})"
                f"&select(genome_id,sequence_id,length,sequence)"
                f"&sort(+sequence_id)"
                f"&limit({page_size},{offset})"
                f"&http_accept=application/json"
            )
            url = f"{endpoint}/?{quote(query, safe='(),&+=\"')}"
            try:
                resp = self.session.get(url, timeout=120)
                resp.raise_for_status()
                data = resp.json()
                if not data:
                    break
                records.extend(data)
                if len(data) < page_size:
                    break
                offset += page_size
                time.sleep(0.2)
            except Exception as e:
                print(f"Error downloading sequence for genome {genome_id}: {e}")
                break

        valid_records = []
        for rec in records:
            seq = "".join(str(rec.get("sequence") or "").split()).upper()
            if seq and re.fullmatch(r"[ACGTRYSWKMBDHVN]+", seq):
                valid_records.append((rec, seq))

        if not valid_records:
            return False, 0, 0, fasta_path

        total_bases = 0
        contigs = 0
        seen_ids = set()

        with open(fasta_path, "w", encoding="utf-8") as f:
            for rec, seq in valid_records:
                sid = str(rec.get("sequence_id") or f"{genome_id}.contig_{contigs+1}")
                if sid in seen_ids:
                    continue
                seen_ids.add(sid)
                f.write(f">{sid} genome_id={genome_id}\n")
                for i in range(0, len(seq), 80):
                    f.write(seq[i:i+80] + "\n")
                total_bases += len(seq)
                contigs += 1

        return contigs > 0, contigs, total_bases, fasta_path

