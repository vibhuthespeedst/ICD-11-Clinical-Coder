# ICD-11 coder

Reads an outpatient note and proposes up to three ICD-11 MMS codes, best first.

```
docker compose run coder /in/notes.jsonl /out/predictions.jsonl
```

Local runs mount `./in` and `./out` with `-f docker-compose.yml -f compose.dev.yml`; the default service has no mounts of its own.

## Scores

| | Dev, 60 notes (score.py) | Synthetic, 145 notes |
|---|---|---|
| No key (offline coder) | 53.3 / 75 (top1 41/60, top3 46/60) | top1 32% |
| Model path, gemini-3.5-flash-lite (free tier) | 72.9 / 75 (top1 58/60, top3 59/60) | 20.7 / 25 (top1 80%, top3 89%) |

I had no paid key, so the model path is measured on free Gemini models, not on the Claude or OpenAI models you grade with. Both remaining top-1 misses on dev are the right disease at the wrong level of detail.

**Estimate for the hidden set:** about 64-70 / 75 on the core slice (the dev notes were seen while designing, and 60 notes carry about +/- 3 points of noise) and about 18-21 / 25 on the generalisation slice (the synthetic codes are rarer than clinic reality, but a model wrote each note knowing its code), so roughly 82-90 / 100. If no key works, the offline coder alone would land around 45-55.

## How it works

1. **Offline first.** BM25 over every MMS title, its ancestors and WHO's index terms (one document per synonym), with clinical abbreviations, UK spelling and negation handling. Predictions for every note are written before any API call.
2. **Model path, two calls per note.** The model reads the note in any language and returns English diagnosis terms, the details that decide specificity, ICD-10 codes and ICD-11 guesses. A shortlist is built from WHO's ICD-10 to ICD-11 table, the search and every leaf under each hit's stem. The model then picks up to three codes from that list only. Every code is checked against the MMS.
3. **Run time.** One spend cap shared across providers ($5.50), a 50-minute stop, an adaptive cap on calls in flight (halves on 429), a spent quota drops the provider, fallbacks across providers, Claude models and output formats. Predictions are rewritten atomically as answers arrive. The search index is built at image build time.

## Data added

- **WHO ICD-API**, release 2026-01, pulled from WHO's offline container (`whoicd/icd-api`) on GitHub Actions: index terms, inclusions, exclusions, definitions and coding notes for all 18,375 codes, plus titles and index terms in French, Spanish, Portuguese and Arabic.
- **WHO ICD-10 to ICD-11 mapping tables** (`mapping.zip`, release 2026-01). Asked directly, four Gemini models gave four wrong ICD-11 codes for uncomplicated falciparum malaria; B50.9 maps straight to the right one.

ICD-11 content is © World Health Organization, used under CC BY-ND 3.0 IGO.

## Evaluation beyond the 60 dev notes

- **145 synthetic notes** across 23 chapters and 8 languages, written by a different model from the one coding them, with a language check that drops notes not written in the requested language. Model-coded notes: top1 79%, top3 89%, the same for English and non-English.
- **A hand check** of 15 synthetic notes against their codes. TODO(Vibhu): result.
- **Overfitting check:** switching my hand rules off one at a time; the rule set most inspired by the dev notes is worth only 1 note now that WHO's synonyms are in.
- **Failure paths, without a key:** a local fake of both APIs drives the real SDKs (rate limits, spent quota, rejected request formats), and CI runs the exact grading command from a clean checkout, with `/in` read-only, with no network, and inside an internal Docker network whose only exit is a proxy that allows just the two model APIs.

## Patient data

Direct identifiers (labelled fields, phone numbers, IDs, dates, names after a title) are stripped before a note leaves the machine; logs carry error types only; OpenAI calls set `store=False`. A real deployment would also need provider agreements (BAA, zero data retention), data residency and audit logs.

## Where the AI tooling was wrong

TODO(Vibhu): the one place you caught it, in your words.

## Hours

TODO(Vibhu): hours spent.

`DECISIONS.md` has the full log, with the evidence for every choice.
