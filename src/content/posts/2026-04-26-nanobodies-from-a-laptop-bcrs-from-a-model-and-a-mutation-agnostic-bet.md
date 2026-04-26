---
title: "Nanobodies From a Laptop, BCRs From a Model, and a Mutation-Agnostic Bet"
description: "Three signals this month, all pointing at the same thing: antibody discovery is becoming a computational discipline first and a wet-lab one second."
date: 2026-04-26
categories: ["Science", "Antibody Engineering"]
tags: []
authors: ["Sukhi Singh"]
draft: false
---

Three signals this month, all pointing at the same thing: antibody discovery is becoming a computational discipline first and a wet-lab one second.

## GPCRs were supposed to be the hard part

A new paper [1] reports nanobody binders to a G-protein coupled receptor discovered in silico using AlphaFold-Multimer. GPCRs are notoriously ugly targets. They sit in the membrane, refuse to crystallize politely, and most antibody campaigns against them die at antigen production.

So skipping the antigen and screening structures instead is a real shift. Not "AI suggested some candidates." Actual binders, validated, against a class of targets that has eaten countless discovery budgets.

The honest caveat: AlphaFold-Multimer still hallucinates interfaces, and a binder is not a drug. But the cost curve here is the story. If you can shortlist nanobody candidates from sequence alone for a GPCR, you can do it for almost anything.

## BCR modeling finally getting serious

The second piece [2] is on AI-driven BCR modeling for precision immunology. This is the part of the field I spend most of my time in. Repertoire data is abundant, structural data is sparse, and the bridge between them has been mostly hand-waving.

What I want from a BCR model is not another embedding benchmark. I want it to predict which clonotypes from a Rep-Seq run are worth expressing. That is the actual bottleneck for our customers: thousands of paired heavy/light sequences, only enough capacity to make a few hundred.

The paper is a step in that direction. Whether it generalizes across species, including the llama and Kymouse repertoires we work with, is the open question.

## A mutation-agnostic antibody walks into a clinic

Then there is Alethio's ATX-011 [3], a mutation-agnostic antibody for essential thrombocythemia. ET is a JAK2/CALR/MPL mutational mess, and most programs chase one driver at a time. Going mutation-agnostic means picking a downstream node that all the genotypes converge on.

That is the kind of target hypothesis you can only really commit to if your discovery engine is cheap enough to fail a few times. It connects to the first two stories: when in silico screening and BCR modeling drop the cost of generating credible leads, you get to be braver about target selection.

The c.$2B market framing is the press release talking. The interesting bit is the bet on biology, not the TAM slide.

## What I take from this

Antibody discovery is splitting into two halves that used to be one workflow. The computational half is getting fast and weird and ambitious. The clinical half is starting to take swings that only make sense if the upstream pipe is cheap.

For platforms like ours at ENPICOM, the implication is concrete: the value is no longer in storing repertoire data. It is in ranking it well enough that someone is willing to put a candidate from your shortlist into a patient.

Working on something similar? I'd love to hear about it, or explore what ENPICOM's IGX Platform can do for your team at [enpicom.com](https://enpicom.com)

---

## References

- **[1]** Harvey EP et al. *In silico discovery of nanobody binders to a G-protein coupled receptor using AlphaFold-Multimer*. Nature communications (2026). <https://pubmed.ncbi.nlm.nih.gov/42026072/>
- **[2]** Liu T et al. *AI-Driven BCR Modeling for Precision Immunology*. International journal of molecular sciences (2026). <https://pubmed.ncbi.nlm.nih.gov/41977475/>
- **[3]** GlobeNewswire. *Alethio Therapeutics Unveils ATX‑011, a Breakthrough, Mutation‑Agnostic Antibody for Treating Essential Thrombocythemia – a c.$2B Market, and Strengthens Leadership to Accelerate Path to IND* (2026-04-16). <https://www.globenewswire.com/news-release/2026/04/16/3275062/0/en/Alethio-Therapeutics-Unveils-ATX-011-a-Breakthrough-Mutation-Agnostic-Antibody-for-Treating-Essential-Thrombocythemia-a-c-2B-Market-and-Strengthens-Leadership-to-Accelerate-Path-to.html>
