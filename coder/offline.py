import pickle
import sys
import threading

from .mms import DATA, MMS
from .search import Index
from .text import FUNCTION_WORDS, is_english, weighted_query
from .who import load_terms

FALLBACK = ["CA07.0", "MG26", "QA0Z"]
INDEX = DATA / "offline-index.pkl"
OTHER_LANGS = ("en", "es", "fr", "pt", "ar")


class OfflineCoder:
    def __init__(self, mms=None, extra_terms=None):
        self.mms = mms or MMS()
        self.terms = load_terms() if extra_terms is None else extra_terms
        self.index = Index(self.mms, self.terms)
        self.multi = None if extra_terms is None else self.index
        self.lock = threading.Lock()

    def __getstate__(self):
        state = self.__dict__.copy()
        del state["lock"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.lock = threading.Lock()

    def multilingual(self):
        """English plus WHO's Spanish, French, Portuguese and Arabic terms, for notes not in English."""
        with self.lock:
            if self.multi is None:
                self.multi = Index(self.mms, load_terms(OTHER_LANGS))
            return self.multi

    def to_leaf(self, code, scores):
        if self.mms.is_leaf(code):
            return code
        leaves = self.mms.leaves_under(code)
        best = max(leaves, key=lambda c: scores.get(c, 0.0))
        if scores.get(best, 0.0) > scores.get(code, 0.0):
            return best
        return self.mms.unspecified_child(code) or best

    def rank(self, text, k=50, english=None):
        if english is None:
            english = is_english(text)
        query = weighted_query(text)
        if english:
            index = self.index
        else:
            index = self.multilingual()
            query = {t: w for t, w in query.items() if t not in FUNCTION_WORDS}
        scores = index.scores(query)
        for code in scores:
            row = self.mms.rows[code]
            if row["chapter"] == "26":
                scores[code] *= 0.3
            elif row["residual"] and code.endswith("Y"):
                scores[code] *= 0.8
        return sorted(scores, key=scores.get, reverse=True)[:k], scores

    def predict(self, text, n=3):
        ranked, scores = self.rank(text)
        out = []
        for code in ranked:
            leaf = self.to_leaf(code, scores)
            if leaf not in out:
                out.append(leaf)
            if len(out) == n:
                break
        return out or FALLBACK[:n]


def load_offline():
    """The index pickled at image build time (python -m coder.prebuild), else a fresh build."""
    if INDEX.exists():
        try:
            with open(INDEX, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(f"prebuilt index unusable ({type(e).__name__}), building", file=sys.stderr)
    return OfflineCoder()
