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

## 8. WHO index terms from the offline WHO container, not the online API
- **When:** 2026-11-05 00:58 IST
- **Commit:** Use WHO index terms and inclusions when downloaded; test-note generator
- **Decision:** The brief hints that WHO publishes much more than titles. Each MMS entity in the ICD-API carries index terms (synonyms, lay and local names) and inclusions. `scripts/fetch_who.py` pulls them for all 18,375 codes from WHO's free `whoicd/icd-api` Docker container (licence accepted with one flag, no account), or from the online API with a client id and secret. They feed the BM25 index and are shown next to each candidate in the model's shortlist ("also: ..."). The tokenizer is now Unicode-aware so translated titles can be added the same way.
- **Options:** Online API (needs registration; 18k authenticated calls); scraping the ICD browser (not acceptable); asking the model to write synonyms (slow, and it invents terms).
- **Evidence:** With a one-entry stand-in file, "chigoe" codes to 1G05 Tungiasis and the shortlist line shows the synonyms. Dev score unchanged at 41.7 with no WHO data present. Real download waits for Docker on this laptop.
- **Revisit:** Index term weight in BM25 once the real file is in; which translations help the generalisation slice.

## 9. Synthetic notes to test beyond the 60 dev notes
- **When:** 2026-11-05 00:58 IST
- **Commit:** Use WHO index terms and inclusions when downloaded; test-note generator
- **Decision:** `scripts/make_synth.py` samples one leaf per note evenly across chapters 01-24 (skipping 23 external causes and .Y codes), a style and a language (about half English; French, Swahili, Spanish, Portuguese, Arabic, Hindi, Amharic), and has the model write a note that fits exactly that code: with the deciding details for a specific code, without them for a .Z code. Written as slice B so score.py reports it apart from the dev set.
- **Options:** Hold out part of the 60 dev notes (too few, and same narrow chapters); hand-write notes (slow, and I am not a clinician).
- **Evidence:** 150 samples cover 23 chapters, 30 are .Z (dev: 14 of 61). Not generated yet; needs a key.
- **Revisit:** Gold here is only as good as the writer; read a sample by hand and drop notes that don't support their code.

## 10. Fail fast when the model API is unreachable; fall back across Claude models
- **When:** 2026-11-05 01:15 IST
- **Commit:** Drop an unreachable provider after 10 errors; fall back across Claude models
- **Decision:** The brief warns that a client that ignores `HTTPS_PROXY` fails every call. Each provider is now dropped after 10 errors in a row (reset on any success), and a temporary error on one provider falls through to the next for that call. If the key cannot use Claude Haiku 5.5 (404), the Anthropic client moves to Haiku 4.5, then Sonnet 5.5, still under the spend cap.
- **Options:** Rely on SDK retries only (every note pays the full retry chain); give up on Anthropic at the first 404 (loses the model path if the key is restricted).
- **Evidence:** Fake key with the API pointed at a dead port: provider dropped after 10 errors, all 60 notes kept their offline codes, whole run 27 s, SCORE 41.7. Unit tests cover fall-through, the drop, and the 404 model fallback (Haiku 4.5 gets no `effort`, which it rejects).
- **Revisit:** The 10-error threshold against real rate-limit behaviour on the graders' keys.

## 11. Verify the graders' command on GitHub Actions, in a private repo
- **When:** 2026-11-05 01:15 IST
- **Commit:** CI: build from a clean checkout and run the graders' command, also with networking off
- **Decision:** No Docker on this laptop, and a build that fails from a clean clone means rejection without review. A private GitHub repo runs, on every push: the unit tests; `docker compose build` from a fresh checkout; the exact `docker compose run coder /in/notes.jsonl /out/predictions.jsonl` with no keys, failing unless every id is present and every code valid; and the image again with `--network none` and fake keys, which is the graders' sandbox with a broken proxy.
- **Options:** Install Docker Desktop locally (8 GB RAM, C: nearly full); trust the Dockerfile unbuilt. Private, not public: the pack is Sugen's and the window is open.
- **Evidence:** First run green (commit dadd584): image builds from a clean checkout; the graders' command with no keys wrote 60/60 valid predictions in 1.9 s (SCORE 41.7); with `--network none` and fake keys for both providers, both were dropped after 10 errors and the run still wrote 60/60 valid predictions in 15 s; 9 unit tests pass.
- **Revisit:** Nothing, if green.

## 12. Pull WHO data on Actions with WHO's container
- **When:** 2026-11-05 01:15 IST
- **Commit:** CI: build from a clean checkout and run the graders' command, also with networking off
- **Decision:** `who-data` workflow starts `whoicd/icd-api` as a service container per language (en, fr, es, pt, ar), waits for it to load, runs `scripts/fetch_who.py` against it and uploads the JSON. The fetch now also keeps exclusions (with the code they point to), definitions and coding notes, which say when a code applies and when another one does.
- **Options:** Wait for Docker on the laptop; the online API (needs an account).
- **Evidence:** Pending first run.
- **Revisit:** Which fields earn a place in the prompt once measured.

