# helpers/peer_lookup.py
import os
import requests
import yfinance as yf

#––– CONFIGURE YOUR TOKEN –––#
# Set this in your shell or Streamlit Cloud secrets:
#   export FINNHUB_TOKEN="d03tvi9r01qm4vp426jgd03tvi9r01qm4vp426k0"
FINNHUB_TOKEN = os.getenv("FINNHUB_TOKEN")

def get_peers(ticker_symbol: str):
    """
    Returns (peers_list, sector, industry)
    1) Try Finnhub peers endpoint
    2) Fallback to yfinance same‐industry scan over a small universe
    """
    peers = []

    # 1) Finnhub.io peers
    if FINNHUB_TOKEN:
        try:
            url = (
                f"https://finnhub.io/api/v1/stock/peers"
                f"?symbol={ticker_symbol}&token={FINNHUB_TOKEN}"
            )
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()          # should be a list of tickers
            if isinstance(data, list) and data:
                peers = data
        except Exception:
            peers = []

    # 2) Fallback: same‐sector / industry via yfinance
    if not peers:
        try:
            info = yf.Ticker(ticker_symbol).info
            sector  = info.get("sector", "")
            industry = info.get("industry", "")
        except Exception:
            sector, industry = "", ""
        else:
            # For demo we use a small universe; in prod swap in your S&P 500 list
            universe = ["AAPL","MSFT","GOOGL","AMZN","TSLA","NFLX","META",
                        "IBM","ORCL","INTC","CSCO","DELL","HPQ","WMT","TGT"]
            matches = []
            for t in universe:
                if t == ticker_symbol:
                    continue
                try:
                    inf = yf.Ticker(t).info
                    if inf.get("sector")==sector and inf.get("industry")==industry:
                        matches.append(t)
                except Exception:
                    pass
            peers = matches

    # finally, grab sector/industry for display
    try:
        info = yf.Ticker(ticker_symbol).info
        sector  = info.get("sector", "")
        industry = info.get("industry", "")
    except Exception:
        sector, industry = "", ""

    return peers, sector, industry
