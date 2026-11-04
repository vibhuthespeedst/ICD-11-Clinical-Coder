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

## 17. Test the success path and the graders' network without a key
- **When:** 2026-11-05 02:12 IST
- **Commit:** End-to-end tests against a fake API; CI sandbox with an allowlist proxy
- **Decision:** Two checks that need no key. (1) `tests/fake_api.py` is a local server that speaks the Anthropic Messages and OpenAI Chat Completions protocols; `tests/test_end_to_end.py` runs the real CLI and the real SDKs against it. (2) A CI job builds the graders' network: an `--internal` Docker network with no internet, plus `tests/connect_proxy.py`, a proxy that only tunnels to api.anthropic.com and api.openai.com and logs every CONNECT. It checks that direct internet fails inside the sandbox, that both SDKs reach their APIs through `HTTPS_PROXY` (fake keys, so the APIs answer 401), that every note still gets valid codes, and that compose passes the proxy and keys into the container.
- **Options:** Wait for a real key (proves quality, but not proxy handling); trust the brief's note that the SDKs honour `HTTPS_PROXY`.
- **Evidence:** Locally, 13 tests pass. Both SDK paths: 60/60 notes with valid codes, exactly 120 requests, key and model on every request, JSON-schema output requested. First 8 requests answered 429: the SDK retried them (128 requests) and all 60 notes still came back from the model path. My first header check assumed `x-api-key`; anthropic 2.4.0 sends `Authorization: Bearer`, so the check now accepts either. Proxy smoke test: api.anthropic.com:443 tunnelled, example.com:443 refused.
- **Evidence (CI, f4a33b8):** inside the sandbox a direct request to example.com fails name resolution; the proxy logged 12 allowed CONNECTs each to api.anthropic.com:443 and api.openai.com:443; both APIs rejected the fake keys (AuthenticationError), both providers were dropped at once, and all 60 notes still got valid codes in 8.6 s (SCORE 53.3).
- **Revisit:** Point the same sandbox at a real key once one exists.

## 18. OpenAI: pick a model the key has; step down when JSON schema is rejected
- **When:** 2026-11-05 02:15 IST
- **Commit:** OpenAI: choose an available mini model; fall back to JSON mode, then plain text
- **Decision:** If none of my preferred OpenAI models is on the key, use the newest `gpt-*-mini` the models endpoint lists instead of a hard-coded name that would 404 and drop OpenAI. If the model rejects `json_schema` output (400), switch for the rest of the run to `json_object` with the schema written into the system prompt, then to plain text with code fences stripped. This also covers Gemini's OpenAI-compatible endpoint, whose schema support I could not check without a key.
- **Options:** Ask the graders which models the key allows (asked, no answer yet); fail the provider on the first 400 (loses OpenAI for the whole run).
- **Evidence:** Two new end-to-end tests against the fake API: with json_schema rejected, all 60 notes still come back from the model path and the last requests use json_object; with gpt-4o, gpt-6-mini and gpt-5.5-mini listed, the run uses gpt-6-mini. 15 tests pass.
- **Revisit:** Remove the guesswork once the graders say which models the keys allow.

## 19. Check the time guard, 600-note throughput and the bundle before there is a key
- **When:** 2026-11-05 02:26 IST
- **Commit:** Test the time budget against a slow fake API
- **Decision:** Keep 12 workers and the 50-minute stop; leave room for extra calls per note only if they measure better. Make the deliverable once early to catch size or content surprises.
- **Options:** Wait for the real key to learn timings (too late to change the design if they are bad).
- **Evidence:** New end-to-end test: fake API at 1 s per call, 4 s budget, 4 workers: the run stops starting notes, all 60 notes keep valid codes, about 10 s in total. One-off run of 600 notes (dev x10) at 1 s per call: 600/600 answered by the model path in 120 s, about 10.5 calls/s with 12 workers, so even 10 s per real call means about 17 minutes. `git bundle create --all`: 5.6 MB, `git bundle verify` okay, clone has all commits, no .env, one author, tests pass and the coder scores 53.3 from the clone.
- **Revisit:** Real latency and rate limits on the graders' keys.

