# app.py
from flask import Flask, render_template, request, send_file, url_for
from datetime import datetime
import io
from scraping import search_case
from models import db, QueryLog

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///court_fetcher.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Case types (fill with common for district court, extend as needed)
CASE_TYPES = [
    {'code': 'CS', 'desc': 'Civil Suit (CS)'},
    {'code': 'CR', 'desc': 'Criminal (CR)'},
    {'code': 'CA', 'desc': 'Civil Appeal (CA)'},
    {'code': 'CC', 'desc': 'Complaint Case (CC)'},
    {'code': 'MACT', 'desc': 'MACT Case (MACT)'},
]

@app.before_request
def create_tables():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        case_type = request.form["case_type"]
        case_no = request.form["case_no"]
        filing_year = request.form["filing_year"]
        result, raw_html = search_case(case_type, case_no, filing_year)
        error_message = result.get("error")
        # Log query
        query = QueryLog(
            case_type=case_type,
            case_no=case_no,
            filing_year=filing_year,
            timestamp=datetime.now(),
            raw_response=raw_html,
            error_message=error_message,
        )
        db.session.add(query)
        db.session.commit()
        if error_message:
            return render_template("error.html", message=error_message)
        return render_template("result.html", data=result, case_type=case_type,
                              case_no=case_no, filing_year=filing_year)
    return render_template("index.html", case_types=CASE_TYPES)

@app.route("/download_pdf")
def download_pdf():
    url = request.args.get("url")
    if not url or not url.startswith("http"):
        return "Invalid PDF link", 400
    try:
        import requests
        r = requests.get(url)
        pdf_bytes = io.BytesIO(r.content)
        filename = url.split("/")[-1]
        return send_file(pdf_bytes, as_attachment=True,
                         download_name=filename,
                         mimetype='application/pdf')
    except Exception:
        return "Could not fetch PDF", 500

if __name__ == "__main__":
    app.run(debug=True)
