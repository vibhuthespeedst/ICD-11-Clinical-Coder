import math
from collections import defaultdict

from .text import tokens


class Index:
    """BM25 where each code has one document for its title plus ancestors, and one per extra term;
    a code scores as its best document, so many synonyms cannot add up."""

    def __init__(self, mms, extra_terms=None, k1=1.2, b=0.6, term_weight=0.9):
        self.mms = mms
        self.k1, self.b = k1, b
        self.postings = defaultdict(list)
        self.doc_code, self.doc_weight, self.doclen = [], [], []
        extra_terms = extra_terms or {}
        for code in mms.rows:
            tf = defaultdict(float)
            for t in tokens(mms.title(code)):
                tf[t] += 1.0
            for a in mms.ancestors(code):
                for t in tokens(mms.title(a)):
                    tf[t] += 0.4
            self._add(code, tf, 1.0)
            for term in extra_terms.get(code, ()):
                tf = defaultdict(float)
                for t in tokens(term):
                    tf[t] += 1.0
                if tf:
                    self._add(code, tf, term_weight)
        n = len(self.doclen)
        self.avglen = sum(self.doclen) / n
        self.idf = {t: math.log(1 + (n - len(p) + 0.5) / (len(p) + 0.5)) for t, p in self.postings.items()}

    def _add(self, code, tf, weight):
        doc = len(self.doc_code)
        self.doc_code.append(code)
        self.doc_weight.append(weight)
        self.doclen.append(sum(tf.values()) or 1.0)
        for t, f in tf.items():
            self.postings[t].append((doc, f))

    def scores(self, query_weights):
        per_doc = defaultdict(float)
        for t, qw in query_weights.items():
            idf = self.idf.get(t)
            if idf is None:
                continue
            for doc, f in self.postings[t]:
                norm = f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.doclen[doc] / self.avglen))
                per_doc[doc] += idf * norm * min(qw, 6.0)
        out = {}
        for doc, s in per_doc.items():
            code = self.doc_code[doc]
            s *= self.doc_weight[doc]
            if s > out.get(code, 0.0):
                out[code] = s
        return out