## 20. Grading mounts belong to the graders: dev mounts moved to a local-only file
- **When:** 2026-11-05 03:45 IST
- **Commit:** Move dev mounts to a local-only compose file; CI mounts /in read-only
- **Decision:** Sugen answered by email: at grading they supply `/in/notes.jsonl` read-only and a writable `/out`, and dev mounts must not sit in the default `coder` service. The default service now declares no volumes. `./in` and `./out` live in `compose.dev.yml`, used only with `-f docker-compose.yml -f compose.dev.yml`. I did not use `docker-compose.override.yml`: compose loads that name automatically, so it would mount over the graders' paths; that name and `compose.override.yml` are now git-ignored so one can never be committed.
- **Options:** `docker-compose.override.yml` (auto-loaded, wrong); keep the mounts (told not to).
- **Evidence:** CI now checks that `docker compose config coder` has no /in or /out mount, runs the graders' command with `-v in:/in:ro -v out:/out` supplied from outside (the program writes only its output file, so a read-only /in is fine), and checks the dev override still works.
- **Revisit:** Nothing.

## 21. Rate limits slow the run down instead of switching a provider off
- **When:** 2026-11-05 03:45 IST
- **Commit:** Back off on rate limits with an adaptive cap; load a prebuilt index
- **Decision:** Sugen cannot guarantee any rate limit and asked for bounded concurrency, timeouts and backoff. Before this, a rate-limited call (after the SDK's own 3 retries) counted towards "10 errors in a row", so a burst of 429s could switch the model path off for the rest of the run. Now 429 and 5xx count as transient: the call backs off with jitter (1 s doubling to 30 s, at most 6 tries, never past the time budget) and a shared cap on calls in flight halves on each rate limit and grows back by one after cap-many successes. Connection errors and timeouts still count towards dropping a provider, since a dead proxy should not cost every note its retries.
- **Options:** Fixed lower concurrency (wastes a generous limit); keep the drop rule (loses the model path under a strict limit).
- **Evidence:** Unit test: 14 rate-limit errors with the drop threshold at 3, provider kept and later calls succeed. End to end against a fake API allowing 4 requests a second: 311 requests, 191 answered 429, cap moved 12 -> 6 -> 3 -> 1 -> 4 -> 3 -> 4 -> 2 -> 4, all 60 notes answered by the model path in 51 s, no provider dropped.
- **Revisit:** The cap's starting value once real limits are seen.

## 22. Build the search index at image build time
- **When:** 2026-11-05 03:45 IST
- **Commit:** Back off on rate limits with an adaptive cap; load a prebuilt index
- **Decision:** Sugen confirmed initialisation counts towards the 60 minutes and image build does not. The Dockerfile now runs `python -m coder.prebuild`, which pickles the offline coder (MMS, WHO terms, BM25 index) into the image; the run loads it and falls back to building if it is missing or unreadable (local runs, tests). The pickle is git- and docker-ignored, so it is always built from the code in the image.
- **Options:** Build at start (works, 6.9 s); ship a prebuilt file in the repo (stale the moment code changes).
- **Evidence:** Build at start 6.9 s; pickle 16 MB, loads in 0.2 s, same answers. Offline run of the 60 dev notes: about 0.6 s with the pickle. 19 tests pass.
- **Revisit:** Nothing.

## 23. Claude: step down when the request format is rejected
- **When:** 2026-11-05 03:58 IST
- **Commit:** Claude: fall back from structured output to JSON in the prompt on a 400
- **Decision:** Sugen provides no dev keys, so my Claude requests may never meet the real API before grading. If the API rejects them (400), every call would fail and, after 10, the Claude path would be dropped for the run. Like the OpenAI client, the Anthropic client now steps down for the rest of the run: structured output with effort, then effort with the JSON Schema written into the system prompt, then a plain request. A shared `parse_json` reads an object out of fenced or chatty replies.
- **Options:** Trust that the request shape is accepted (cheap, but one wrong field costs the whole model path).
- **Evidence:** End-to-end test with the fake API rejecting `output_config.format`: one 400, then all 60 notes answered by the model path from fenced replies, no provider dropped. 21 tests pass; dev SCORE unchanged at 53.3.
- **Revisit:** Drop the fallback once a real call confirms the request shape.

## 24. The commit hook must catch the key I actually have, not the format I expected
- **When:** 2026-11-05 04:26 IST
- **Commit:** Commit hook refuses any secret value from .env, whatever its format
- **Decision:** My Gemini key does not start with `AIza`, so the pattern list would not have caught it. The hook now also reads `.env` and refuses any staged line containing the value of a variable whose name has KEY, TOKEN or SECRET in it (16+ characters), without printing it.
- **Options:** Add another prefix pattern (breaks again on the next format change).
- **Evidence:** My first attempt failed: the editor refused to overwrite the hook file, the old hook stayed installed, and my test (a real `git commit` of a file holding a fake key) went through as a local commit. I removed it with a reset to the last pushed commit before anything was pushed, and now test the hook by running it directly. Direct runs: fake key value staged -> refused; a staged file holding only the base URL -> allowed; real `.env` with a clean change -> allowed, nothing printed.
- **Revisit:** Nothing.

## 25. Dev model: gemini-3.6-flash on the free tier; models cannot code ICD-11 from memory
- **When:** 2026-11-05 04:35 IST
- **Commit:** Dev runs: settings already in the environment win over .env
- **Decision:** Develop against `gemini-3.6-flash`, the newest model the free key actually serves. `scripts/run_dev.sh` now lets variables already set in the shell override `.env`, so models can be tried without editing the key file.
- **Options:** `gemini-3.8-flash` (every call rate-limited or timed out; a 3-note run hit the 300 s budget with 0 model answers, all offline answers kept); `gemini-flash-latest` and `gemini-3.7-flash` (503); the 2.5 models (listed but 404); Pro models (429, no free quota).
- **Evidence:** One request per model asking directly for "uncomplicated Plasmodium falciparum malaria" (gold 1F40.Z): the four that answered (3.5-flash, 3.6-flash, 3-flash-preview, 3.1-flash-lite) gave 1F40.1, 1F40.01 (not a valid code), 1F40.0 and 1F40.0; none gave 1F40.Z. (First version of this entry said five; recounted.) That is the case for the shortlist and the ICD-10 conversion rather than trusting a model's memory of ICD-11. Smoke test of 3 dev notes on gemini-3.6-flash: all 3 answered by the model path, all 3 top-1 correct, 46 s under free-tier rate limiting (the cap fell to 1 call in flight).
- **Revisit:** These are Gemini numbers; the graders run Claude or OpenAI.

## 26. Treat notes as patient data
- **When:** 2026-11-05 04:50 IST
- **Commit:** Strip direct identifiers before notes leave the machine; keep note text out of logs
- **Decision:** These notes are synthetic, but the system is built for clinics. (1) Before a note goes to a model provider, `coder/redact.py` removes direct identifiers that coding never needs: labelled fields (Name, MRN, IP/OP No, NHIF, DOB, Tel, Address, Next of kin), emails, phone numbers, 8+ digit IDs, full dates, a title plus name, and "my name is ...". On by default; `CODER_REDACT=0` turns it off. The offline coder still reads the full note, since it never leaves the machine. (2) Logs carry the error type and HTTP status only, never provider error bodies, which can echo the request. (3) OpenAI calls set `store=False`. (4) The dev cache prints a warning that it writes model answers to disk.
- **Options:** Send notes as they are (the task allows it); a named-entity model to find names (another model in the image for little gain); broad patterns (a "this is X" rule I tried in the scan matched "This is chickenpox", the diagnosis itself).
- **Evidence:** Scan of the 60 dev notes: zero emails, phone numbers, long IDs, titled names, labelled fields or full dates, so all 60 are sent unchanged and dev scores cannot move. Unit tests: a sample note's identifiers are removed while BP 118/76, x3/7, 12/40, 80/480, Hb 13.4, VL 1000000 and "This is chickenpox" stay. End to end through the real Anthropic SDK: none of 7 identifiers reached the fake API, the diagnosis line did; 400 errors that echo the note show up in the log only as "BadRequestError 400". 26 tests pass.
- **Revisit:** A real deployment also needs provider agreements (BAA, zero data retention), data residency, audit logs and a retention policy; regex de-identification misses free-text names ("Amina said...").

## 27. Security checklist pass; clean errors instead of tracebacks
- **When:** 2026-11-05 04:55 IST
- **Commit:** Print a one-line error, not a traceback, when the input or output file fails
- **Decision:** Went through a 25-item web-app security checklist. Most items (passwords, sessions, JWT, OAuth, routes, tenants, SQL, uploads, HTML, logins, payments, webhooks, RLS) have nothing to apply to: this is a batch job with no users, server, database or browser. For the items that do apply: (1) no secrets in code or in any commit, (3) every setting has a safe default and no key at all falls back to the offline coder, (4) every .env variant is ignored by git and docker, (15) no eval, exec or shell calls on input, (17) model output is accepted only if it is a real MMS code, (20) spend is capped across providers, (25) a missing input or unwritable output now prints one line and exits 1, instead of a traceback with internal paths.
- **Options:** Leave tracebacks (normal for a CLI, but they show paths and are noisy for the graders).
- **Evidence:** History scan with counts only: every commit on every branch and the local reflog, 178 KB of added lines plus all 7 versions of the JSON data files (31.8 MB): zero sk-, sk-ant-, sk-proj-, AIza, pk_ or PASSWORD/SECRET/DATABASE_URL values, and zero occurrences of my real key. The only pickle load reads the index the image builds itself (git- and docker-ignored). "cannot read the input file: FileNotFoundError", exit 1.
- **Revisit:** Nothing.

## 28. A spent quota is not a rate limit
- **When:** 2026-11-05 05:10 IST
- **Commit:** Treat a spent quota as fatal: drop the provider instead of retrying
- **Decision:** A 429 that means the budget or daily quota is gone (OpenAI `insufficient_quota`, Google's per-day quota) now drops the provider at once, so the run falls through to the other provider or the offline coder instead of retrying until the time budget. Ordinary 429s still back off.
- **Options:** Keep treating every 429 as temporary (what happened below).
- **Evidence:** First full dev run on gemini-3.6-flash: only 8 of 60 notes got model answers. The free tier allows 20 requests per day per model (Google's 429 body: "limit: 20 ... per day"), so after the 3-note smoke test and 8 notes every request was refused; each remaining note spent about a minute retrying and the run ended after 1,645 s with every note still answered (offline). Its SCORE 55.4 is therefore mostly the offline coder, not a model score. I also deleted `work/`, which holds the dev cache, during that run; that lost the cached answers but did not cause the failures. New end-to-end test: with the quota spent, OpenAI is dropped within the first wave (at most 12 workers x the SDK's own 4 attempts = 48 requests), the run takes under 30 s, and all 60 notes get valid codes. 27 tests pass.
- **Revisit:** A real model score needs more quota: a free model with a larger daily limit, or paid credit.

## 29. Overfitting check: switch my hand rules off
- **When:** 2026-11-05 05:10 IST
- **Commit:** Treat a spent quota as fatal: drop the provider instead of retrying
- **Decision:** Keep the hand rules, but treat any gain under about 3 points as noise and judge model-path changes on the synthetic notes, not the dev set.
- **Options:** Drop the hand-made lay-term list, the part most inspired by the dev notes.
- **Evidence:** Offline dev SCORE with everything on 53.3 (top1 41/60); without my lay-term list 51.7 (40/60), so WHO's synonyms now cover most of what it did; without my abbreviation list 50.0 (37/60); without the chapter 26 and .Y penalties 48.3 (35/60); without any hand rule 44.2 (32/60). The gains come mostly from standard abbreviations and the brief's own .Z rule, which carry to any clinic. Noise: with 60 notes, a top-1 of 68% has a standard error of about 6%, about +/- 3 points on the 75-point core.
- **Revisit:** Re-run once the synthetic notes exist.
