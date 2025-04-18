def get_peers(ticker_symbol):
    static_peers = {
        "TGT": ["WMT", "COST", "KR", "BJ"],
        "AAPL": ["MSFT", "GOOGL", "DELL"],
        "NFLX": ["DIS", "CMCSA", "PARA"],
        "META": ["GOOGL", "SNAP", "PINS"],
        "TSLA": ["F", "GM", "RIVN"]
    }

    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        sector = info.get("sector", "")
        industry = info.get("industry", "")
    except:
        sector, industry = "", ""

    peers = static_peers.get(ticker_symbol.upper(), [])
    return peers, sector, industry
