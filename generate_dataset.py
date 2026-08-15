"""
ReFound - Synthetic Lost & Found Dataset Generator
==================================================
Generates a realistic synthetic dataset of lost-and-found item reports for
Dublin Business School / Dublin city context.

Key design decision: the dataset includes GROUND-TRUTH MATCHED PAIRS -
a lost report and a found report describing the SAME item using DIFFERENT
wording. This lets us objectively evaluate the TF-IDF + cosine similarity
matching engine later (top-1 / top-3 accuracy).

Output: data/refound_dataset.csv
Columns:
    report_id     - unique ID (L### for lost, F### for found)
    report_type   - 'lost' or 'found'
    category      - ground-truth category (for training the NB classifier)
    description   - free-text item description (input to TF-IDF + classifier)
    location      - where the item was lost/found
    date_reported - report date
    match_id      - shared ID linking a true lost/found pair; empty if unmatched
"""

import random
import pandas as pd
from datetime import date, timedelta

random.seed(42)

# ---------------------------------------------------------------------------
# Vocabulary pools
# ---------------------------------------------------------------------------

LOCATIONS = [
    "DBS Aungier Street - Library", "DBS Aungier Street - Canteen",
    "DBS Aungier Street - Room 4.2", "DBS Aungier Street - Reception",
    "DBS Castle House - Lecture Hall", "DBS Castle House - Computer Lab",
    "Aungier Street bus stop", "George's Street Arcade", "Camden Street",
    "St Stephen's Green", "Luas Green Line - Harcourt", "Dublin Bus 16",
    "Dublin Bus 122", "Grafton Street", "Trinity College area", "Temple Bar",
]

COLOURS = ["black", "navy blue", "dark grey", "red", "brown", "white",
           "silver", "green", "pink", "light blue", "beige", "purple"]

# Each category: list of (item, [extra detail phrases])
CATALOGUE = {
    "Electronics": [
        ("iPhone 13", ["cracked screen protector", "clear case", "photo of a dog as wallpaper", "pop socket on the back"]),
        ("Samsung Galaxy phone", ["blue silicone case", "scratched corner", "screen slightly cracked"]),
        ("AirPods Pro", ["in a white charging case", "case has a small scratch", "left earbud missing tip"]),
        ("Dell laptop", ["stickers on the lid", "in a grey sleeve", "charger attached"]),
        ("wireless mouse", ["Logitech brand", "small and portable"]),
        ("Kindle e-reader", ["black cover", "screen saver showing a book quote"]),
        ("phone charger", ["USB-C cable", "fast charging plug", "coiled cable"]),
        ("smartwatch", ["Fitbit brand", "rubber strap", "cracked glass"]),
    ],
    "Wallet/ID": [
        ("leather wallet", ["contains bank cards", "student ID inside", "small tear on the fold", "coins in the zip pocket"]),
        ("student ID card", ["DBS student card", "photo visible", "on a lanyard"]),
        ("Leap card", ["in a plastic holder", "attached to a keyring"]),
        ("card holder", ["holds three cards", "slim aluminium design"]),
        ("passport", ["Irish passport", "in a navy cover"]),
        ("driving licence", ["Irish licence", "in a clear sleeve"]),
    ],
    "Keys": [
        ("set of house keys", ["three keys on a ring", "bottle opener keyring", "red keychain tag"]),
        ("car key", ["Toyota fob", "black fob with buttons", "attached to a lanyard"]),
        ("single key", ["brass coloured", "small padlock key"]),
        ("keys with keyring", ["Eiffel Tower keyring", "fluffy pompom attached", "supermarket loyalty tags"]),
    ],
    "Bag": [
        ("backpack", ["laptop compartment", "water bottle in side pocket", "zip slightly broken", "Nike brand"]),
        ("tote bag", ["canvas material", "bookshop logo printed", "contains notebooks"]),
        ("gym bag", ["duffel style", "runners inside", "Adidas logo"]),
        ("handbag", ["shoulder strap", "gold coloured clasp", "small make-up bag inside"]),
        ("laptop bag", ["padded interior", "charger in front pocket"]),
    ],
    "Clothing": [
        ("hoodie", ["DBS logo on front", "zip-up style", "size medium"]),
        ("jacket", ["rain jacket", "puffer style", "hood with drawstring"]),
        ("scarf", ["wool material", "striped pattern", "very long"]),
        ("umbrella", ["compact folding type", "automatic open button", "broken spoke"]),
        ("beanie hat", ["knitted", "small logo on the front"]),
        ("gloves", ["touchscreen fingertips", "leather", "one pair"]),
    ],
    "Jewellery": [
        ("silver ring", ["small stone set in it", "engraved initials inside"]),
        ("necklace", ["thin chain", "heart shaped pendant", "gold coloured"]),
        ("bracelet", ["charm bracelet", "beaded", "clasp is loose"]),
        ("earring", ["single hoop", "stud with small pearl"]),
        ("watch", ["analogue face", "leather strap", "Casio brand"]),
    ],
    "Books/Documents": [
        ("notebook", ["lecture notes inside", "spiral bound", "name written inside cover"]),
        ("textbook", ["Python programming book", "statistics textbook", "highlighted pages"]),
        ("folder of documents", ["assignment printouts", "plastic wallet", "CV copies inside"]),
        ("diary", ["2026 planner", "appointments written in"]),
    ],
    "Other": [
        ("water bottle", ["stainless steel", "stickers on the side", "750ml size"]),
        ("glasses", ["prescription glasses", "in a hard case", "thin metal frames"]),
        ("sunglasses", ["polarised lenses", "in a soft pouch"]),
        ("lunch box", ["two compartments", "fork inside"]),
        ("travel mug", ["keep-cup style", "coffee stains inside"]),
    ],
}

