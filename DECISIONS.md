# Decisions

Newest last. Each entry is committed with the work it describes; "Commit" names that commit's subject.

## 1. Offline baseline first, standard library only
- **When:** 2026-11-05 00:23 IST
- **Commit:** Offline BM25 coder as the no-key path
- **Decision:** Build the no-key path before anything that needs an API key: BM25 over each MMS title plus its ancestors' titles, a clinical abbreviation and lay-term list, US to UK spelling (MMS titles are UK English), negated phrases dropped, and the diagnosis line (A:, Dx, Imp) weighted 4x. A parent hit is pushed down to its best-scoring leaf, or to its .Z child when no child scores higher, because gold is always a leaf.
- **Options:** TF-IDF with scikit-learn; local embeddings; BM25 in plain Python. Plain Python keeps the image small and builds anywhere; embeddings can come later if the no-key path matters more than I expect.
- **Evidence:** All 61 dev gold codes are leaves; 14 are .Z. First run: SCORE 35.4/75 (top1 0.400, top3 0.617), 60 notes in under 2 s.
- **Revisit:** Real synonyms from WHO (index terms, inclusions) instead of my hand list.

## 2. Down-weight traditional medicine and "other specified" codes
- **When:** 2026-11-05 00:23 IST
- **Commit:** Offline BM25 coder as the no-key path
- **Decision:** Multiply chapter 26 (traditional medicine) scores by 0.3 and residual .Y codes by 0.8.
- **Options:** Drop chapter 26 entirely; leave scores alone.
- **Evidence:** "Thrush disorder (TM1)" and "Dysentery disorder (TM1)" beat the real codes, and .Y siblings beat .Z. SCORE 35.4 -> 41.7 (top1 0.400 -> 0.517). Kept chapter 26 reachable since a hidden note could still be coded there.
- **Revisit:** Learn these priors from more labelled notes than 60.
