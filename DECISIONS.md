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

## 3. Keys stay out of the repo, the image and the logs
- **When:** 2026-11-05 00:33 IST
- **Commit:** Keep API keys out of the repo and the image
- **Decision:** Keys come only from the environment. `.env` is git-ignored and docker-ignored, `.env.example` has empty values, and a pre-commit hook (`scripts/pre-commit`, copy to `.git/hooks`) refuses staged text shaped like an OpenAI or Anthropic key. The deliverable is `git bundle --all`, so one committed key would ship with every ref.
- **Options:** Rely on .gitignore alone; a secrets scanner such as gitleaks. The hook is ten lines and needs nothing installed.
- **Evidence:** Hook tested with a fake `sk-ant-...` string: commit refused, HEAD unchanged.
- **Revisit:** Nothing; this is cheap insurance.

## 4. Model path: extract, shortlist, choose
- **When:** 2026-11-05 00:33 IST
- **Commit:** Model path: extract diagnoses, shortlist codes, choose
- **Decision:** Two calls per note. (1) The model reads the note in any language and returns English diagnosis terms, the details that decide specificity, and its own code guesses. (2) BM25 searches the MMS with those terms; every hit is expanded to all leaves under its 4-character stem so the specific child is always on the list; the model then picks up to 3 codes from that list only. Output codes are checked against the MMS; a parent is pushed to its .Z child; empty slots are filled from the offline coder.
- **Options:** One call with the model coding from memory (models know ICD-10 far better than ICD-11 codes, so invalid or outdated codes are likely); embeddings over titles (needs an embedding model at run time or in the image); a single call with a fixed BM25 shortlist from the raw note (gold was on that list for only 44/60 dev notes).
- **Evidence:** Without the model, the shortlist from note text alone contains gold for 44/60 notes, median 15 codes. Stub tests cover: invalid codes and an injected "IGNORE PREVIOUS" string dropped, auth errors disabling a provider, the spend cap stopping calls.
- **Revisit:** Measure with a real key; try one call instead of two if cost or time is tight.

## 5. Run-time guards for the 60-minute and $6 caps
- **When:** 2026-11-05 00:33 IST
- **Commit:** Model path: extract diagnoses, shortlist codes, choose
- **Decision:** Write offline predictions for every note first, then overwrite each note's line as its model answer arrives (atomic rewrite of the whole file). 12 worker threads, stop starting notes after 50 minutes (`CODER_TIME_BUDGET_S`) or an estimated $5.50 (`CODER_BUDGET_USD`). Anthropic first if its key is set, OpenAI second; an auth, permission or not-found error drops that provider for the rest of the run.
- **Options:** Append lines as they finish (score.py keeps the first line per id, so a later better answer could never replace an earlier fallback); one provider only (the graders may supply only one of the two keys).
- **Evidence:** No-key run still scores 41.7/75 and every id is written.
- **Revisit:** Worker count once rate limits on the graders' keys are known; OpenAI model choice (picked from a preference list via the models endpoint, untested).

## 6. Docker: slim Python image, data baked in, keys only at run time
- **When:** 2026-11-05 00:33 IST
- **Commit:** Docker image and compose service (not built locally yet)
- **Decision:** `python:3.13-slim` with two pinned SDKs; the MMS file is copied into the image so the run needs no network except the model APIs. Compose passes the keys and proxy variables through from the caller's environment and mounts `./in` and `./out`.
- **Options:** Bake an index file into the image (index builds in about 1.5 s at start, not worth it yet).
- **Evidence:** None yet: Docker is not installed on this laptop, so the image is unbuilt. Must build and run from a fresh clone before submitting.
- **Revisit:** How the graders mount /in and /out (asked by email).

## 7. Develop on a free Gemini key, confirm on Claude before submitting
- **When:** 2026-11-05 00:48 IST
- **Commit:** Develop against a free Gemini key through the OpenAI client
- **Decision:** For day-to-day dev runs, point the OpenAI client at Gemini's OpenAI-compatible endpoint with `OPENAI_BASE_URL` and `CODER_OPENAI_MODEL` in my local `.env`. No code change; compose does not pass `OPENAI_BASE_URL`, so the graded container always talks to api.openai.com or api.anthropic.com.
- **Options:** Pay for Anthropic credit from the start; free OpenRouter models (about 50 requests a day, one dev run needs 120).
- **Evidence:** Client resolves the Gemini base URL from the environment alone (checked with a dummy key, no network). Pre-commit hook now also refuses Google-style `AIza...` keys, tested with a fake one.
- **Revisit:** Gemini scores are not what the graders will see; run the dev set once on Claude Haiku 5.5 before submitting.
