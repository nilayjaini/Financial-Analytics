import requests
from bs4 import BeautifulSoup
import streamlit as st

@st.cache_data(show_spinner=False)
def load_ticker_to_cik():
    """Download and parse SEC’s ticker→CIK map once."""
    url = "https://www.sec.gov/include/ticker.txt"
    txt = requests.get(url, headers={"User-Agent":"youremail@example.com"}).text
    return {t.upper(): c for t, c in (line.split("|") for line in txt.splitlines())}

@st.cache_data(show_spinner=False)
def get_sic_from_cik(cik: str) -> str:
    """Fetch a company’s SIC code from its SEC company page."""
    url = f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={cik}&action=getcompany&owner=exclude"
    r = requests.get(url, headers={"User-Agent":"youremail@example.com"})
    soup = BeautifulSoup(r.text, "html.parser")
    # find the row where <th>SIC</th> and grab the next <td>
    row = soup.find("th", string="SIC")
    return row.find_next_sibling("td").get_text(strip=True)

@st.cache_data(show_spinner=False)
def get_peer_tickers_by_sic(sic: str, ticker_map: dict) -> list[str]:
    """Get all company CIKs for a given SIC, map back to tickers."""
    url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&SIC={sic}&owner=exclude&count=200"
    r = requests.get(url, headers={"User-Agent":"youremail@example.com"})
    soup = BeautifulSoup(r.text, "html.parser")
    peers = set()
    # each row link to “?CIK=0000…”
    for a in soup.select("table.tableFile2 a"):
        href = a.get("href","")
        if "CIK=" in href:
            cik = href.split("CIK=")[1].split("&")[0]
            peers.add(cik)
    # invert ticker_map to CIK→ticker
    cik_to_ticker = {c: t for t, c in ticker_map.items()}
    # translate and filter
    return [cik_to_ticker[c] for c in peers if c in cik_to_ticker]

def get_dynamic_peers(ticker: str) -> list[str]:
    """High-level: ticker → dynamic list of peer tickers via SEC SIC."""
    ticker_map = load_ticker_to_cik()
    cik = ticker_map.get(ticker.upper())
    if not cik:
        return []
    sic = get_sic_from_cik(cik)
    return get_peer_tickers_by_sic(sic, ticker_map)
