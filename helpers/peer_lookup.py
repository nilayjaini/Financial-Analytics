# helpers/peer_lookup.py

import requests
from bs4 import BeautifulSoup
from functools import lru_cache
import yfinance as yf

HEADERS = {
    "User-Agent": "Your Name your_email@example.com",
    "Accept-Encoding": "gzip, deflate",
}

@lru_cache(maxsize=None)
def load_ticker_cik_map() -> dict[str,str]:
    """
    Returns a dict mapping uppercase ticker -> zero-padded 10-digit CIK.
    Handles both dict- or list-based JSON from SEC.
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    data = r.json()

    # `data` may be a dict keyed by numeric strings or a list of entries
    entries = data.values() if isinstance(data, dict) else data

    mapping: dict[str,str] = {}
    for entry in entries:
        # each entry has "ticker" and "cik_str"
        t = entry.get("ticker")
        c = entry.get("cik_str")
        if t and c:
            mapping[t.upper()] = c.zfill(10)

    return mapping

@lru_cache(maxsize=None)
def get_company_sic(cik: str) -> str | None:
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json().get("sic")

def get_dynamic_peers(
    ticker: str,
    peer_count: int = 8
) -> tuple[list[str], str, str]:
    ticker = ticker.upper().strip()
    mapping = load_ticker_cik_map()
    cik = mapping.get(ticker)
    if not cik:
        return [], "", ""

    sic = get_company_sic(cik)
    if not sic:
        return [], "", ""

    browse_url = (
        "https://www.sec.gov/cgi-bin/browse-edgar"
        f"?action=getcompany&SIC={sic}"
        f"&owner=exclude&count={peer_count+1}&output=xml"
    )
    r = requests.get(browse_url, headers=HEADERS)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml-xml")
    all_ciks = [tag.text.strip() for tag in soup.find_all("cik")]
    peer_ciks = [c for c in all_ciks if c != cik][:peer_count]

    reverse_map = {v: k for k, v in mapping.items()}
    peers = [reverse_map.get(pc) for pc in peer_ciks]
    peers = [p for p in peers if p]

    # get sector & industry via yfinance fallback
    sector = industry = ""
    try:
        info = yf.Ticker(ticker).info
        sector = info.get("sector", "") or ""
        industry = info.get("industry", "") or ""
    except:
        pass

    return peers, sector, industry
