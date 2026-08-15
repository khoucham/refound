"""matcher.py — TF-IDF + cosine similarity matching engine."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class Matcher:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english",
                                          ngram_range=(1, 2))
        self.fitted = False

    def fit(self, descriptions):
        """Learn the vocabulary from ALL report descriptions in the DB."""
        self.vectorizer.fit(descriptions)
        self.fitted = True

    def top_matches(self, query_description, candidates, k=3):
        """
        candidates: list of dicts, each with at least 'id' and 'description'.
        Returns the k most similar candidates, best first, each with a
        'similarity' score added (0.0 to 1.0).
        """
        if not candidates:
            return []
        q_vec = self.vectorizer.transform([query_description])
        c_vecs = self.vectorizer.transform([c["description"] for c in candidates])
        sims = cosine_similarity(q_vec, c_vecs)[0]
        ranked = sorted(zip(candidates, sims), key=lambda x: x[1], reverse=True)
        return [dict(c, similarity=round(float(s), 3)) for c, s in ranked[:k]]