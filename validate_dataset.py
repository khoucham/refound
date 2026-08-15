"""
ReFound - Dataset Validation & ML Feasibility Check
===================================================
Runs BEFORE building the system, to prove the synthetic dataset supports:
  1. TF-IDF + cosine similarity matching (top-1 / top-3 accuracy on
     ground-truth pairs)
  2. Multinomial Naive Bayes category classification (5-fold CV accuracy)
"""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score

df = pd.read_csv("data/refound_dataset.csv").fillna({"match_id": ""})

# ---------------- Basic EDA ----------------
print("=" * 60)
print("BASIC EDA")
print("=" * 60)
print(f"Records: {len(df)} | Lost: {(df.report_type=='lost').sum()} | "
      f"Found: {(df.report_type=='found').sum()}")
print(f"Missing values: {df.isna().sum().sum()}")
print(f"Duplicate descriptions: {df.description.duplicated().sum()}")
print(f"Description length (words): min={df.description.str.split().str.len().min()}, "
      f"mean={df.description.str.split().str.len().mean():.1f}, "
      f"max={df.description.str.split().str.len().max()}")

# ---------------- Matching engine feasibility ----------------
print("\n" + "=" * 60)
print("MATCHING ENGINE CHECK (TF-IDF + cosine similarity)")
print("=" * 60)

lost = df[df.report_type == "lost"].reset_index(drop=True)
found = df[df.report_type == "found"].reset_index(drop=True)

vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
vec.fit(df.description)
L = vec.transform(lost.description)
F = vec.transform(found.description)
sims = cosine_similarity(L, F)

top1 = top3 = evaluated = 0
sim_of_true_match = []

for i, row in lost.iterrows():
    if not row.match_id:
        continue
    true_idx = found.index[found.match_id == row.match_id]
    if len(true_idx) == 0:
        continue
    evaluated += 1
    true_idx = true_idx[0]
    ranking = sims[i].argsort()[::-1]
    rank = list(ranking).index(true_idx)
    sim_of_true_match.append(sims[i][true_idx])
    if rank == 0:
        top1 += 1
    if rank < 3:
        top3 += 1

print(f"Ground-truth pairs evaluated: {evaluated}")
print(f"Top-1 accuracy: {top1/evaluated:.1%}  (true match is the #1 suggestion)")
print(f"Top-3 accuracy: {top3/evaluated:.1%}  (true match in top 3 suggestions)")
print(f"Mean cosine similarity of true matches: "
      f"{sum(sim_of_true_match)/len(sim_of_true_match):.3f}")

# ---------------- Category classifier feasibility ----------------
print("\n" + "=" * 60)
print("CATEGORY CLASSIFIER CHECK (Multinomial Naive Bayes)")
print("=" * 60)

pipe = Pipeline([
    ("tfidf", TfidfVectorizer(stop_words="english")),
    ("nb", MultinomialNB()),
])
scores = cross_val_score(pipe, df.description, df.category, cv=5)
print(f"5-fold CV accuracy: {scores.mean():.1%} (+/- {scores.std():.1%})")
print("Per fold:", [f"{s:.1%}" for s in scores])
