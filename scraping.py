# scraping.py
import requests
from bs4 import BeautifulSoup

def search_case(case_type, case_no, filing_year):
    """
    Search a case in Faridabad eCourt and return parsed info & raw HTML.
    """
    url = "https://services.ecourts.gov.in/ecourtindia_v6/?p=casestatus/index&state=D&dist=8"

    # eCourts uses POST data, these names/values are from their actual form.
    data = {
        'casetype': case_type,
        'cno': case_no,
        'cyear': filing_year,
        'cCaptcha': '',
        'submit': 'Submit',
    }
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    session = requests.Session()
    try:
        res = session.post(url, data=data, headers=headers, timeout=30)
        html = res.text
        if 'No Case Found' in html:
            return {"error": "No case found. Please check the details."}, html
        soup = BeautifulSoup(html, "html.parser")
        # Parse parties
        party_tag = soup.find('span', id="PetitionerRespondent")
        party_names = party_tag.text.strip() if party_tag else "Not found"
        # Filing Date
        filing_tag = soup.find('td', string="Registration Date")
        filing_date = filing_tag.find_next_sibling('td').text.strip() if filing_tag else "NA"
        # Next Hearing
        next_tag = soup.find('td', string="Next Hearing Date")
        next_hearing = next_tag.find_next_sibling('td').text.strip() if next_tag else "NA"
        # Orders/Judgments
        pdf_section = soup.find('table', id="order_jud_tbl") or soup.find('table', class_="order_table")
        pdfs = []
        if pdf_section:
            rows = pdf_section.find_all('tr')[1:] # skip header
            for row in rows:
                cols = row.find_all('td')
                if not cols:
                    continue
                order_date = cols[1].get_text(strip=True)
                pdf_link = cols[-1].find('a')['href'] if cols[-1].find('a') else None
                if pdf_link and not pdf_link.startswith("http"):
                    pdf_link = "https://services.ecourts.gov.in" + pdf_link
                pdfs.append({"date": order_date, "url": pdf_link})
        latest_pdf = pdfs[-1] if pdfs else None
        return {
            "party_names": party_names,
            "filing_date": filing_date,
            "next_hearing": next_hearing,
            "pdfs": pdfs,
            "latest_pdf": latest_pdf,
        }, html
    except Exception as e:
        return {"error": f"Error fetching/parsing court data: {e}"}, ""