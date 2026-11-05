# Review of 15 synthetic notes

For each note, read the text and decide whether it really supports the target code: the right condition AND the right level of detail.
Write `OK` or `WRONG: <short reason>` on the Verdict line. Specific codes need their deciding detail in the note; `.Z` (unspecified) codes need that detail to be missing.

## synth-111  (ambient_transcript)

**Target:** `LB79.0` Fused fingers  (under `LB79` Syndactyly)

**Must be told apart from:** `LB79.1` Webbed fingers; `LB79.2` Fused toes; `LB79.3` Webbed toes; `LB79.Y` Other specified syndactyly; `LB79.Z` Syndactyly, unspecified

> Doctor: Good morning. Let me take a look at little Leo’s hand. I see here that the middle and ring fingers on his right hand are physically joined together by skin and soft tissue starting from the base all the way up to the second knuckle. Patient: Yes, it is just those two fingers on his right hand. His toes are all perfectly normal and separated. Doctor: Based on this examination, it is clear he has complex syndactyly, specifically involving a congenital fusion of the digits. Vitals are stable, pulse is regular, and there is no evidence of bony involvement at this stage. Since his feet are completely unaffected and this is strictly limited to the fingers of one hand, we will schedule a referral with a pediatric hand surgeon to discuss separating the fingers to improve future function. We will keep an eye on his development to ensure no other joints are involved. Patient: That sounds like a plan. We just want to make sure he can use his hand properly as he grows. Doctor: We will get that appointment set up for you today.

**Verdict:** WRONG: the findings are skin and soft tissue only with no bone involved, which is webbed fingers (LB79.1), yet the note calls it fused.

## synth-010  (ambient_transcript)

**Target:** `BD11.Z` Left ventricular failure, unspecified  (under `BD11` Left ventricular failure)

**Must be told apart from:** `BD11.0` Left ventricular failure with preserved ejection fraction; `BD11.1` Left ventricular failure with mid range ejection fraction; `BD11.2` Left ventricular failure with reduced ejection fraction

> Doctor: Good morning, Mrs. Gable. I have reviewed the results of your echocardiogram and your recent blood work. How have you been feeling since we last spoke? Patient: Honestly, Doctor, I am still so winded when I walk to the mailbox. I feel like I just cannot get enough air, and my ankles are still swollen by the evening. Doctor: I hear you. Based on the imaging and your symptoms of shortness of breath and fluid retention, it is clear that your heart muscle is struggling to pump blood effectively to the rest of your body. Your left ventricle is not functioning properly, which is causing this backup. We call this left ventricular failure. I need to get you started on a new medication regimen to manage this fluid and support your heart's workload. Vitals today show blood pressure is 145/90 and your pulse is 88. Plan: We will start lisinopril and furosemide today. Please monitor your daily weights, eat a low-sodium diet, and follow up in two weeks for repeat labs to ensure your kidneys are handling the medications well.

**Verdict:** OK

## synth-094  (short_consult)

**Target:** `3A00.2` Acquired iron deficiency anaemia due to decreased absorption  (under `3A00` Iron deficiency anaemia)

**Must be told apart from:** `3A00.0` Acquired iron deficiency anaemia due to blood loss; `3A00.1` Acquired iron deficiency anaemia due to low intake; `3A00.3` Acquired iron deficiency anaemia due to increased requirement; `3A00.Y` Other specified iron deficiency anaemia; `3A00.Z` Iron deficiency anaemia, unspecified

> Pt, 54yo M, h/o celiac dx, presenting w/ fatigue, glossitis. Labs: Hgb 9.2, low ferritin, high TIBC. Pt adherent to strict GF diet, no occult GI bleed, no dietary restriction. Malabsorption suspected secondary to refractory celiac sprue. Plan: Start FeSO4, repeat labs in 4wks, ref GI for EGD/duodenal bx to eval absorption status.

**Verdict:** OK

## synth-138  (short_consult)

**Target:** `1E51.3` Chronic hepatitis E  (under `1E51` Chronic viral hepatitis)

**Must be told apart from:** `1E51.0` Chronic hepatitis B; `1E51.1` Chronic hepatitis C; `1E51.2` Chronic hepatitis D; `1E51.Y` Other specified chronic viral hepatitis; `1E51.Z` Chronic viral hepatitis, unspecified

