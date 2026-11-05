# ICD-11 coder

Reads an outpatient note and proposes up to three ICD-11 MMS codes, best first.

```
docker compose run coder /in/notes.jsonl /out/predictions.jsonl
```

Local runs add `-f docker-compose.yml -f compose.dev.yml` to mount `./in` and `./out`; the default service has no mounts.

## Scores

| | Dev, 60 notes (score.py) | Synthetic, 145 notes |
|---|---|---|
| No key (offline coder) | 53.3 / 75 | 8.1 / 25 (top1 28%) |
| Model path, gemini-3.5-flash-lite (free tier) | 72.9 / 75 (top1 58/60, top3 59/60) | 20.7 / 25 (top1 80%, top3 89%) |

I had no paid key, so these are free Gemini models, not the Claude or OpenAI models you grade with.

**Hidden-set estimate:** 64-70 / 75 on the core slice (I saw the dev notes while designing, and 60 notes carry about +/- 3 points of noise) and 18-21 / 25 on generalisation: roughly 82-90 / 100. With no working key, about 53-61.

## How it works

1. **Offline first.** BM25 over every MMS title, its parents and WHO's synonyms writes codes for every note before any API call.
2. **Model path.** Call 1 reads the note in any language and returns English diagnoses, the deciding details and ICD-10 codes. A shortlist comes from WHO's ICD-10 to ICD-11 table, the search and every child of each hit. Call 2 picks up to three codes from that list only, each checked against the MMS.
3. **Run time.** A spend cap shared across providers, a 50-minute stop, adaptive concurrency on rate limits, fallbacks across providers, models and output formats, and predictions rewritten as answers arrive.

## Data added

- **WHO ICD-API** (release 2026-01), from WHO's offline container on GitHub Actions: synonyms, inclusions, exclusions, definitions and coding notes for all 18,375 codes, plus French, Spanish, Portuguese and Arabic terms.
- **WHO's ICD-10 to ICD-11 tables** (release 2026-01). Models know ICD-10 far better: asked for uncomplicated falciparum malaria, four Gemini models all gave a wrong ICD-11 code, while its ICD-10 code maps straight to the right one.

ICD-11 content is © World Health Organization, CC BY-ND 3.0 IGO.

## Evaluation beyond the 60 dev notes

- **145 synthetic notes** over 23 chapters and 8 languages, written by a different model from the coder. Non-English notes score close to English (top1 78% against 82%).
- **A hand check** of 15 of them: 12 fit their codes and 3 did not, so the synthetic score is a rough guide.
- **Overfitting checks:** hand rules switched off one at a time; prompt changes judged on the synthetic notes, not the dev set; one rule that helped only dev was dropped.
- **Failure paths, no key needed:** a local fake of both APIs drives the real SDKs, and CI runs the exact grading command from a clean checkout, with read-only `/in`, with no network, and behind a proxy that allows only the two model APIs.

## Security and patient data

Identifiers are stripped before a note leaves the machine, logs carry error types only, and OpenAI calls set `store=False`. The applicable items of a 25-item security checklist pass, and every package and the base image are pinned. A real clinic deployment would also need provider agreements (BAA, zero data retention), data residency and audit logs.

## Where the AI tooling was wrong

1. **It sent patient details it did not need.** The insurance code only needs the diagnosis and the clinical details, but the first version sent each whole note to the AI provider, including any name, phone number, ID or date of birth in it. It also printed the provider's error messages into the log, where they can repeat the note. I caught this with a privacy review. Those details are now removed before a note leaves the machine, and the log keeps only the type of error.
2. **Its error messages showed too much.** A missing input file printed a long error listing the program's internal folders and files, when it only needed to say the file was not found. I caught this with a security checklist; it now prints one line.
3. **One of its instructions was wrong.** It told the model to choose "other specified" when a note said "primary", but for "primary hypothyroidism" the right answer is "unspecified". A stronger model made the same mistake on the hardest notes, which showed the instruction was at fault, not the model. The rule was rewritten and checked on notes the design had never seen.
4. **Some of its test notes did not match their labels.** Reading 15 of them, I found 3 whose details did not support their code: fingers joined by skin only, labelled "fused fingers"; divergence insufficiency labelled "synergistic divergence"; and low desire that began in one relationship, labelled "lifelong". So I treat the synthetic score as a rough guide.

## Hours

About 14 hours.

`DECISIONS.md` has the full log, with the evidence for every choice.
