# 🏛️ Court Data Fetcher & Mini-Dashboard

A lightweight, Python-Flask-based dashboard that fetches case metadata from the **Faridabad District Court** portal using public data scraping. It supports user input, error handling, search history logging, and PDF downloads – all with a clean and responsive UI.

![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)

---

##  Court Chosen

> **Faridabad District Court (eCourts portal)**  
Website: https://districts.ecourts.gov.in/faridabad

---

##  Features

-  Search by Case Type, Number & Filing Year  
-  Displays party names, advocates, status, and more  
-  Auto logs each query in a local SQLite DB (`court_fetcher.db`)  
-  PDF download support  
-  Responsive UI with Bootstrap  
-  CAPTCHA ready (manual or automated fallback)  
-  Docker-compatible

---

##  Setup Steps

###  Local Setup (for Development)

```bash
# Clone repo
git clone https://github.com/your-username/court-data-fetcher.git
cd court-data-fetcher

# Setup virtual environment
python -m venv venv
source venv/bin/activate         # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py

Visit http://localhost:5000 in your browser.

### Docker Setup (Optional)

# Build Docker image
docker build -t court-fetcher .

# Run container
docker run -p 5000:5000 court-fetcher


##  Screenshots 

Here are sample screenshots showing different stages of the app in action:

### 🔍 Search Form  
![Search Form](dashboard.png)

### 📄 Result Display  
![Case Result](screenshots/search.png)

### 🧾 Case History or Error Page  
![Case History / Error](creenshots/result.png)
