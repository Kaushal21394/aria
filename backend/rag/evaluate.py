"""
RAGAS evaluation harness for ARIA Phase 3.

Runs 4 RAGAS metrics against a held-out Q&A test set derived from the proposals
corpus to measure RAG quality:

    faithfulness        — Is the answer grounded in retrieved context?
    answer_relevancy    — Does the answer address the question?
    context_precision   — Were the right chunks retrieved?
    context_recall      — Were all relevant chunks retrieved?

Usage:
    python -m backend.rag.evaluate

Requirements (installed via requirements.txt):
    ragas>=0.1.21,<0.2.0
    datasets
"""
from __future__ import annotations

import json
import logging
import os
import sys

# Ensure the project root is on the path when run as __main__
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from backend.rag.retrieval import format_rag_context, retrieve_proposals

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

# ---------------------------------------------------------------------------
# 20-question evaluation dataset
# Each entry: question, ground_truth answer, optional TA filter for retrieval
# ---------------------------------------------------------------------------
EVAL_QUESTIONS = [
    {
        "question": "What oncology Phase II studies has Meridian run in North America?",
        "ground_truth": (
            "Meridian has run multiple Phase II oncology studies in North America, including "
            "a HER2+ bispecific antibody study (Arpex Oncology, 48 patients, 12 US/Canada sites), "
            "an IDH2 inhibitor study in relapsed/refractory AML (Novara Therapeutics, 85 patients, "
            "18 US sites), and an anti-PD-L1 plus SBRT Phase I/II study (Helix Immuno, 6 NCI centers)."
        ),
        "ta_filter": "oncology",
    },
    {
        "question": "Does Meridian have experience with gene therapy trials?",
        "ground_truth": (
            "Yes. Meridian ran a landmark Phase III AAV9 gene therapy study in SMA Type I infants "
            "(GenPathways, 45 patients, 9 global sites) that resulted in BLA approval, and a Phase I "
            "intrathecal AAV-BDNF gene therapy study in spinal cord injury (SpineGenix, 18 patients, "
            "4 US centers). Both resulted in wins and follow-on work."
        ),
        "ta_filter": None,
    },
    {
        "question": "What rare disease studies has Meridian conducted in Europe?",
        "ground_truth": (
            "Meridian ran a Phase III enzyme replacement therapy study in Fabry disease with "
            "cardiomyopathy (FabryGen, 120 EU/US patients) that received EU MA, and an ongoing "
            "Phase III adaptive design study in Huntington's disease (AdaptaNeuro, 300 patients, "
            "45 EU sites)."
        ),
        "ta_filter": "rare_disease",
    },
    {
        "question": "What cardiovascular outcomes trials has Meridian managed?",
        "ground_truth": (
            "Meridian managed two large CVOTs: a Phase III HFpEF outcomes trial for HeartFirst Pharma "
            "(2,800 patients, 220 global sites, composite MACE endpoint) and a Phase III Type 2 "
            "diabetes CVOT for GlucoPharm International (5,000 patients, 320 global sites, 3-point "
            "MACE). Both studies met primary endpoints and resulted in NDA filings."
        ),
        "ta_filter": "cardiology",
    },
    {
        "question": "Has Meridian worked on any obesity or GLP-1 related studies?",
        "ground_truth": (
            "Yes. Meridian ran a Phase II dose-ranging study for ObesiCure Bio testing a GLP-1 "
            "agonist/amylin analog combination (OCB-12) in 320 adults with BMI ≥30 across 24 US "
            "obesity medicine centers. The study established dose-response and led to a Phase III "
            "agreement. Meridian also ran a Phase III CVOT for a SGLT2/GLP-1 dual agonist in "
            "Type 2 diabetes (GlucoPharm, 5,000 patients globally)."
        ),
        "ta_filter": "metabolic",
    },
    {
        "question": "What respiratory disease trials has Meridian run in Europe?",
        "ground_truth": (
            "Meridian ran a Phase II anti-IL-5 biologic study in eosinophilic asthma (BioAsthma EU, "
            "240 patients, 30 EU sites) and a Phase III COPD triple combination inhaler study "
            "(AirPath, 2,200 global patients with EU enrollment). Both were wins that led to "
            "follow-on Phase III or NDA submissions."
        ),
        "ta_filter": "respiratory",
    },
    {
        "question": "What studies has Meridian lost and why?",
        "ground_truth": (
            "Meridian has lost studies due to: insufficient radioligand therapy site infrastructure "
            "(Cascadia Bio Phase III prostate cancer), limited IPF-specific site experience "
            "(FibroLung Sciences Phase III), lack of interventional cardiology procedure monitoring "
            "capability (PressureLow Bio), limited Japan regulatory experience for a multi-regional "
            "hATTR study (TransAmyloid), limited ALS site network (NeuralPath), and PRO/ePRO "
            "capability gaps in GI oncology (Pathogen Therapeutics)."
        ),
        "ta_filter": None,
    },
    {
        "question": "What neurology Phase III studies has Meridian run?",
        "ground_truth": (
            "Meridian has run Phase III neurology studies including: an anti-tau antibody in "
            "Alzheimer's disease (AlzClear, 800 patients, 90 global sites, met co-primary endpoints), "
            "a CGRP antagonist in chronic migraine (Cepha Bio, 650 patients, 80 US/EU sites, NDA "
            "filed), and a voltage-gated sodium channel modulator in drug-resistant epilepsy "
            "(EpilexPharma, 420 patients, dual pediatric/adult cohorts)."
        ),
        "ta_filter": "neurology",
    },
    {
        "question": "Has Meridian conducted any studies in Asia-Pacific?",
        "ground_truth": (
            "Yes. Meridian ran a Phase III atrial fibrillation study in Asia-Pacific for PacificHeart "
            "KK (1,200 patients, 80 APAC sites, PMDA submission), a Phase III gout study for "
            "PharmaGout Asia (700 patients, 40 APAC sites, Japan PMDA submission accepted), and "
            "a Phase II rare disease study that required Asia-Pacific sites (though was lost to a "
            "competitor due to Japan regulatory gaps)."
        ),
        "ta_filter": None,
    },
    {
        "question": "What immunology trials has Meridian conducted and what were the outcomes?",
        "ground_truth": (
            "Meridian has won multiple immunology trials: a Phase III JAK inhibitor in RA "
            "(RheumaVance, 900 patients, both co-primary endpoints met, NDA filed), a Phase II "
            "anti-IL-17 bispecific in psoriasis (SkinClear EU, PASI 90 confirmed), a Phase III "
            "IL-4Rα antagonist in atopic dermatitis (AtopyRx, FDA approved), a Phase II anti-IFNAR1 "
            "in SLE (LupusMed, Phase III initiated), and an ongoing Phase II anti-TL1A in Crohn's "
            "disease (GutImmune, 50% enrolled)."
        ),
        "ta_filter": "immunology",
    },
    {
        "question": "Does Meridian have experience with CAR-T or cell therapy trials?",
        "ground_truth": (
            "Yes. Meridian ran a Phase I CAR-T leukapheresis logistics study for CellVector Bio "
            "(24 patients, 6 US authorized treatment centers, large B-cell lymphoma). Meridian "
            "developed a proprietary chain-of-custody tracking system with 0% temperature excursion "
            "rate across 48 shipments. This established Meridian as a preferred cell therapy "
            "logistics partner."
        ),
        "ta_filter": "oncology",
    },
    {
        "question": "What studies has Meridian run involving digital or wearable endpoints?",
        "ground_truth": (
            "Meridian ran a Phase II Parkinson's disease study for NeuroMotion Bio using a novel "
            "wearable-based tremor/bradykinesia composite endpoint. Meridian's digital health team "
            "built a custom EDC integration for wearable data ingestion. Device data quality exceeded "
            "the FDA pre-specified acceptability threshold, and the methodology was highlighted at "
            "IAPRD as a methodological innovation."
        ),
        "ta_filter": "neurology",
    },
    {
        "question": "What infectious disease trials has Meridian managed?",
        "ground_truth": (
            "Meridian managed a Phase III RSV vaccine efficacy study for VaxShield Bio (22,000 "
            "patients, 120 global sites, 2 RSV seasons — the largest single study Meridian has "
            "managed) and a Phase II long-acting HIV injectable study for LongActRx (200 patients, "
            "US and sub-Saharan Africa sites). Both were wins."
        ),
        "ta_filter": "infectious_disease",
    },
    {
        "question": "What is Meridian's experience with adaptive design trials?",
        "ground_truth": (
            "Meridian has run adaptive design studies including: a Phase II dose-escalation "
            "oncology study with adaptive dose-escalation SMC review (Arpex), an ongoing Phase III "
            "Huntington's disease study with adaptive sample size re-estimation (AdaptaNeuro), and "
            "an ongoing Phase III MASH study with a screen failure mitigation sub-strategy "
            "(LiverStrat)."
        ),
        "ta_filter": None,
    },
    {
        "question": "Has Meridian worked with small biotech sponsors on Phase I studies?",
        "ground_truth": (
            "Yes. Meridian has worked with multiple small biotech sponsors on Phase I studies: "
            "Arpex Oncology (HER2+ bispecific, Phase I/II), Helix Immuno (anti-PD-L1 + SBRT, "
            "Phase I), CellVector Bio (CAR-T logistics, Phase I), SpineGenix (gene therapy "
            "intrathecal, Phase I), and PulmoVex Bio (PAH, Phase II, small sponsor). All resulted "
            "in wins and follow-on agreements."
        ),
        "ta_filter": None,
    },
    {
        "question": "What metabolic disease studies has Meridian conducted in Europe?",
        "ground_truth": (
            "Meridian ran a Phase II Type 1 diabetes immunomodulation study in pediatric patients "
            "for ImmunoSugar Bio (120 patients, 18 EU academic pediatric diabetes centers), which "
            "led to EU PIP grant and Phase III award. An ongoing Phase III MASH study "
            "(LiverStrat, 950 global patients with EU enrollment) is also in progress."
        ),
        "ta_filter": "metabolic",
    },
    {
        "question": "What is Meridian's track record with FDA Breakthrough Therapy Designation?",
        "ground_truth": (
            "Meridian has supported FDA Breakthrough Therapy Designation for multiple sponsors: "
            "CardiGene Therapeutics (HCM cardiac myosin inhibitor, BTD granted after Phase II), "
            "PulmoVex Bio (PAH soluble guanylate cyclase stimulator, BTD granted), and "
            "LysoCure Bio (Gaucher disease Type III, Accelerated Approval pathway granted)."
        ),
        "ta_filter": None,
    },
    {
        "question": "Has Meridian run any COPD or spirometry-focused trials?",
        "ground_truth": (
            "Yes. Meridian ran a Phase III COPD triple combination inhaler study for AirPath "
            "Therapeutics (2,200 patients, 160 global sites, trough FEV1 and exacerbation rate "
            "endpoints). Meridian's centralized spirometry quality program achieved <4% unusable "
            "assessments vs. ~12% industry average, and was cited by FDA in the statistical review."
        ),
        "ta_filter": "respiratory",
    },
    {
        "question": "What large Phase III global studies has Meridian managed with >500 patients?",
        "ground_truth": (
            "Meridian has managed many large Phase III global studies including: a CVOT in HFpEF "
            "(2,800 patients), a Type 2 diabetes CVOT (5,000 patients), an RSV vaccine efficacy "
            "study (22,000 patients), a Phase III NSCLC study (620 patients, 85 sites), a Phase III "
            "COPD study (2,200 patients), and a Phase III RA JAK inhibitor study (900 patients)."
        ),
        "ta_filter": None,
    },
    {
        "question": "What is Meridian's experience with EU regulatory submissions and GCP inspections?",
        "ground_truth": (
            "Meridian has strong EU regulatory experience. Key examples: managed 9 simultaneous EU "
            "member state submissions for ImmunoCNS (MS study), achieved zero critical findings in "
            "an EMA GCP inspection on the FabryGen Fabry disease study, managed all EU submissions "
            "and import licenses for EurOncology (ovarian cancer), and led EU Pediatric Investigation "
            "Plan (PIP) for ImmunoSugar Bio's Type 1 diabetes study."
        ),
        "ta_filter": None,
    },
]


