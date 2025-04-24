import streamlit as st
import yfinance as yf
from textblob import TextBlob
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="News & Sentiment", 
    layout="wide"
)

# ─── Helper ───────────────────────────────────────────────────────────────────
def get_recent_news_sentiment(ticker: str):
    news_items = yf.Ticker(ticker).news[:5]
    results = []
    for article in news_items:
        title = article.get("title", "").strip()
        if not title:
            continue
        polarity = TextBlob(title).sentiment.polarity
        results.append((title, polarity))
    return results

# ─── Auto-refresh every 60s ───────────────────────────────────────────────────
st_autorefresh(interval=60_000, key="news_refresh")

# ─── Page ─────────────────────────────────────────────────────────────────────
st.title("📰 Real-Time News Sentiment")
ticker = st.text_input("Enter ticker symbol", "AAPL").upper()

if ticker:
    st.markdown(f"### Latest headlines for **{ticker}**")
    try:
        data = get_recent_news_sentiment(ticker)
        if not data:
            st.warning("No recent news found.")
        else:
            for title, score in data:
                color = "green" if score > 0 else "red" if score < 0 else "gray"
                st.markdown(
                    f"- **{score:+.2f}** <span style='color:{color}'>●</span>  {title}",
                    unsafe_allow_html=True
                )

            # Bar chart of the last 5 polarity scores
            st.subheader("Sentiment Scores")
            st.bar_chart([s for (_, s) in data])
    except Exception:
        st.error("Failed to fetch or analyze news. Try again later.")

st.caption("Data via Yahoo Finance + TextBlob sentiment")