LOST_TEMPLATES = [
    "Lost my {colour} {item} {detail_phrase}. Last seen at {loc_hint}. Really need it back.",
    "I misplaced a {colour} {item}, {detail}. I think I left it somewhere around {loc_hint}.",
    "Missing: {colour} {item}. {Detail}. Lost it on {day_phrase}, please contact me if found.",
    "Lost a {colour} {item} {detail_phrase} on {day_phrase}. It has sentimental value.",
    "Can't find my {item}, it's {colour} and {detail}. Probably dropped it near {loc_hint}.",
    "My {colour} {item} went missing {day_phrase}. {Detail}. Any help appreciated.",
]

FOUND_TEMPLATES = [
    "Found a {colour} {item} {detail_phrase} at {loc_hint}. Handed a photo in here so the owner can claim it.",
    "Picked up a {colour} {item}, {detail}, near {loc_hint}. Describe it to claim.",
    "Someone left a {colour} {item} behind at {loc_hint}. {Detail}. Contact to collect.",
    "Found: {colour} {item}. {Detail}. It was lying at {loc_hint} on {day_phrase}.",
    "I came across a {colour} {item} {detail_phrase} on {day_phrase}. Currently keeping it safe.",
]

DAY_PHRASES = ["Monday morning", "Tuesday afternoon", "Wednesday evening",
               "Thursday around lunchtime", "Friday morning", "the weekend",
               "yesterday evening", "this morning"]

LOC_HINTS = ["the library", "the canteen", "the bus stop", "the lecture hall",
             "the computer lab", "reception", "the Luas stop", "the park",
             "the main entrance", "the stairwell"]


def fill(template, colour, item, detail):
    return (template
            .replace("{colour}", colour)
            .replace("{item}", item)
            .replace("{detail_phrase}", f"with {detail}")
            .replace("{detail}", f"it has {detail}")
            .replace("{Detail}", f"It has {detail}.")
            .replace("{loc_hint}", random.choice(LOC_HINTS))
            .replace("{day_phrase}", random.choice(DAY_PHRASES)))


def random_date():
    start = date(2026, 6, 1)
    return start + timedelta(days=random.randint(0, 70))


rows = []
lost_n, found_n, match_n = 0, 0, 0

def add_row(rtype, category, desc, match_id):
    global lost_n, found_n
    if rtype == "lost":
        lost_n += 1
        rid = f"L{lost_n:03d}"
    else:
        found_n += 1
        rid = f"F{found_n:03d}"
    rows.append({
        "report_id": rid,
        "report_type": rtype,
        "category": category,
        "description": desc,
        "location": random.choice(LOCATIONS),
        "date_reported": random_date().isoformat(),
        "match_id": match_id,
    })

# ---------------------------------------------------------------------------
# 1) Ground-truth matched pairs: same item, DIFFERENT wording & details
# ---------------------------------------------------------------------------
PAIRS_PER_CATEGORY = 8   # 8 pairs x 8 categories = 64 pairs = 128 reports

for category, items in CATALOGUE.items():
    for _ in range(PAIRS_PER_CATEGORY):
        item, details = random.choice(items)
        colour = random.choice(COLOURS)
        d1, d2 = random.sample(details, k=min(2, len(details)))
        if len(details) == 1:
            d2 = d1
        match_n += 1
        mid = f"M{match_n:03d}"
        add_row("lost", category,
                fill(random.choice(LOST_TEMPLATES), colour, item, d1), mid)
        add_row("found", category,
                fill(random.choice(FOUND_TEMPLATES), colour, item, d2), mid)

# ---------------------------------------------------------------------------
# 2) Unmatched distractor reports (realistic noise)
# ---------------------------------------------------------------------------
UNMATCHED_PER_CATEGORY = 12  # 12 x 8 = 96 unmatched reports

for category, items in CATALOGUE.items():
    for _ in range(UNMATCHED_PER_CATEGORY):
        item, details = random.choice(items)
        colour = random.choice(COLOURS)
        d = random.choice(details)
        rtype = random.choice(["lost", "found"])
        tmpl = random.choice(LOST_TEMPLATES if rtype == "lost" else FOUND_TEMPLATES)
        add_row(rtype, category, fill(tmpl, colour, item, d), "")

df = pd.DataFrame(rows).sample(frac=1, random_state=42).reset_index(drop=True)
df.to_csv("data/refound_dataset.csv", index=False)

print(f"Total records: {len(df)}")
print(f"Lost: {(df.report_type=='lost').sum()}  Found: {(df.report_type=='found').sum()}")
print(f"Ground-truth matched pairs: {match_n}")
print("\nCategory balance:")
print(df.category.value_counts().to_string())
print("\nSample rows:")
print(df.head(4).to_string())
