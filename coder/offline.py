import pickle
import sys

from .mms import DATA, MMS
from .search import Index
from .text import weighted_query
from .who import load_terms

FALLBACK = ["CA07.0", "MG26", "QA0Z"]
INDEX = DATA / "offline-index.pkl"


class OfflineCoder:
    def __init__(self, mms=None, extra_terms=None):
        self.mms = mms or MMS()
        self.terms = load_terms() if extra_terms is None else extra_terms
        self.index = Index(self.mms, self.terms)

    def to_leaf(self, code, scores):
        if self.mms.is_leaf(code):
            return code
        leaves = self.mms.leaves_under(code)
        best = max(leaves, key=lambda c: scores.get(c, 0.0))
        if scores.get(best, 0.0) > scores.get(code, 0.0):
            return best
        return self.mms.unspecified_child(code) or best

    def rank(self, text, k=50):
        scores = self.index.scores(weighted_query(text))
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
