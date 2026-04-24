---
title: "Antibodies as Biomarkers: The Signal We Keep Underusing"
description: "Everyone wants a blood test. Almost no one wants to talk about what's actually in the blood that's most informative. The antibody repertoire is the most data-rich biomarker in the body, and we treat i"
date: 2026-04-24
categories: ["Science", "Antibody Engineering"]
tags: []
authors: ["Sukhi Singh"]
draft: false
---

Everyone wants a blood test. Almost no one wants to talk about what's actually in the blood that's most informative. The antibody repertoire is the most data-rich biomarker in the body, and we treat it like a footnote.

Think about what a B cell receptor repertoire actually encodes. Decades of exposures. Current infections. Pre-symptomatic autoimmunity. Vaccine response. Tumor surveillance. Each person carries roughly a trillion-copy archive of immunological history, written in VDJ rearrangements. Most clinical workflows sample almost none of it.

## Why the field stalled

The classical biomarker playbook was built for small molecules and single proteins. Pick an analyte, build an ELISA, set a cutoff. Antibody repertoires don't fit. The signal isn't one molecule at a given concentration. It's the shape of a distribution: clonal expansion, CDR3 convergence, isotype class switching, somatic hypermutation load.

That's a statistics problem disguised as an assay problem. For years we didn't have the sequencing depth, the reference repertoires, or the computational infrastructure to make it tractable. We do now. The bottleneck moved from wet lab to interpretation, and interpretation has been slow to catch up.

The other problem is that repertoire signatures are cohort-dependent. A clonotype that screams lupus in one population looks like background in another. Without harmonized reference data across ethnicities, ages, and exposure histories, you get beautiful single-study results that refuse to replicate.

## Where it's actually working

Minimal residual disease in B-cell malignancies is the cleanest win. Sequence the dominant clone at diagnosis, track it over time at a sensitivity a flow panel cannot touch. The FDA has approved this logic. Patients are alive because of it.

Infection serology using repertoire sequencing is the next obvious step. Convergent antibody signatures after SARS-CoV-2, dengue, and HIV exposure are now well-documented. Public clonotypes, shared across unrelated donors, give you a way to read past exposure from a single sample without needing the original antigen. That matters for outbreak surveillance and for vaccine development when you're trying to figure out who responded and who didn't.

Autoimmunity is the hardest and most interesting. Pre-diagnostic signatures in type 1 diabetes and rheumatoid arthritis show up years before clinical presentation. The problem is specificity. Healthy people carry autoreactive clones too. Distinguishing dangerous from tolerated is still an open question, and it's where machine learning on paired heavy-light chain data will earn its keep.

## What's still overhyped

Every few months a paper claims a universal cancer-detection signature from serum antibodies. Most don't replicate. The biology is real, the statistics usually aren't. If your training cohort has 80 patients and 80 controls and you report AUC 0.95, I am going to assume overfitting until a second site proves otherwise.

"Liquid biopsy" pitches that fold antibody signals into cfDNA panels also deserve scrutiny. Combining modalities is sensible. Pretending they report on the same biology is not.

## My take

The interesting frontier isn't finding new biomarkers. It's building the infrastructure to make repertoire-based ones usable at clinical scale: standardized protocols, shared reference datasets, and analytic pipelines that cross institutional boundaries. This is where platforms matter more than papers. Whoever solves the harmonization problem ends up owning the category.

At ENPICOM we spend a lot of time on exactly this plumbing: clonotype tracking, public-repertoire queries, cross-cohort comparisons. Less glamorous than discovering a new signature. More useful in the long run.

Working on something similar? I'd love to hear about it, or explore what ENPICOM's IGX Platform can do for your team at [enpicom.com](https://enpicom.com)