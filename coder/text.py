import re

TOKEN = re.compile(r"[^\W_]+")

STOP = set("""
a an the and or of in on at to for with without by from as is are was were be been it its this that
these those he she they his her their him them we you your i my me our patient pt pts doctor dr
yes ok okay right left l r x day days week weeks month months year years yr yrs old today since
also has have had not no due other unspecified specified type site
""".split())

US_UK = [
    (r"\bedema", "oedema"), (r"anemi", "anaemi"), (r"\besophag", "oesophag"), (r"diarrhea", "diarrhoea"),
    (r"hemorrh", "haemorrh"), (r"hematu", "haematu"), (r"hemat", "haemat"), (r"hemoglob", "haemoglob"),
    (r"hemoly", "haemoly"), (r"hemophil", "haemophil"), (r"pediatr", "paediatr"), (r"gynecol", "gynaecol"),
    (r"leukem", "leukaem"), (r"ischem", "ischaem"), (r"tumor", "tumour"), (r"\bfetal", "foetal"),
    (r"estrogen", "oestrogen"), (r"dyspnea", "dyspnoea"), (r"apnea", "apnoea"), (r"orthopedic", "orthopaedic"),
    (r"glycemi", "glycaemi"), (r"lipidemi", "lipidaemi"), (r"septicemi", "septicaemi"), (r"cesarean", "caesarean"),
    (r"candidiasis", "candidosis"), (r"\bgerd\b", "gord"),
]

ABBREV = {
    "urti": "upper respiratory infection", "lrti": "lower respiratory infection", "uti": "urinary tract infection",
    "tb": "tuberculosis", "ptb": "pulmonary tuberculosis", "eptb": "extrapulmonary tuberculosis",
    "htn": "hypertension", "dm": "diabetes mellitus", "t1dm": "type 1 diabetes mellitus",
    "t2dm": "type 2 diabetes mellitus", "dka": "diabetic ketoacidosis", "copd": "chronic obstructive pulmonary disease",
    "gord": "gastro oesophageal reflux disease", "pud": "peptic ulcer", "ibs": "irritable bowel syndrome",
    "pid": "pelvic inflammatory disease", "af": "atrial fibrillation", "dvt": "deep vein thrombosis",
    "pe": "pulmonary embolism", "pet": "pre eclampsia", "sam": "severe acute malnutrition",
    "mam": "moderate acute malnutrition", "oa": "osteoarthritis", "ra": "rheumatoid arthritis",
    "bph": "hyperplasia of prostate", "ccf": "congestive heart failure", "chf": "congestive heart failure",
    "hf": "heart failure", "ihd": "ischaemic heart disease", "acs": "acute coronary syndrome",
    "mi": "myocardial infarction", "stemi": "st elevation myocardial infarction", "ckd": "chronic kidney disease",
    "aki": "acute kidney injury", "cap": "community acquired pneumonia", "aom": "acute otitis media",
    "ome": "otitis media with effusion", "csom": "chronic suppurative otitis media", "bv": "bacterial vaginosis",
    "sti": "sexually transmitted infection", "hiv": "human immunodeficiency virus hiv disease",
    "ida": "iron deficiency anaemia", "scd": "sickle cell disease", "age": "acute gastroenteritis",
    "gad": "generalised anxiety disorder", "mdd": "depressive disorder", "ptsd": "post traumatic stress disorder",
    "ocd": "obsessive compulsive disorder", "adhd": "attention deficit hyperactivity disorder",
    "lbp": "low back pain", "tia": "transient ischaemic attack", "cva": "stroke", "hsv": "herpes simplex",
    "uri": "upper respiratory infection", "ugib": "upper gastrointestinal haemorrhage", "bppv": "benign positional vertigo",
    "ttn": "transient tachypnoea of newborn", "nnj": "neonatal jaundice", "pph": "postpartum haemorrhage",
    "prom": "premature rupture of membranes", "gdm": "gestational diabetes mellitus arising in pregnancy",
    "anc": "antenatal care supervision of pregnancy", "hzv": "zoster", "ms": "multiple sclerosis",
    "osa": "obstructive sleep apnoea", "sle": "systemic lupus erythematosus", "uc": "ulcerative colitis",
    "ckd5": "chronic kidney disease stage 5", "bmi": "", "bd": "", "tds": "", "od": "", "prn": "",
}

