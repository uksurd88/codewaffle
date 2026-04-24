---
title: "Nanobodies in silico, rabbits in wet lab, and a mutation-agnostic antibody that skips the JAK2 debate"
description: "Antibody discovery is splitting into two cultures. One trusts the model. The other trusts the rabbit. Both had a good month."
date: 2026-04-24
categories: ["Science", "Antibody Engineering"]
tags: []
authors: ["Sukhi Singh"]
draft: false
---

Antibody discovery is splitting into two cultures. One trusts the model. The other trusts the rabbit. Both had a good month.

## The AlphaFold-Multimer pipeline finally produced GPCR binders

A new paper describes nanobody binders to a G-protein coupled receptor discovered entirely in silico using AlphaFold-Multimer [1]. GPCRs are the punishing case: flexible, membrane-embedded, historically brutal for structure-based design. Getting nanobody hits without a single panning round is the part worth pausing on.

The caveat nobody in the press release will mention: in silico hit rates still live or die by the library you screen against. Multimer scoring is noisy at the tails, and a top-ranked binder is not a developable one. You still need affinity maturation, specificity counter-screens, and the usual liability filters. What changed is the entry point, not the finish line.

Parallel to this, another group published an AI-driven BCR modeling framework aimed at precision immunology [2]. The trend is clear. Repertoire data is becoming the substrate that generative models want to be trained on, not just analyzed with.

## Rabbits are not obsolete

Against that backdrop, a naïve rabbit antibody library paper is a useful reality check [3]. NGS profiling of rabbit repertoires for monoclonal selection is not glamorous work. It is, however, how a lot of real therapeutic leads still get found, especially for targets where human and mouse repertoires keep failing.

The interesting bit is the pairing: naïve library plus deep sequencing plus downstream selection. This is exactly the workflow shape where the in silico tools slot in as a pre-filter, not a replacement. You sequence the library, you model the binders, you triage before you touch a plate. That is the honest near-term integration story.

People keep framing this as AI versus wet lab. It is not. It is AI reducing the search space so the wet lab burns less reagent on obvious losers.

## Mutation-agnostic as a design philosophy

Alethio Therapeutics unveiled ATX-011, pitched as a first-in-class mutation-agnostic antibody for essential thrombocythemia, targeting a roughly two billion dollar market [4]. ET is a JAK2, CALR, MPL mess. Most programs chase one mutation class and leave the others on the table.

Mutation-agnostic is an interesting framing because it implies targeting a downstream node or a surface epitope common to the disease state rather than the driver mutation itself. If it holds up, it is a template other MPN programs will copy. If it does not, it will be because pathway redundancy bit them, which is the usual failure mode for anything labeled agnostic.

I am withholding enthusiasm until there is human data. But the target selection logic is the right kind of ambitious.

## What I keep thinking about

The three stories rhyme. In silico binder discovery, rabbit repertoire NGS, and a clinical program built on epitope logic rather than mutation logic. All three assume you can reason about antibodies at the sequence and structure level before you commit to a molecule. That assumption is cheaper to act on every quarter.

The platforms that win the next five years are the ones that treat repertoire data, structural prediction, and wet lab validation as one loop, not three handoffs. Most teams still treat them as three handoffs.

Working on something similar? I'd love to hear about it, or explore what ENPICOM's IGX Platform can do for your team at [enpicom.com](https://enpicom.com)

---

## References

- **[1]** Harvey EP et al. *In silico discovery of nanobody binders to a G-protein coupled receptor using AlphaFold-Multimer*. Nature communications (2026). <https://pubmed.ncbi.nlm.nih.gov/42026072/>
- **[2]** Liu T et al. *AI-Driven BCR Modeling for Precision Immunology*. International journal of molecular sciences (2026). <https://pubmed.ncbi.nlm.nih.gov/41977475/>
- **[3]** Rodríguez S et al. *Generation and NGS profiling of naïve rabbit antibody libraries for efficient monoclonal antibody selection*. New biotechnology (2026). <https://pubmed.ncbi.nlm.nih.gov/41389987/>
- **[4]** GlobeNewswire. *Alethio Therapeutics Unveils ATX‑011, a Breakthrough, Mutation‑Agnostic Antibody for Treating Essential Thrombocythemia – a c.$2B Market, and Strengthens Leadership to Accelerate Path to IND* (2026-04-16). <https://www.globenewswire.com/news-release/2026/04/16/3275062/0/en/Alethio-Therapeutics-Unveils-ATX-011-a-Breakthrough-Mutation-Agnostic-Antibody-for-Treating-Essential-Thrombocythemia-a-c-2B-Market-and-Strengthens-Leadership-to-Accelerate-Path-to.html>
