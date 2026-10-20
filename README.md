
/
ReFound
An AI-assisted lost & found platform. People report lost or found items, the system suggests likely matches using text similarity, and ownership is confirmed with a secret question before any contact details are revealed.

Built as a capstone project for the HDip/BSc in Computing at Dublin Business School (DBS) by Mohamed Khoucham.

Features
Report lost or found items with description, category, location, date and optional photo
Automatic category suggestion from the description (Naive Bayes classifier)
Smart matching: each new report is instantly compared against open reports of the opposite type and category; the top 3 matches are returned (TF-IDF + cosine similarity)
Ownership verification: the finder sets a secret question; the claimant's answer is checked with fuzzy matching so typos and rewording still pass
Privacy by design: contact email and secret answer are never returned by normal endpoints. The email is revealed only after a successful verification, with a limit of 3 attempts per match
Photo upload via Cloudinary
Browse and search reports by type and keyword
How it works
Matching is a three-layer design, because picking the single right item from text alone is hard (top-1 accuracy is about 42%):

Shortlist: TF-IDF + cosine similarity returns the 3 best candidates
Photo: the user visually compares the shortlisted items
Secret question: only the true owner can answer, verified with RapidFuzz token_set_ratio (threshold 70)
Tech stack
Layer	Technology
Frontend	HTML, CSS, vanilla JavaScript (fetch)
Backend	Python, Flask, Flask-CORS
Database	SQLite
ML	scikit-learn (TF-IDF, MultinomialNB), RapidFuzz, pandas, joblib
Images	Cloudinary
Results
Evaluated on a 224-record synthetic dataset:

Module	Metric	Result
Category classifier	Accuracy	90.6%
Matching engine	Top-3 accuracy	89.1%
Matching engine	Top-1 accuracy	~42%
Project structure
refound/
├── backend/
│   ├── app.py            # Flask REST API
│   ├── database.py       # SQLite schema and connection
│   ├── seed_db.py        # Loads the synthetic dataset
│   └── ml/
│       ├── matcher.py    # TF-IDF + cosine similarity
│       ├── classifier.py # Naive Bayes category model
│       └── verifier.py   # Fuzzy secret-answer check
├── frontend/
│   ├── index.html        # Report form
│   ├── browse.html       # Browse, matches, verification
│   ├── app.js
│   └── style.css
├── data/
│   └── refound_dataset.csv
├── notebooks/
├── tests/
├── generate_dataset.py
├── validate_dataset.py
└── requirements.txt
Database
Four tables: users, reports, matches (lost/found pair with similarity score, unique per pair) and verifications (every secret-question attempt with its fuzzy score).

Getting started
Prerequisites
Python 3.11+
Git
Setup
bash
git clone https://github.com/YOUR-USERNAME/refound.git
cd refound

python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
Initialise the database and train the model
bash
cd backend
python seed_db.py          # creates refound.db and loads 224 reports
python ml/classifier.py    # trains and saves the category model
Optional: photo upload
Create backend/.env (never commit this file):

CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_key
CLOUDINARY_API_SECRET=your_secret
Run
Use two terminals.

bash
# Terminal 1: backend (http://127.0.0.1:5000)
cd backend
python app.py

# Terminal 2: frontend
cd frontend
python -m http.server 8000
Open http://localhost:8000.

On Mac, use python3 in place of python.

API
Method	Endpoint	Description
POST	/api/reports	Create a report and return instant matches
GET	/api/reports	List reports (type, category, search filters)
GET	/api/reports/<id>	Get one report
GET	/api/reports/<id>/matches	Top 3 suggested matches
GET	/api/reports/<id>/question	Secret question for a found report
POST	/api/suggest-category	Predict category and confidence
POST	/api/verify	Check a secret answer, reveal contact on pass
POST	/api/upload	Upload a photo to Cloudinary
Demo flow
Submit a found report with a secret question and answer
Submit a lost report describing the same item in different words
Open Browse, click Find matches on the lost report, then This is mine
Answer the secret question (a typo still passes) to reveal the finder's contact email
Limitations
Trained and evaluated on synthetic data, not real reports
Text-only matching; there is no image-based matching yet
Identical duplicate submissions are not detected
No user authentication in the current version
Future work
Image similarity matching (for example MobileNetV2 embeddings)
User accounts and login
Duplicate report detection
Email notifications when a new match appears
Author
Mohamed Khoucham, Dublin Business School