> Pt w/ persistent HEV RNA+ >6mo despite tx. Labs: AST 85, ALT 110, Bili 1.2. Neg for HBV, HCV, HDV, HAV. Persistent transaminitis & viremia confirm chronic HEV in this immunosuppressed transplant recipient. Plan: cont ribavirin, monitor q4wks viral load, optimize IS levels.

**Verdict:** OK

## synth-039  (typed_consult)

**Target:** `HA00.1` Hypoactive sexual desire dysfunction, lifelong, situational  (under `HA00` Hypoactive sexual desire dysfunction)

**Must be told apart from:** `HA00.0` Hypoactive sexual desire dysfunction, lifelong, generalised; `HA00.2` Hypoactive sexual desire dysfunction, acquired, generalised; `HA00.3` Hypoactive sexual desire dysfunction, acquired, situational; `HA00.Z` Hypoactive sexual desire dysfunction, unspecified

> Pt: 28F, healthy, presents with concerns regarding persistent lack of sexual interest. Hx: Pt reports she has never experienced sexual desire in her life. However, she notes that this absence of desire is strictly limited to her current long-term partner of 3 years. When asked about other potential partners or past crushes, she describes feeling normal libido levels, confirming this is a situational response to her current relationship dynamic. No history of sexual trauma or hormonal imbalances. Ex: Vitals stable. Pmh: Unremarkable. Exam: Vagina healthy, no signs of atrophy or inflammation. Pelvic floor tone WNL. Imp: Hypoactive sexual desire dysfunction, lifelong, situational. Unlike generalized forms, her libido is intact in other contexts, indicating a specific relational trigger rather than a systemic or neurobiological baseline deficit. Plan: Referral to couples therapy to address interpersonal conflict and relational dynamics. Discussed communication exercises and scheduling intimate time. Follow up in 6 weeks to evaluate if shift in relational satisfaction impacts her subjective desire levels. Education provided on arousal non-concordance.

**Verdict:** WRONG: she has normal desire with past crushes and other partners, and the low desire is limited to a 3-year relationship, which is acquired and situational (HA00.3); the note's "never experienced desire" line contradicts that.

## synth-004  (ambient_transcript)

**Target:** `5C51.1` Disorders of glycerol metabolism  (under `5C51` Inborn errors of carbohydrate metabolism)

**Must be told apart from:** `5C51.0` Disorders of the pentose phosphate pathway; `5C51.2` Disorders of glyoxylate metabolism; `5C51.3` Glycogen storage disease; `5C51.4` Disorders of galactose metabolism; `5C51.5` Disorders of fructose metabolism; `5C51.Y` Other specified inborn errors of carbohydrate metabolism; `5C51.Z` Inborn errors of carbohydrate metabolism, unspecified

> Doctor: Good morning, Leo. I have reviewed your blood work and the specialized metabolic panel we ordered. Your symptoms of recurring episodic nausea and the finding of persistent high levels of glycerol in your urine, alongside your normal blood sugar and lactate levels, help clarify what is going on. Patient: I have been worried about these episodes, especially since they do not seem tied to specific meals. Does this mean it is a problem with how my body breaks down sugar? Doctor: Not exactly. This is specifically a disorder of glycerol metabolism. Your body is struggling to convert glycerol into the energy pathways it usually follows, which leads to an accumulation of these compounds in your system. It is distinct from issues with glycogen or galactose processing because your liver enzymes related to those are perfectly normal. We are going to start you on a specialized low-fat diet to reduce the glycerol load and schedule a follow-up with the metabolic geneticist to confirm the exact enzymatic deficiency. Vitals today show a BP of 122/80, pulse 74, and temp 98.6. Findings confirm the elevated urinary glycerol excretion. We will monitor your symptoms closely as we adjust your intake.

**Verdict:** OK

## synth-121  (short_consult)

**Target:** `7A00` Chronic insomnia

**Must be told apart from:** nothing (no siblings)

> Pt reports 6mo hx of difficulty falling/staying asleep 4-5 nights/wk despite adequate opportunity. Denies OSA sx, RLS, or stress triggers. Affects daytime fctn. Dx: Chronic insomnia. Plan: Sleep hygiene counseling, taper caffeine, trial of low-dose melatonin, f/u in 4wks if no improvement.

**Verdict:** OK

## synth-059  (short_consult)

**Target:** `EE8Z` Histiocytic-granulomatous disorders of the skin, unspecified

**Must be told apart from:** nothing (no siblings)

