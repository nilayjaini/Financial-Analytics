import requests
from bs4 import BeautifulSoup
import yfinance as yf

def get_peers_from_finviz(ticker):
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        peer_section = soup.find("table", class_="fullview-title")
        peer_table = peer_section.find_next_sibling("table")
        peer_links = peer_table.find_all("a", href=True)
        peers = [link.text.strip() for link in peer_links if link.text.strip() != ticker.upper()]
        return peers[:5]
    except Exception as e:
        print("Error:", e)
        return []

def get_peers(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        sector = info.get("sector", "")
        industry = info.get("industry", "")
    except:
        sector, industry = "", ""

    peers = get_peers_from_finviz(ticker_symbol)
    return peers, sector, industry
