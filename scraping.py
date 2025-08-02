import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def search_case(case_type, case_no, filing_year):
    base_url = "https://districts.ecourts.gov.in/faridabad"
    search_url = f"{base_url}/case-status"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    payload = {
        "case_type": case_type,
        "case_no": case_no,
        "case_year": filing_year
    }

    with requests.Session() as session:
        response = session.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        form = soup.find("form")
        if not form:
            return {"error": "Case status form not found."}

        action_url = form.get("action") or search_url
        form_url = urljoin(search_url, action_url)

        case_response = session.post(form_url, data=payload, headers=headers)
        case_soup = BeautifulSoup(case_response.text, "html.parser")

        case_title = case_soup.find("h2")
        status = case_soup.find("div", class_="case-status")

        orders = []
        judgments = []

        tables = case_soup.find_all("table")
        for table in tables:
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            rows = table.find_all("tr")
            for row in rows[1:]:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    doc_type = cols[0].get_text(strip=True).lower()
                    date = cols[1].get_text(strip=True) if len(cols) > 2 else ""
                    link = cols[-1].find("a")
                    if link and link.has_attr("href"):
                        doc_url = urljoin(search_url, link['href'])
                        if "judgment" in doc_type:
                            judgments.append({"type": "Judgment", "date": date, "link": doc_url})
                        elif "order" in doc_type:
                            orders.append({"type": "Order", "date": date, "link": doc_url})

        if not orders and not judgments:
            return {
                "case_title": case_title.get_text(strip=True) if case_title else "N/A",
                "status": status.get_text(strip=True) if status else "N/A",
                "message": "No orders or judgments found."
            }

        return {
            "case_title": case_title.get_text(strip=True) if case_title else "N/A",
            "status": status.get_text(strip=True) if status else "N/A",
            "orders": orders,
            "judgments": judgments
        }