def run_evaluation() -> dict:
    """
    Run the full RAGAS evaluation on the 20-question test set.

    Returns:
        Dict mapping metric names to mean scores.
    """
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )
    except ImportError as e:
        raise ImportError(
            f"Missing evaluation dependency: {e}. "
            "Install with: pip install 'ragas>=0.1.21,<0.2.0' datasets"
        ) from e

    import anthropic

    # RAGAS uses the LLM to score — set the OpenAI key so it can call gpt-3.5-turbo
    os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

    logger.info("Generating answers for %d evaluation questions…", len(EVAL_QUESTIONS))

    records = []
    for item in EVAL_QUESTIONS:
        q = item["question"]
        ta = item.get("ta_filter")

        # Retrieve relevant chunks
        hits = retrieve_proposals(query=q, therapeutic_area=ta, top_k=3)
        context_texts = [h["text"] for h in hits]
        context_block = format_rag_context(hits)

        # Generate answer using the ARIA model
        system = (
            "You are a CRO knowledge assistant. Answer questions about Meridian CRO's past work "
            "using ONLY the proposal context provided. Be specific and cite proposal details."
        )
        user_msg = f"Context:\n{context_block}\n\nQuestion: {q}"

        client = anthropic.Anthropic()
        response = client.messages.create(
            model=os.getenv("ARIA_MODEL", "claude-haiku-4-5-20251001"),
            max_tokens=400,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        answer = response.content[0].text

        records.append({
            "question":     q,
            "answer":       answer,
            "contexts":     context_texts,
            "ground_truth": item["ground_truth"],
        })
        logger.info("  ✓ %s", q[:70])

    logger.info("Running RAGAS evaluation…")
    dataset = Dataset.from_list(records)
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )

    scores_df = result.to_pandas()
    metric_cols = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    mean_scores = {
        m: round(float(scores_df[m].mean()), 4)
        for m in metric_cols
        if m in scores_df.columns
    }

    print("\n=== RAGAS Evaluation Results ===")
    for metric, score in mean_scores.items():
        bar = "█" * int(score * 20)
        print(f"  {metric:<24} {score:.4f}  {bar}")
    print()

    return mean_scores


if __name__ == "__main__":
    scores = run_evaluation()
    print(json.dumps(scores, indent=2))
