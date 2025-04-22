import requests
from bs4 import BeautifulSoup
import streamlit as st

USER_AGENT = "YourName your.email@example.com"

@st.cache_data(show_spinner=False)
def load_ticker_to_cik() -> dict[str, str]:
    """
    Download and parse SEC’s ticker→CIK mapping.
    Skips any malformed lines.
    """
    url = "https://www.sec.gov/include/ticker.txt"
    r = requests.get(url, headers={"User-Agent": USER_AGENT})
    r.raise_for_status()

    mapping = {}
    for line in r.text.splitlines():
        if "|" not in line:
            continue
        ticker, cik = line.split("|", 1)
        ticker = ticker.strip().upper()
        cik = cik.strip()
        if ticker and cik:
            mapping[ticker] = cik

    return mapping

@st.cache_data(show_spinner=False)
def get_sic_from_cik(cik: str) -> str:
    """
    Scrape a company’s SEC page to extract its 4‑digit SIC code.
    """
    url = (
        "https://www.sec.gov/cgi-bin/browse-edgar"
        f"?CIK={cik}&action=getcompany&owner=exclude"
    )
    r = requests.get(url, headers={"User-Agent": USER_AGENT})
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    th = soup.find("th", string="SIC")
    if not th:
        return ""
    td = th.find_next_sibling("td")
    return td.get_text(strip=True) if td else ""

@st.cache_data(show_spinner=False)
def get_peer_tickers_by_sic(sic: str, ticker_map: dict[str, str]) -> list[str]:
    """
    Given an SIC, fetch all peer CIKs from EDGAR and map back to tickers.
    """
    url = (
        "https://www.sec.gov/cgi-bin/browse-edgar"
        f"?action=getcompany&SIC={sic}&owner=exclude&count=200"
    )
    r = requests.get(url, headers={"User-Agent": USER_AGENT})
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    peer_ciks = {
        a["href"].split("CIK=")[1].split("&")[0]
        for a in soup.select("table.tableFile2 a[href*='CIK=']")
    }

    # invert the ticker→CIK map
    cik_to_ticker = {c: t for t, c in ticker_map.items()}
    return [cik_to_ticker[c] for c in peer_ciks if c in cik_to_ticker]

def get_dynamic_peers(ticker: str) -> list[str]:
    """
    Top‑level helper: ticker → CIK → SIC → [peer tickers].
    """
    ticker = ticker.upper().strip()
    ticker_map = load_ticker_to_cik()
    cik = ticker_map.get(ticker)
    if not cik:
        return []
    sic = get_sic_from_cik(cik)
    if not sic:
        return []
    peers = get_peer_tickers_by_sic(sic, ticker_map)
    # remove self if it sneaks in
    return [p for p in peers if p != ticker]
