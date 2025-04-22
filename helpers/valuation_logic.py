# helpers/peer_lookup.py
import requests
import streamlit as st
from bs4 import BeautifulSoup
from functools import lru_cache

# SEC requires a descriptive User-Agent
HEADERS = {
    "User-Agent": "Your Name your_email@example.com",
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov",
}

@lru_cache()
def load_ticker_cik_map():
    """
    Loads the SEC's master ticker -> CIK mapping.
    Returns { 'AAPL': '0000320193', ... }
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    data = r.json()
    # the JSON is keyed by integer strings, with values { ticker, cik_str, ... }
    return {
        val["ticker"].upper(): val["cik_str"].zfill(10)
        for val in data.values()
    }

@lru_cache()
def get_company_sic(cik):
    """
    Given a zero‑padded 10‑digit CIK, pull its SIC from the submissions JSON.
    """
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    info = r.json()
    return info.get("sic")

def get_peers(ticker, peer_count=8):
    """
    Dynamic peer lookup via SEC SIC.
    Returns (peers, sector, industry)
    """
    ticker = ticker.upper()
    mapping = load_ticker_cik_map()
    cik = mapping.get(ticker)
    if not cik:
        st.warning(f"Ticker {ticker} not found in SEC mapping.")
        return [], "", ""

    # 1) get SIC
    sic = get_company_sic(cik)
    if not sic:
        st.warning(f"SIC code not found for {ticker}.")
        return [], "", ""

    # 2) pull EDGAR browse page for that SIC
    browse_url = (
        f"https://www.sec.gov/cgi-bin/browse-edgar"
        f"?action=getcompany&SIC={sic}&owner=exclude&count={peer_count}&output=xml"
    )
    r2 = requests.get(browse_url, headers=HEADERS)
    r2.raise_for_status()
    soup = BeautifulSoup(r2.text, "lxml")

    # 3) extract CIKs of peers
    peer_ciks = []
    for div in soup.select("div.companyInfo"):
        span = div.find("span", class_="companyCik")
        if not span:
            continue
        peer_cik = span.text.strip().split(" ")[0]  # e.g. '0000320193'
        if peer_cik != cik:
            peer_ciks.append(peer_cik)

    # 4) map CIKs back to tickers
    reverse_map = {v: k for k, v in mapping.items()}
    peers = [reverse_map.get(pc) for pc in peer_ciks]
    peers = [p for p in peers if p]  # drop any unmapped

    # Optionally, you can also grab sector/industry from yfinance:
    info = {}
    try:
        info = requests.get(
            f"https://data.sec.gov/submissions/CIK{cik}.json",
            headers=HEADERS
        ).json().get("sicDescription", {})
    except:
        pass

    # For sector/industry, fall back to yfinance if you wish:
    # import yfinance as yf
    # yfinfo = yf.Ticker(ticker).info
    # sector = yfinfo.get("sector", "")
    # industry = yfinfo.get("industry", "")
    sector, industry = "", ""

    return peers[:peer_count], sector, industry
