import os
import time
import re
import sqlite3
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from flask import Flask, render_template_string, request, jsonify, send_file
from io import StringIO, BytesIO

app = Flask(__name__)

# Initialize SQLite
conn = sqlite3.connect("queries.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_type TEXT,
    case_number TEXT,
    filing_year TEXT,
    response TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)''')
conn.commit()

# UI Template
html_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Court Data Fetcher</title>
    <style>
        body { font-family: Arial; padding: 20px; background: #f5f5f5; }
        form, .batch { background: white; padding: 20px; border-radius: 10px; max-width: 500px; margin: auto; margin-top: 20px; }
        input, select { width: 100%; padding: 10px; margin: 10px 0; }
        input[type="submit"], button { background-color: #4CAF50; color: white; border: none; cursor: pointer; padding: 10px; width: 100%; }
    </style>
</head>
<body>
    <h2 align="center">Court Data Fetcher</h2>
    <form action="/fetch" method="post">
        <label>Case Type</label>
        <input type="text" name="case_type" required>
        <label>Case Number</label>
        <input type="text" name="case_number" required>
        <label>Filing Year</label>
        <input type="text" name="filing_year" required>
        <input type="submit" value="Fetch Case Data">
    </form>

    <div class="batch">
        <form action="/upload-csv" method="post" enctype="multipart/form-data">
            <label>Upload CSV (case_type, case_number, filing_year)</label>
            <input type="file" name="file" accept=".csv" required>
            <input type="submit" value="Batch Fetch via CSV">
        </form>
        <form action="/batch-fetch" method="get">
            <button type="submit">Run Predefined Batch Fetch</button>
        </form>
        <form action="/download-results" method="get">
            <button type="submit">Download Results as JSON</button>
        </form>
    </div>
</body>
</html>'''

@app.route("/", methods=["GET"])
def home():
    return render_template_string(html_template)

@app.route("/fetch", methods=["POST"])
def fetch_case_data():
    case_type = request.form.get("case_type")
    case_number = request.form.get("case_number")
    filing_year = request.form.get("filing_year")
    return jsonify(fetch_single_case(case_type, case_number, filing_year))

def fetch_single_case(case_type, case_number, filing_year):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    result = {}

    try:
        driver.get("https://districts.ecourts.gov.in/faridabad")
        time.sleep(3)
        driver.find_element(By.LINK_TEXT, "Case Status").click()
        time.sleep(3)

        driver.find_element(By.ID, "tab1").click()
        time.sleep(1)
        driver.find_element(By.ID, "case_type_id").send_keys(case_type)
        driver.find_element(By.ID, "case_number_id").send_keys(case_number)
        driver.find_element(By.ID, "filing_year_id").send_keys(filing_year)
        driver.find_element(By.ID, "submit_btn_id").click()
        time.sleep(5)

        case_title = driver.find_element(By.ID, "case_title_id").text
        case_status = driver.find_element(By.ID, "status_id").text
        filing_date = driver.find_element(By.ID, "filing_date_id").text
        next_hearing = driver.find_element(By.ID, "hearing_date_id").text

        judgments, orders = [], []
        documents = driver.find_elements(By.CSS_SELECTOR, ".judgementOrderRow")
        for doc in documents:
            text = doc.text
            link = doc.find_element(By.TAG_NAME, "a").get_attribute("href")
            date = extract_date(text)
            if "Judgment" in text:
                judgments.append({"type": "Judgment", "date": date, "link": link})
            elif "Order" in text:
                orders.append({"type": "Order", "date": date, "link": link})

        result = {
            "case_type": case_type,
            "case_number": case_number,
            "filing_year": filing_year,
            "case_title": case_title,
            "status": case_status,
            "filing_date": filing_date,
            "next_hearing_date": next_hearing,
            "judgments": judgments,
            "orders": orders
        }

        cursor.execute("INSERT INTO logs (case_type, case_number, filing_year, response) VALUES (?, ?, ?, ?)",
                       (case_type, case_number, filing_year, str(result)))
        conn.commit()

    except Exception as e:
        result = {"case_type": case_type, "case_number": case_number, "filing_year": filing_year, "error": str(e)}

    finally:
        driver.quit()

    return result

@app.route("/batch-fetch", methods=["GET"])
def batch_fetch():
    cases_to_search = [
        {"case_type": "CIVIL", "case_number": "123", "filing_year": "2023"},
        {"case_type": "CRIMINAL", "case_number": "456", "filing_year": "2023"},
        {"case_type": "CIVIL", "case_number": "789", "filing_year": "2022"}
    ]
    global last_results
    last_results = [fetch_single_case(c["case_type"], c["case_number"], c["filing_year"]) for c in cases_to_search]
    return jsonify(last_results)

@app.route("/upload-csv", methods=["POST"])
def upload_csv():
    if 'file' not in request.files:
        return "No file uploaded", 400
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return "Invalid file format", 400

    stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
    reader = csv.DictReader(stream)
    global last_results
    last_results = []
    for row in reader:
        case_type = row.get("case_type")
        case_number = row.get("case_number")
        filing_year = row.get("filing_year")
        if case_type and case_number and filing_year:
            last_results.append(fetch_single_case(case_type, case_number, filing_year))
    return jsonify(last_results)

@app.route("/download-results", methods=["GET"])
def download_results():
    if not last_results:
        return "No results to download", 400
    json_str = str(last_results).replace("'", '"')
    return send_file(BytesIO(json_str.encode("utf-8")), download_name="results.json", as_attachment=True, mimetype="application/json")

def extract_date(text):
    match = re.search(r"\d{2}-\d{2}-\d{4}", text)
    if match:
        return f"{match.group(0)[6:]}-{match.group(0)[3:5]}-{match.group(0)[0:2]}"
    return "Unknown"

last_results = []

if __name__ == "__main__":
    app.run(debug=True)