# ─── at the top of your file ──────────────────────────────────────────────────
import streamlit as st
import yfinance as yf
from transformers import pipeline

# load once (this can take ~10–20s on first run)
@st.cache_resource
def load_finbert():
    return pipeline(
        "sentiment-analysis",
        model="yiyanghkust/finbert-tone",
        tokenizer="yiyanghkust/finbert-tone",
        return_all_scores=False
    )

finbert = load_finbert()


# ─── replace your existing get_recent_news_sentiment ────────────────────────
def get_recent_news_sentiment(ticker):
    news_items = yf.Ticker(ticker).news[:5]
    results = []
    for article in news_items:
        title = article.get("title", "").strip()
        if not title:
            continue

        # FinBERT returns a dict like {'label': 'POSITIVE', 'score': 0.99}
        pred = finbert(title)[0]
        label = pred["label"]       # POSITIVE / NEUTRAL / NEGATIVE
        score = pred["score"]       # float in [0,1]

        # map to a polarity-like scale if you want:
        #   POSITIVE  -> +score
        #   NEUTRAL   ->  0
        #   NEGATIVE  -> −score
        polarity = {
            "POSITIVE": +score,
            "NEUTRAL":  0.0,
            "NEGATIVE": -score
        }[label]

        results.append({
            "title":     title,
            "label":     label,
            "score":     score,
            "polarity":  polarity
        })
    return results


# ─── in your “News & Sentiment” page ─────────────────────────────────────────
elif page == "📰 News & Sentiment":
    st.title("📰 Real-Time News Sentiment (FinBERT)")
    ticker_input = st.text_input("Enter ticker symbol", "AAPL").upper()
    if ticker_input:
        try:
            items = get_recent_news_sentiment(ticker_input)
            if not items:
                st.warning("No recent headlines found.")
            else:
                # Display each with color coding
                for it in items:
                    color = "green" if it["polarity"]>0 \
                            else "red"   if it["polarity"]<0 \
                            else "gray"
                    st.markdown(
                        f"- **{it['label']}** ({it['score']:.2f}) "
                        f"<span style='color:{color}'>●</span>  {it['title']}",
                        unsafe_allow_html=True
                    )
                # Chart the polarity scores
                st.bar_chart([it["polarity"] for it in items])
        except Exception as e:
            st.error("Error fetching or processing news.")
            st.exception(e)

    st.caption("Sentiment via FinBERT (`yiyanghkust/finbert-tone`)")
