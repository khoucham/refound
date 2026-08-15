from ml.classifier import load_model, suggest_category

model = load_model()
tests = [
    "lost my phone with a cracked screen and blue case",
    "black leather wallet with student ID and bank cards",
    "set of keys with a red keyring and bottle opener",
    "navy blue backpack with a laptop inside",
]
for t in tests:
    print(suggest_category(model, t), "<-", t)