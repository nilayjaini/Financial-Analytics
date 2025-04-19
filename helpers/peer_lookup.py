def get_peers(ticker_symbol):
    static_peers = {
    # 🛒 Retail
    "TGT": ["WMT", "COST", "KR", "BJ"],
    "WMT": ["TGT", "COST", "KR", "BJ"],
    "COST": ["WMT", "TGT", "BJ", "KR"],
    "KR": ["WMT", "TGT", "COST", "ACI"],  # Albertsons
    "BJ": ["WMT", "TGT", "COST"],

    # 📱 Consumer Tech / Hardware
    "AAPL": ["MSFT", "GOOGL", "DELL", "HPQ"],
    "MSFT": ["AAPL", "GOOGL", "ORCL", "IBM"],
    "GOOGL": ["MSFT", "META", "AAPL", "AMZN"],
    "DELL": ["HPQ", "AAPL", "LENOVO"],  # Lenovo not traded in US, use if needed
    "HPQ": ["DELL", "AAPL"],

    # 📺 Media & Streaming
    "NFLX": ["DIS", "CMCSA", "PARA", "WBD"],
    "DIS": ["NFLX", "PARA", "WBD", "CMCSA"],
    "CMCSA": ["DIS", "NFLX", "PARA"],
    "PARA": ["DIS", "NFLX", "WBD"],
    "WBD": ["DIS", "NFLX", "PARA"],

    # 📢 Social & Digital Ads
    "META": ["GOOGL", "SNAP", "PINS", "TWTR"],
    "SNAP": ["META", "PINS", "TWTR"],
    "PINS": ["META", "SNAP", "TWTR"],
    "TWTR": ["META", "SNAP", "PINS"],

    # 🚗 Auto & EV
    "TSLA": ["F", "GM", "RIVN", "LCID"],
    "F": ["GM", "TSLA", "STLA"],
    "GM": ["F", "TSLA", "STLA"],
    "RIVN": ["TSLA", "LCID"],
    "LCID": ["TSLA", "RIVN"],
    "STLA": ["F", "GM"],  # Stellantis

    # 🛒 E-Commerce & Consumer Services
    "AMZN": ["BABA", "WMT", "TGT", "EBAY"],
    "EBAY": ["AMZN", "BABA"],
    "BABA": ["AMZN", "JD"],  # JD.com for context

    # 🛢️ Energy sector
    "XOM": ["CVX", "COP", "BP", "SHEL", "TOT"]    
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
