"""verifier.py — fuzzy string matching for secret-question answers."""
from rapidfuzz import fuzz

THRESHOLD = 70  # 0-100. Tune this in Week 5 testing.


def check_answer(submitted, stored):
    """
    token_set_ratio ignores word order and duplicated words, so
    'photo of my dog' vs 'my dog photo' scores ~100.
    Returns (passed: bool, score: float).
    """
    score = fuzz.token_set_ratio(submitted.lower().strip(),
                                 stored.lower().strip())
    return score >= THRESHOLD, round(score, 1)


if __name__ == "__main__":
    tests = [
        ("blue nokia", "blue Nokia"),          # case difference  -> pass
        ("blu nokia", "blue nokia"),           # typo             -> pass
        ("nokia that is blue", "blue nokia"),  # reworded         -> pass
        ("a blue nokia phone", "blue nokia"),  # extra words      -> pass
        ("red iphone", "blue nokia"),          # wrong            -> FAIL
        ("phone", "blue nokia"),               # too vague guess  -> FAIL
    ]
    for submitted, stored in tests:
        passed, score = check_answer(submitted, stored)
        print(f"{score:5.1f}  {'PASS' if passed else 'FAIL'}   "
              f"'{submitted}' vs '{stored}'")