> Pt presents w/ persistent erythematous indurated plaques on trunk. Biopsy shows non-specific histiocytic and granulomatous infiltrate, dermis. No systemic involvement noted on labs or exam. Suspect cutaneous histiocytic-granulomatous process. Plan: refer to derm for further IHC staining and potential excisional bx to clarify etiology. Monitor for new lesions.

**Verdict:** OK

## synth-053  (typed_consult)

**Target:** `8B41` Myelitis

**Must be told apart from:** nothing (no siblings)

> Patient is a 42-year-old female presenting with 3 days of progressive lower extremity weakness and sensory level at T10. She reports urinary urgency and mid-back pain. Vitals: BP 128/82, HR 78, T 99.1F, SpO2 98%. Exam reveals 3/5 strength in bilateral quadriceps and hamstrings, hyperreflexia in the lower extremities, and positive Babinski sign bilaterally. Pinprick sensation is diminished below the umbilicus. Labs show mild leukocytosis. MRI of the thoracic spine demonstrates hyperintense signal within the central cord extending over three vertebral segments, consistent with transverse inflammatory pathology. No compression or disc herniation seen. Assessment: Acute transverse myelitis. Plan: Admit for high-dose IV methylprednisolone pulse therapy. Obtain CSF studies including oligoclonal bands and NMO/MOG antibodies to rule out secondary causes. Neurology consult requested for further workup and to discuss potential plasmapheresis if refractory to steroids. Physical therapy to initiate mobility training pending stabilization.

**Verdict:** OK

## synth-026  (typed_consult)

**Target:** `4B22` Cryoglobulinaemia

**Must be told apart from:** nothing (no siblings)

> Pt: 54yo F presents w/ 3mo hx of palpable purpura on LEs, persistent arthralgias in hands, and generalized malaise. Denies recent travel or drug use. PMH: Hep C (untreated). Vitals: T 98.4, BP 138/82, HR 76, RR 16, O2 sat 99%. Exam: Bilateral lower extremity non-blanching purpuric rash. Trace edema noted. Neuro: decreased pinprick sensation in distal feet. Labs: RF elevated, C4 low, positive cryoglobulins on testing. Assessment: Mixed cryoglobulinaemia, likely secondary to chronic HCV infection. Plan: 1. Confirm viral load and genotype for HCV. 2. Refer to rheumatology for assessment of vasculitic involvement. 3. Monitor renal function via BMP and UA for proteinuria. 4. Initiate counseling for upcoming antiviral therapy. Pt understands the need for systemic management to prevent nerve and kidney damage.

**Verdict:** OK

## synth-101  (typed_consult)

**Target:** `AA40.0` Exostosis of external auditory canal  (under `AA40` Acquired deformity of external auditory canal)

**Must be told apart from:** `AA40.1` Acquired stenosis of external auditory canal; `AA40.2` Cholesteatoma of external auditory canal; `AA40.Y` Other specified acquired deformity of external auditory canal; `AA40.Z` Acquired deformity of external auditory canal, unspecified

> Patient: 42M, avid surfer. Hx: Complains of intermittent sense of fullness in the right ear and occasional trapped water after swimming. Denies pain, discharge, or hearing loss. Ex: Vitals stable, afebrile. Otoscopy reveals multiple, broad-based, smooth, bony protuberances arising from the medial tympanic ring of the external auditory canal bilaterally. The skin overlying these mounds is thin, pale, and intact. No signs of inflammation, debris, or wax impaction noted. The tympanic membranes are clear and mobile bilaterally. No evidence of canal narrowing or soft tissue growth. Imp: Multiple bilateral bony growths consistent with external auditory canal exostosis, likely secondary to chronic cold water exposure. These are distinct from cholesteatoma as the epithelium remains intact and non-migratory. Canal patency is well-preserved, ruling out acquired stenosis. Plan: Conservative management. Advised use of custom-fitted silicone earplugs during water activities to prevent further enlargement. Will monitor periodically for progression or potential impaction of cerumen between the bony ridges. Return to clinic if patient develops secondary otitis externa or obstructive symptoms.

**Verdict:** OK

## synth-037  (short_consult)

**Target:** `FA80.2` Intervertebral disc degeneration of cervical spine with bony spur at the vertebra  (under `FA80` Intervertebral disc degeneration)

