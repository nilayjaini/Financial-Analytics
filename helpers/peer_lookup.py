# helpers/peer_lookup.py

import requests
from bs4 import BeautifulSoup
from functools import lru_cache
import yfinance as yf

# SEC requires a descriptive User-Agent
HEADERS = {
    "User-Agent": "Your Name your_email@example.com",
    "Accept-Encoding": "gzip, deflate",
}


@lru_cache(maxsize=None)
def load_ticker_cik_map() -> dict[str,str]:
    """
    Returns a dict mapping uppercase ticker -> zero-padded 10-digit CIK.
    Source: https://www.sec.gov/files/company_tickers.json
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    raw = r.json()
    # JSON keyed by numeric strings; each val has 'ticker' and 'cik_str'
    return {
        entry["ticker"].upper(): entry["cik_str"].zfill(10)
        for entry in raw.values()
    }


@lru_cache(maxsize=None)
def get_company_sic(cik: str) -> str | None:
    """
    Fetch the company's submissions JSON and return its SIC code.
    """
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    data = r.json()
    # SIC is stored at top‐level
    return data.get("sic")


def get_dynamic_peers(
    ticker: str,
    peer_count: int = 8
) -> tuple[list[str], str, str]:
    """
    For the given ticker, returns a tuple:
      ([peer_tickers...], sector, industry)
    Peers are fetched live from EDGAR by matching SIC code.
    """
    ticker = ticker.upper().strip()
    mapping = load_ticker_cik_map()
    cik = mapping.get(ticker)
    if not cik:
        return [], "", ""

    # get SIC code
    sic = get_company_sic(cik)
    if not sic:
        return [], "", ""

    # edition: fetch SEC browse-edgar by SIC in XML format
    browse_url = (
        "https://www.sec.gov/cgi-bin/browse-edgar"
        f"?action=getcompany&SIC={sic}"
        f"&owner=exclude&count={peer_count+1}&output=xml"
    )
    r = requests.get(browse_url, headers=HEADERS)
    r.raise_for_status()

    # parse XML to extract CIK tags
    soup = BeautifulSoup(r.text, "lxml-xml")
    cik_tags = [tag.text.strip() for tag in soup.find_all("cik")]
    # skip first (the company itself) and dedupe
    peer_ciks = [c for c in cik_tags if c != cik][:peer_count]

    # reverse map to tickers
    reverse_map = {v: k for k, v in mapping.items()}
    peers = [reverse_map.get(c) for c in peer_ciks]
    peers = [p for p in peers if p]  # drop any unmapped

    # fetch sector/industry via yfinance (EDGAR JSON has no industry text)
    sector, industry = "", ""
    try:
        info = yf.Ticker(ticker).info
        sector = info.get("sector", "") or ""
        industry = info.get("industry", "") or ""
    except:
        pass

    return peers, sector, industry