LAY = [
    (r"\bjiggers?\b", "tungiasis"), (r"\bbilharzia\w*", "schistosomiasis"), (r"\bthrush\b", "candidosis"),
    (r"frozen shoulder", "adhesive capsulitis of shoulder"), (r"enteric fever", "typhoid fever"),
    (r"\bpiles\b", "haemorrhoids"), (r"\bshingles\b", "zoster"), (r"chicken ?pox", "varicella"),
    (r"german measles", "rubella"), (r"whooping cough", "pertussis"), (r"pink eye", "conjunctivitis"),
    (r"heartburn", "gastro oesophageal reflux"), (r"ringworm", "dermatophytosis tinea"), (r"\btinea\b", "dermatophytosis tinea"),
    (r"\bboils?\b", "furuncle"), (r"\bstye\b", "hordeolum"), (r"glue ear", "otitis media with effusion"),
    (r"slipped disc", "intervertebral disc displacement"), (r"kidney stones?", "calculus of kidney"),
    (r"gall ?stones?", "cholelithiasis"), (r"\bfibroids?\b", "leiomyoma of uterus"),
    (r"high blood pressure", "hypertension"), (r"heart attack", "myocardial infarction"),
    (r"\bfits\b", "seizure epilepsy"), (r"\bflu\b", "influenza"), (r"cold sores?", "herpes simplex labialis"),
    (r"athlete'?s foot", "tinea pedis dermatophytosis of foot"), (r"\bdysentery\b", "dysentery"),
    (r"prediabetes|pre-diabetes", "impaired fasting glucose intermediate hyperglycaemia"),
    (r"low (blood )?sugar", "hypoglycaemia"), (r"high (blood )?sugar", "hyperglycaemia"),
    (r"\bbreathless\w*", "dyspnoea"), (r"tummy|stomach ache", "abdominal pain"),
]

NEGATION = re.compile(
    r"\b(?:no|not|nil|denies|denied|without|neg|negative for)\b[^.;,\n:]*"
    r"|[^.;,\n:]*\b(?:excluded|ruled out|negative|neg)\b",
    re.I,
)
DX_LINE = re.compile(r"(?im)^\s*(?:a|ax|dx|imp|impression|assessment|diagnosis|diagnoses|a/p)\s*[:\-]\s*(.*)$")
DX_INLINE = re.compile(r"(?i)\b(?:dx|imp|impression|diagnosis|assessment)\s*[:\-]?\s*([^.\n]*)")
DOCTOR_SAYS = re.compile(r"(?i)\b(?:this is|you have|it's|it is|looks like|consistent with|diagnosis is)\b([^.?!\n]*)")


def normalize(text):
    t = text.lower()
    for pat, rep in US_UK:
        t = re.sub(pat, rep, t)
    for pat, rep in LAY:
        t = re.sub(pat, lambda m, rep=rep: m.group(0) + " " + rep, t)
    return t


def stem(w):
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "us", "is", "as")):
        return w[:-1]
    return w


def tokens(text):
    out = []
    for w in TOKEN.findall(normalize(text)):
        if w in ABBREV:
            out.extend(TOKEN.findall(ABBREV[w]))
            continue
        if w in STOP or len(w) < 2:
            continue
        out.append(stem(w))
    return [t for t in out if t not in STOP]


def drop_negations(text):
    return NEGATION.sub(" ", text)


def weighted_query(text):
    """Token weights for a note: diagnosis statements count more than the rest."""
    weights = {}

    def add(chunk, w):
        for t in tokens(drop_negations(chunk)):
            weights[t] = weights.get(t, 0.0) + w

    add(text, 1.0)
    for m in DX_LINE.finditer(text):
        add(m.group(1), 4.0)
    for m in DX_INLINE.finditer(text):
        add(m.group(1), 2.0)
    for m in DOCTOR_SAYS.finditer(text):
        add(m.group(1), 1.5)
    return weights