**Must be told apart from:** `FA80.0` Intervertebral disc degeneration of cervical spine without prolapsed disc; `FA80.1` Intervertebral disc degeneration of cervical spine with prolapsed disc; `FA80.3` Intervertebral disc degeneration of cervical spine with nervous system involvement; `FA80.4` Intervertebral disc degeneration of thoracic spine without prolapsed disc; `FA80.5` Intervertebral disc degeneration of thoracic spine with prolapsed disc; `FA80.6` Intervertebral disc degeneration of thoracic spine with bony spur at the vertebra; `FA80.7` Intervertebral disc degeneration of thoracic spine with nervous system involvement; `FA80.8` Intervertebral disc degeneration of lumbar spine without prolapsed disc

> Pt presents w/ chronic neck pain, worse w/ rotation. Exam shows limited ROM, no radiculopathy or focal neuro deficits. Imaging confirms C5-C6 disc space narrowing w/ prominent osteophyte formation at the vertebral endplate. No evidence of herniation or cord compression noted. Will start PT and NSAIDs for symptomatic relief.

**Verdict:** OK

## synth-008  (short_consult)

**Target:** `9C83.63` Synergistic divergence  (under `9C83.6` Anomalies of divergence or deviation of eye movement)

**Must be told apart from:** `9C83.60` Divergence insufficiency; `9C83.61` Divergence paralysis; `9C83.62` Divergence excess; `9C83.64` Skew deviation; `9C83.65` Ocular tilt reaction; `9C83.66` Alternating skew deviation; `9C83.67` Dissociative vertical divergence; `9C83.6Y` Other specified anomalies of divergence or deviation of eye movement

> Pt reports chronic intermittent horizontal diplopia, worse at distance. Exam shows orthophoria at near, but significant esotropia on primary gaze distance testing that worsens with attempted abduction. Full range of motion, no neurological deficits. Dx: Synergistic divergence. Plan: Fresnel prism for distance activities and monitor q6mo.

**Verdict:** WRONG: esotropia worse at distance and normal at near is divergence insufficiency (9C83.60); the note just copies the target name into its Dx line.

## synth-107  (typed_consult)

**Target:** `GC40.37` Complete uterine prolapse with anterior and posterior vaginal wall prolapse  (under `GC40.3` Uterovaginal prolapse)

**Must be told apart from:** `GC40.30` Incomplete uterovaginal prolapse; `GC40.31` Incomplete uterine prolapse with anterior vaginal wall prolapse; `GC40.32` Incomplete uterine prolapse with posterior vaginal wall prolapse; `GC40.33` Incomplete uterine prolapse with anterior and posterior vaginal wall prolapse; `GC40.34` Complete uterovaginal prolapse; `GC40.35` Complete uterine prolapse with anterior vaginal wall prolapse; `GC40.36` Complete uterine prolapse with posterior vaginal wall prolapse; `GC40.3Z` Uterovaginal prolapse, unspecified

> Subjective: 68-year-old G4P4 female presents with a persistent, golf-ball-sized bulge extruding from the introitus. She reports severe pelvic pressure, difficulty voiding, and fecal urgency requiring digital pressure to evacuate. Symptoms worsened over two years. Objective: Vitals: BP 135/85, HR 76. Pelvic exam confirms total procidentia with the entire uterine corpus, cervix, and both anterior and posterior vaginal walls exteriorized beyond the hymenal ring. No ulceration noted. Assessment: Complete uterine prolapse with anterior and posterior vaginal wall prolapse. The degree of descent confirms full procidentia including both cystocele and rectocele components. Plan: Discussed management options including pessary trial vs. surgical intervention. Patient desires definitive repair. Ordered preoperative urodynamics and scheduled MRI of the pelvic floor. Advised pelvic floor PT for symptomatic management in the interim. Follow up in two weeks to review surgical risks including recurrence and mesh erosion.

**Verdict:** OK

## synth-149  (short_consult)

**Target:** `CA71.2` Pneumonitis due to aspiration of blood  (under `CA71` Pneumonitis due to solids or liquids)

**Must be told apart from:** `CA71.0` Pneumonitis due to inhalation of food or vomit; `CA71.1` Pneumonitis due to oils or essences; `CA71.3` Lipoid pneumonitis; `CA71.Y` Other specified pneumonitis due to solids or liquids; `CA71.Z` Pneumonitis due to solids or liquids, unspecified

> Pt presented w/ SOB & tachypnea post-epistaxis. CXR shows RLL infiltrates. Vitals: T 100.2, HR 105, O2 sat 91% on RA. Hx sig for massive nosebleed w/ coughing & choking episodes prior to dyspnea. Dx: pneumonitis secondary to blood aspiration. Plan: O2 support, serial CXRs, monitor resp status.

**Verdict:** OK
