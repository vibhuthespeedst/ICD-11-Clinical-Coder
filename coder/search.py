import math
from collections import defaultdict

from .text import tokens


class Index:
    """BM25 over each code's title plus its ancestors' titles and any extra terms."""

    def __init__(self, mms, extra_terms=None, k1=1.2, b=0.6):
        self.mms = mms
        self.k1, self.b = k1, b
        self.postings = defaultdict(list)
        self.doclen = {}
        extra_terms = extra_terms or {}
        for code in mms.rows:
            tf = defaultdict(float)
            for t in tokens(mms.title(code)):
                tf[t] += 1.0
            for a in mms.ancestors(code):
                for t in tokens(mms.title(a)):
                    tf[t] += 0.4
            for term in extra_terms.get(code, ()):
                for t in tokens(term):
                    tf[t] = max(tf[t], 0.8)
            self.doclen[code] = sum(tf.values()) or 1.0
            for t, f in tf.items():
                self.postings[t].append((code, f))
        n = len(self.doclen)
        self.avglen = sum(self.doclen.values()) / n
        self.idf = {t: math.log(1 + (n - len(p) + 0.5) / (len(p) + 0.5)) for t, p in self.postings.items()}

    def scores(self, query_weights):
        out = defaultdict(float)
        for t, qw in query_weights.items():
            idf = self.idf.get(t)
            if idf is None:
                continue
            for code, f in self.postings[t]:
                norm = f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.doclen[code] / self.avglen))
                out[code] += idf * norm * min(qw, 6.0)
        return out