## 13. Ask for ICD-10, convert with WHO's official table
- **When:** 2026-11-05 01:18 IST
- **Commit:** Map the model's ICD-10 codes to ICD-11 with WHO's mapping table
- **Decision:** Models have seen far more ICD-10 than ICD-11 coding. The extract step now also returns ICD-10 codes, and WHO's 10-to-11 mapping table (public `mapping.zip` in the 2026-01 release files, same release as the scored MMS) converts them; the targets and all leaves under their stems go to the front of the shortlist, and they are the fallback answer if the choose step fails. Lookup tolerates `B509` and falls back to the 3-character code (WHO's table has `E11` but not `E11.9`). The Dockerfile now copies all of `data/` (it copied only the MMS file, so the table would have been missing from the image).
- **Options:** Trust the model's ICD-11 guesses alone; the WHO online search API at run time (not reachable from the graders' sandbox).
- **Evidence:** 11,174 ICD-10 codes map to valid 2026-01 MMS categories. Spot check of the standard ICD-10 code for 17 dev diagnoses: 14 convert straight to the gold code (B50.9 -> 1F40.Z, A01.0 -> 1A07.Z, J06.9 -> CA07.0, N39.0 -> GC08.Z, B88.1 -> 1G05, B65.0 -> 1F86.0, O14.1 -> JA24.1, O24.4 -> JA63.2, E11 -> 5A11, I50.0 -> BD10, K29.7 -> DA42.Z, K21.9 -> DA22.Z, B01.9 -> 1E90.0, M17.9 -> FA01.Z). The 3 misses are where ICD-11 holds detail ICD-10 lacks: I10 -> BA00.Z (gold BA00.0, combined systolic and diastolic), J45.9 -> CA23.32 (gold CA23.30, with exacerbation), E66.9 -> 5B81.Z (gold 5B81.01, in adults), so the choose step still has to read the note. This uses my own ICD-10 codes, not the model's; the real test is the model's. (First version of this entry said 13 of 17; recounted.)
- **Revisit:** Measure how often the model's ICD-10 code is right, and whether the table's choice should outrank the choose step when they disagree.

## 14. WHO synonyms as one search document each, English only for now
- **When:** 2026-11-05 01:52 IST
- **Commit:** Index WHO synonyms one document each; English WHO data on by default
- **Decision:** The `who-data` workflow returned all 18,375 codes in en, fr, es, pt and ar (98,442 English index terms on 16,171 codes, 6,561 definitions, 4,144 exclusions, 855 coding notes). `scripts/compact_who.py` keeps every field for English and title plus index terms for the other languages, about 5 MB once compressed in the bundle. In the BM25 index each synonym is its own document and a code scores as its best document. English terms are on by default; the other languages stay in the repo, off, until non-English notes can be measured.
- **Options:** All of a code's terms in one document (tried: SCORE fell 41.7 -> 35.4, all languages 33.8; "Burn of face" with its "burn of nose" term beat Acute sinusitis, and 16 long "not confirmed" TB terms beat confirmed TB); all five languages on (51.2 on the English dev notes, 27 s index build).
- **Evidence:** SCORE 41.7 -> 53.3 (top1 31 -> 41 of 60, top3 38 -> 46). Synonym weight 0.8 to 1.0 all give 52.9-53.3 (0.7 gives 50.4), so 0.9 is not a lucky value. Index builds in 5.5 s, 5 ms per note.
- **Revisit:** Definitions, exclusions and coding notes in the choose prompt; French, Spanish, Portuguese and Arabic terms for non-English notes once the synthetic set exists.

## 15. Tried and dropped: end the diagnosis span where the plan starts
- **When:** 2026-11-05 01:54 IST
- **Commit:** Cache model answers on disk for dev runs only
- **Decision:** Keep the diagnosis span as it is. The idea was to stop the weighted "Dx:" span at a dash, a semicolon or words such as start, plan, review, because "Dx: HTN stage 2 – start Amlodipine, low salt diet" scored the WHO term "low salt syndrome" (hyponatraemia) above hypertension.
- **Options:** The cut above; leave it.
- **Evidence:** SCORE 53.3 -> 52.5 (top1 41 -> 40). It fixes nothing the model path won't, so not worth a rule.
- **Revisit:** Only if the no-key path turns out to matter.

## 16. Cache model answers on disk, for dev runs only
- **When:** 2026-11-05 01:54 IST
- **Commit:** Cache model answers on disk for dev runs only
- **Decision:** When `CODER_CACHE_DIR` is set (`scripts/run_dev.sh` sets it to `work/cache`), each provider answer is stored under a hash of provider, model, prompt and schema, and an identical request is replayed at no cost. Changing only the choose prompt then re-runs only the choose calls. Compose never passes the variable, so graded runs are never cached.
- **Options:** No cache (the free Gemini tier has daily request limits and one dev run is 120 calls).
- **Evidence:** Unit test: second identical request served from disk at cost 0, a different note still calls the model. CI on fcff27f: graders' command 53.3 in 8.7 s; --network none 53.3 in 22.6 s.
- **Revisit:** Turn it off when measuring run-to-run variance.
