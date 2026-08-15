from ml.matcher import Matcher

m = Matcher()
docs = [
    "black leather wallet with cards",
    "red umbrella broken spoke",
    "brown leather wallet found canteen",
]
m.fit(docs)

candidates = [
    {"id": 2, "description": docs[1]},
    {"id": 3, "description": docs[2]},
]
results = m.top_matches("lost my black wallet, leather, cards inside", candidates, k=2)
for r in results:
    print(r["similarity"], "->", r["description"])