# At the top of your main app (e.g. 1_Company_Snapshot.py or your __init__.py)
import streamlit as st
from textblob import TextBlob
import yfinance as yf

# (Paste your existing get_recent_news_sentiment here)

def get_recent_news_sentiment(ticker):
    news = yf.Ticker(ticker).news
    sentiments = []
    for article in news[:5]:
        title = article.get("title", "")
        sentiment = TextBlob(title).sentiment.polarity
        sentiments.append((title, sentiment))
    return sentiments

# === Page selector ===
st.set_page_config(layout="wide")
page = st.sidebar.selectbox("🔎 Choose a page", [
    "🏢 Company Snapshot",
    "💸 Valuation Advisor",
    "📂 Financial Fundamentals",
    "🧠 Risk-Matched Stocks",
    "📰 News & Sentiment"   # ← new option
])

# === Existing pages ===
if page == "🏢 Company Snapshot":
    # ... your existing code ...
    pass

elif page == "💸 Valuation Advisor":
    # ... your existing code ...
    pass

# (other elifs)

# === New News & Sentiment page ===
elif page == "📰 News & Sentiment":
    st.title("📰 Real-Time News Sentiment")
    ticker_input = st.text_input("Enter ticker symbol", "AAPL").upper()
    
    # Auto-refresh every 60 seconds (optional)
    st.experimental_rerun()  # or use st_autorefresh from streamlit_autorefresh

    if ticker_input:
        st.markdown(f"### Latest headlines for **{ticker_input}**")
        try:
            data = get_recent_news_sentiment(ticker_input)
            if not data:
                st.warning("No recent news found.")
            else:
                # Display headlines + polarity
                for title, score in data:
                    color = "green" if score>0 else "red" if score<0 else "gray"
                    st.markdown(f"- **{score:+.2f}** <span style='color:{color}'>●</span>  {title}", unsafe_allow_html=True)
                
                # Quick bar chart of sentiment scores
                scores = [s for (_,s) in data]
                st.bar_chart(scores)
        except Exception as e:
            st.error("Failed to fetch news. Try again later.")

    st.caption("Data via Yahoo Finance + TextBlob sentiment")
