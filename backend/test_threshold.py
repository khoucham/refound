from rapidfuzz import fuzz

# (submitted, stored, should_pass)
cases = [
    ("blue nokia", "blue Nokia", True),
    ("blu nokia", "blue nokia", True),
    ("nokia that is blue", "blue nokia", True),
    ("a blue nokia phone", "blue nokia", True),
    ("golden retriever", "a golden retriever", True),
    ("my dogs photo", "photo of my dog", True),
    ("red iphone", "blue nokia", False),
    ("phone", "blue nokia", False),
    ("samsung", "blue nokia", False),
    ("i dont know", "blue nokia", False),
]

for threshold in [50, 60, 70, 80, 90]:
    correct = sum(
        ((fuzz.token_set_ratio(s.lower(), t.lower()) >= threshold) == expected)
        for s, t, expected in cases
    )
    print(f"Threshold {threshold}: {correct}/{len(cases)} correct")