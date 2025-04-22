import requests
from bs4 import BeautifulSoup
import streamlit as st

@st.cache_data(show_spinner=False)
def load_ticker_to_cik():
    """
    Download SEC’s ticker→CIK mapping, skip empty/malformed lines.
    """
    url = "https://www.sec.gov/include/ticker.txt"
    headers = {"User-Agent": "YourName your@email.com"}
    txt = requests.get(url, headers=headers).text
    mapping = {}
    for line in txt.splitlines():
        if not line or "|" not in line:
            continue
        try:
            ticker, cik = line.split("|", 1)
            mapping[ticker.upper().strip()] = cik.strip()
        except ValueError:
            # just in case
            continue
    return mapping

@st.cache_data(show_spinner=False)
def get_sic_from_cik(cik: str) -> str:
    """Scrape a company’s SEC page to extract its 4‑digit SIC code."""
    url = f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={cik}&action=getcompany&owner=exclude"
    headers = {"User-Agent": "YourName your@email.com"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    th = soup.find("th", string="SIC")
    if not th:
        return ""
    td = th.find_next_sibling("td")
    return td.get_text(strip=True) if td else ""

@st.cache_data(show_spinner=False)
def get_peer_tickers_by_sic(sic: str, ticker_map: dict) -> list[str]:
    """Fetch all company CIKs sharing this SIC, map back to tickers."""
    url = (
        "https://www.sec.gov/cgi-bin/browse-edgar"
        f"?action=getcompany&SIC={sic}&owner=exclude&count=200"
    )
    headers = {"User-Agent": "YourName your@email.com"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    peer_ciks = set()
    for a in soup.select("table.tableFile2 a"):
        href = a.get("href", "")
        if "CIK=" in href:
            cik = href.split("CIK=")[1].split("&")[0]
            peer_ciks.add(cik)
    # invert map
    cik_to_ticker = {c: t for t, c in ticker_map.items()}
    return [cik_to_ticker[c] for c in peer_ciks if c in cik_to_ticker]

def get_dynamic_peers(ticker: str) -> list[str]:
    """
    Top‑level: ticker → CIK → SIC → list of peer tickers.
    """
    ticker_map = load_ticker_to_cik()
    cik = ticker_map.get(ticker.upper())
    if not cik:
        return []
    sic = get_sic_from_cik(cik)
    if not sic:
        return []
    return get_peer_tickers_by_sic(sic, ticker_map)
