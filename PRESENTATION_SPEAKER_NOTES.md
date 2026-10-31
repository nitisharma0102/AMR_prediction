# Presentation Speaker Notes & Delivery Script
## Project Title: AI-Driven Prediction of Antimicrobial Resistance Using Genomic Language Models
### Integrated with Coursera: Managing Projects with AI
**Teammates:** Niti Sharma, Ishita Tripathi, Vishva Shah  
**Institution:** SVKM's NMIMS University, MPSTME, Department of Computer Engineering  
**Academic Year:** 2025–2026  
**Presentation File:** [`AI_AMR_Coursera_Presentation.pptx`](file:///c:/Users/HP/Desktop/capstone_finalll/AI_AMR_Coursera_Presentation.pptx)

---

### Slide 1: Title Slide
- **Estimated Time:** 1:00 min
- **Speaker:** Niti Sharma (Opening & Team Introduction)
- **Script:**
  > "Respected evaluators, faculty members, and peers, good morning. Today, our team—comprising Ishita Tripathi, Vishva Shah, and myself, Niti Sharma—is proud to present our Capstone project: **'AI-Driven Prediction of Antimicrobial Resistance Using Genomic Language Models'**.
  > 
  > This project bridges cutting-edge computational biology with modern machine learning, specifically addressing the diagnostic delay in bacterial infection treatment. Furthermore, we have structured, governed, and delivered this initiative by integrating the end-to-end framework taught in the Coursera course **'Managing Projects with AI'**. Over the next 15 minutes, we will walk you through our clinical problem, agile project governance, genomic transformer architecture, empirical benchmarks, and production-ready clinical deployment."

---

### Slide 2: Executive Overview & Coursera PM Framework Mapping
- **Estimated Time:** 1:00 min
- **Speaker:** Niti Sharma
- **Key Talking Points:**
  - Introduce the dual core of the project: Technical innovation + rigorous AI project management.
  - Explain how each phase of the project maps directly to the 6 modules of the Coursera course:
    1. *Module 1 (Initiation):* Defining the clinical business case for *E. coli* infections.
    2. *Module 2 (Planning):* 15-week Agile sprint plan and Work Breakdown Structure (WBS).
    3. *Module 3 (Data-Driven Decisions):* Label auditing and risk mitigation matrix.
    4. *Module 4 (Team Collaboration):* AI-assisted pair programming and CI/CD quality gates.
    5. *Module 5 (Ethical AI & Bias):* Asymmetric cost of clinical False Negatives and threshold calibration.
    6. *Module 6 (Implementation & Scale):* Production Streamlit diagnostic decision support system.

---

### Slide 3: Coursera Module 1 – Project Initiation & Clinical Problem Definition
- **Estimated Time:** 1:15 min
- **Speaker:** Niti Sharma
- **Key Talking Points:**
  - *The Global AMR Threat:* 1.27 million direct deaths and 4.95 million associated deaths annually; projected to reach 10 million annual deaths by 2050 (Lancet GRAM study).
  - *The 72-Hour Diagnostic Bottleneck:* Standard culture-based antimicrobial susceptibility testing (AST) takes 48–72 hours. In acute septic shock, every single hour of delay reduces patient survival by 7.6%.
  - *The Empiric Trap:* Clinicians must guess broad-spectrum antibiotics, fueling resistance selection.
  - *Project Charter & KPIs:* Leverage Next-Generation Sequencing (WGS) to compress turnaround from 72 hours to under 15 minutes, targeting 5 major antibiotic families simultaneously with high exact-match subset accuracy.

---

### Slide 4: Coursera Module 2 – Work Breakdown Structure (WBS) & Team Governance
- **Estimated Time:** 1:15 min
- **Speaker:** Niti Sharma (Transitioning to Ishita & Vishva)
- **Key Talking Points:**
  - *Agile Scrum Methodology:* 15-week development lifecycle structured into four key sprint cycles.
  - *Specialized Accountability:*
    - **Niti Sharma (Lead Data Engineer):** Curation of 1,200+ raw *E. coli* contigs, AST laboratory label auditing, dual-strand motif scanning, 8,000 genomic chunk bag assembly.
    - **Ishita Tripathi (Lead AI/ML Researcher):** Bidirectional ProkBERT fine-tuning, Class-Wise Multi-Head Attention layer formulation in PyTorch, loss balancing.
    - **Vishva Shah (MLOps & Governance Lead):** Patient-level leak-free stratification, benchmarking against classical ML, Streamlit clinical UI engineering, and WHO/CLSI ethical governance.
  - *AI Management Tools:* GitHub Projects for sprint backlogs, automated milestone tracking, and daily standups.

---

### Slide 5: Coursera Module 3 – Data-Driven Decision Making & Label Auditing
- **Estimated Time:** 1:15 min
- **Speaker:** Niti Sharma
- **Key Talking Points:**
  - *The Data Quality Breakthrough:* Highlighting Coursera Module 3 principle that data quality dictates project outcome.
  - *The Heuristic Trap in Public Datasets:* Many public repositories label resistance computationally using BLAST or CARD rules. Models trained on such labels merely memorize bioinformatics heuristics.
  - *Strict AST Filtering:* We filtered 1,200+ raw isolates from PATRIC/NCBI, strictly enforcing `evidence == "Laboratory Method"` (broth microdilution / disk diffusion).
  - *Genomic Bag Assembly:* 8,000 chunks (900 bp) with 5,116 verified resistance determinant loci and 2,884 chromosomal background controls, formatted as bags of $M=24$ chunks with boolean padding masks.

---

### Slide 6: Technical Core I – Dual-Strand Resistome-Guided Sequence Scanning
- **Estimated Time:** 1:15 min
- **Speaker:** Niti Sharma
- **Key Talking Points:**
  - *The Strand Orientation Blindspot:* Bacterial contigs from *de novo* assemblers have arbitrary 5' to 3' orientations. 50% of bacterial resistance genes lie on the reverse-complement strand. Conventional DNA models that tokenize only forward miss half the resistome!
  - *Our Solution:* Bidirectional regex scanner querying both forward ($S_{\text{fwd}}$) and reverse-complement ($S_{\text{rev}}$) strands across 12 conserved catalytic motifs (*blaTEM*, *blaCTX-M*, *gyrA* QRDR, *parC*, *aac(3)*, *aadA*).
  - *Active Site Centering:* We center 900 bp windows directly on the catalytic residue (`start = max(0, motif_pos - 120)`), ensuring the active site consistently appears at tokens 15–35.

---

### Slide 7: Technical Core II – Class-Wise Multi-Head Attention Pooling
- **Estimated Time:** 1:30 min
- **Speaker:** Ishita Tripathi (Technical Architecture Lead)
- **Key Talking Points:**
  - *Mathematical Formulation:*
    - Input bag: $\mathbf{H} \in \mathbb{R}^{M \times d}$.
    - Non-linear projection: $\mathbf{u}_m = \tanh(\mathbf{h}_m \mathbf{W}_{\text{proj}} + \mathbf{b})$.
    - Class-specific attention vector $\mathbf{v}_k$ computes relevance scores $e_m^{(k)} = \mathbf{u}_m^\top \mathbf{v}_k$.
    - Softmax normalization with masked padding: $\boldsymbol{\alpha}^{(k)} \in \mathbb{R}^M$.
    - Class context vector: $\mathbf{c}_k = \sum_m \alpha_m^{(k)} \mathbf{h}_m \rightarrow \text{Sigmoid}(\mathbf{W}_k \mathbf{c}_k + b_k)$.
  - *Why Conventional Pooling Fails:* In a 5 Mbp genome, 99.5% is housekeeping DNA. Mean-pooling dilutes the 861 bp *blaTEM* gene into mathematical obscurity (0.0000 subset accuracy).
  - *Multi-Head Necessity:* In multi-drug resistant (MDR) bacteria, Ampicillin resistance is on a plasmid, while Ciprofloxacin resistance is on a chromosomal *gyrA* SNP. 5 independent attention heads allow both to be located simultaneously without cross-talk.

---

### Slide 8: System Architecture & Pipeline Flow
- **Estimated Time:** 1:00 min
- **Speaker:** Ishita Tripathi
- **Key Talking Points:**
  - Walk the evaluators through the four pipeline stages on the embedded architecture diagram:
    1. Raw Genomic Contigs (WGS FASTA).
    2. Dual-Strand Motif Preprocessing & Bag Construction ($M=24$).
    3. ProkBERT Bidirectional Transformer Backbone (shifted 6-mers).
    4. Class-Wise Attention Pooling $\rightarrow$ 5 Calibrated Sigmoid Classifiers $\rightarrow$ Attention Localization Map.

---

### Slide 9: Coursera Module 3 (Cont.) – Risk Management & Mitigation Matrix
- **Estimated Time:** 1:00 min
- **Speaker:** Vishva Shah (MLOps & Governance Lead)
- **Key Talking Points:**
  - Present the 4 key risk events analyzed using Coursera project risk management principles:
    1. *Clonal Lineage Leakage (ST131 Outbreaks):* Mitigated via patient-level, leak-free multi-label stratified splitting.
    2. *Class Imbalance Skew (74% AMP vs 30% CAZ):* Mitigated via positive-weighted BCE loss and validation threshold calibration ($T_k \in [0.37, 0.62]$).
    3. *Quadratic GPU Memory Overflow:* Mitigated via Multiple Instance Learning (MIL) bag chunking ($M=24 \times 900$ bp), running with zero OOM crashes on commodity CPU/GPU hardware.
    4. *Clinical False Negatives:* Mitigated by asymmetric loss tuning prioritizing clinical sensitivity.

---

### Slide 10: Coursera Module 4 – AI for Team Collaboration & Agile Productivity
- **Estimated Time:** 1:00 min
- **Speaker:** Vishva Shah
- **Key Talking Points:**
  - *AI Pair-Programming:* Accelerated PyTorch tensor vectorization and automated unit test generation.
  - *Automated CI/CD Quality Control:* 100% test pass rate across `tests/test_pipeline.py`, verifying bag masking, zero-padding, multi-head tensor shapes, and gradient propagation.
  - *Robust Exception Handling:* Embedded `torch.nan_to_num(..., nan=0.0)` in the ProkBERT backbone to eliminate PyTorch NaN edge-cases on masked bags.
  - *Reproducible Environments:* Pinned dependencies in `requirements.txt`.

---

### Slide 11: Coursera Module 5 – Ethical AI, Algorithmic Bias & Clinical Safety
- **Estimated Time:** 1:15 min
- **Speaker:** Vishva Shah
- **Key Talking Points:**
  - *Asymmetric Clinical Costs:*
    - **False Negative (Very Major Error):** Prescribing an ineffective drug to a bacteremic patient $\rightarrow$ treatment failure and sepsis death.
    - **False Positive (Major Error):** Overprescribing toxic reserve antibiotics (carbapenems, colistin) $\rightarrow$ adverse drug events and resistance escalation.
  - *Calibrated Dynamic Thresholds:* Replaced arbitrary 0.50 cutoffs with drug-specific thresholds ($T_{\text{CAZ}} = 0.37$, $T_{\text{AMP}} = 0.52$, $T_{\text{CIP}} = 0.62$).
  - *Clinical Safety Achievement:* Reached **100% Sensitivity on Ceftazidime (CAZ)**—zero false negatives on critical 3rd-generation cephalosporins!

---

### Slide 12: Empirical Validation – Comparative Performance Benchmark
- **Estimated Time:** 1:15 min
- **Speaker:** Ishita Tripathi
- **Key Talking Points:**
  - Point to the benchmark table and embedded comparison chart:
    - **ProkBERT + Class Attention (Ours):** **0.2800 Subset Accuracy**, **0.6716 Micro F1**, **0.6777 Macro ROC-AUC**.
    - **XGBoost (k-mers):** 0.0800 Subset Accuracy (our model is **3.5x higher**).
    - **Random Forest:** 0.0400 Subset Accuracy (our model is **7x higher**).
    - **Mean-Pooling Transformer:** 0.0000 Subset Accuracy (completely collapses due to background signal dilution).
  - Highlights: This proves empirically that class-wise attention is not just an optimization, but a fundamental biological requirement for multi-label AMR prediction.

---

### Slide 13: Diagnostic Validation – ROC & Confusion Matrix Analysis
- **Estimated Time:** 1:00 min
- **Speaker:** Ishita Tripathi
- **Key Talking Points:**
  - Analyze the embedded ROC curves: Macro AUC-ROC reaches **0.7681** across drug classes.
  - Review drug-specific highlights from the confusion matrices:
    - *Ceftazidime (CAZ):* 100% recall (8/8 resistant isolates correctly identified).
    - *Ampicillin (AMP):* 88.9% recall, 84.2% precision.
    - *Cefotaxime (CTX):* 88.9% recall.
    - *Ciprofloxacin (CIP):* 85.7% precision.

---

### Slide 14: Mechanistic Explainability – Genomic Attention Heatmap
- **Estimated Time:** 1:15 min
- **Speaker:** Ishita Tripathi
- **Key Talking Points:**
  - Explain how our architecture solves the "black-box" clinical trust barrier:
    - The *Ampicillin head* concentrates over 65% of its attention mass specifically on chunk 3, which harbors the *blaTEM* $\beta$-lactamase gene.
    - The *Ciprofloxacin head* isolates chunk 7, corresponding to the *gyrA* QRDR Ser83Leu chromosomal point mutation.
    - The *Gentamicin head* isolates the *aac(3)* aminoglycoside acetyltransferase chunk.
  - The model autonomously tells the clinician *which specific resistance determinant* was detected, satisfying FDA and European medical AI explainability criteria.

---

### Slide 15: Coursera Module 6 – Implementation, Streamlit Dashboard & Production Scale
- **Estimated Time:** 1:15 min
- **Speaker:** Vishva Shah
- **Key Talking Points:**
  - *Operationalizing the Research:* We transformed our model into an interactive clinical decision support application in `app/app.py`.
  - *Clinician Workflow:* Upload raw whole-genome FASTA contigs $\rightarrow$ Automated dual-strand resistome scanning $\rightarrow$ Instant calibrated susceptibility report $\rightarrow$ Interactive attention heatmaps.
  - *Production SLAs:*
    - Inference latency: **< 1.2 seconds** on standard CPU.
    - 100% offline capable (air-gapped hospital network security, zero HIPAA/GDPR cloud leakage).
    - Lightweight model footprint (< 50 MB PyTorch checkpoint).

---

### Slide 16: Project Closure, Key Achievements & Value Delivery
- **Estimated Time:** 1:00 min
- **Speaker:** Niti Sharma
- **Key Talking Points:**
  - *Summary of Delivered Value:*
    - **72 hours $\rightarrow$ < 15 minutes:** Diagnostic turnaround compressed by over 99%.
    - **3.5x Exact-Match Multi-Drug Diagnostic Improvement** over state-of-the-art XGBoost.
    - Complete suite of academic deliverables: Open-source PyTorch codebase, Streamlit web app, 46-page NMIMS Black Book, 15-week Capstone Log Book, and IEEE Review Paper.
  - *Coursera AI Project Management Lessons:*
    - Data quality and label auditing outweigh model scale.
    - Architecture must mirror underlying domain biology.
    - Ethical threshold calibration is non-negotiable in healthcare AI.

---

### Slide 17: Conclusion, Team Credits & Q&A
- **Estimated Time:** 1:00 min
- **Speaker:** Niti Sharma (Closing)
- **Script:**
  > "In conclusion, our project demonstrates that by combining prokaryote-specific language models with Class-Wise Attention Pooling and strict AI project management principles, we can deliver clinically safe, explainable, and lightning-fast antimicrobial resistance diagnostics.
  > 
  > On behalf of Ishita Tripathi, Vishva Shah, and myself, Niti Sharma, we express our sincere gratitude to our faculty mentors and evaluators. We are now open and eager for your questions."

---

## 💡 Anticipated Evaluator Q&A & Recommended Responses

| Question | Recommended Answer |
|---|---|
| **Q1: Why did you choose ProkBERT over larger models like DNABERT-2 or Nucleotide Transformer?** | "While models like Nucleotide Transformer are large (2.5B parameters), they are trained heavily on eukaryotic genomes and use non-overlapping 6-mers. ProkBERT is pre-trained exclusively on 17,100 bacterial assemblies using shifted overlapping 6-mers ($k6s1/k6s2$). This preserves all three translational reading frames on both strands, perfectly capturing compact bacterial operons with zero eukaryotic bias and a lightweight parameter footprint." |
| **Q2: Why is exact-match subset accuracy so much harder than individual drug accuracy?** | "In multi-label classification across 5 drugs, a model gets zero subset accuracy if even 1 of the 5 drug predictions is incorrect ($2^5 = 32$ possible phenotype permutations). Standard models like XGBoost achieve only 0.0800 because errors compound across independent drug heads. Our class-wise attention mechanism shares a rich bidirectional backbone while isolating attention scoring, achieving 0.2800 (a 3.5x improvement)." |
| **Q3: How does your project manage data leakage across closely related hospital strains?** | "As highlighted in Lüftinger et al. (Frontiers 2021) and Module 3 of our Coursera framework, hospital outbreaks often feature clonal expansion of identical sequence types (e.g., *E. coli* ST131). If contigs or chunks from the same isolate are randomly split, the model memorizes lineage markers rather than resistance determinants. We enforced strict isolate-level / patient-level stratified splitting so that train and test partitions never share contigs from the same biological isolate." |
| **Q4: How did the Coursera course 'Managing Projects with AI' influence your technical development?** | "The Coursera course provided the governance structure that prevented project failure. Specifically: Module 3 guided our decision to audit and filter out noisy computational BLAST labels in favor of strict laboratory microdilution AST ground truth. Module 5 guided our asymmetric clinical threshold calibration, ensuring we achieved 100% sensitivity on Ceftazidime to prevent fatal false negatives in bacteremia." |

