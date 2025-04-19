import nltk

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
import streamlit as st
from helpers.peer_lookup import get_peers, get_recent_news_sentiment
from helpers.valuation_logic import analyze_valuation, plot_price_range

st.title("📊 Valuation & Recommendation")

col1, col2 = st.columns(2)
ticker_input = col1.text_input("Enter primary ticker", "TGT")
compare_input = col2.text_input("Compare with (optional)", "")

if ticker_input:
    peers, sector, industry = get_peers(ticker_input.upper())

    if not peers:
        st.warning("Could not fetch peer data.")
        st.stop()

    st.markdown(f"**Sector:** {sector}  \n**Industry:** {industry}  \n**Peers:** {', '.join(peers)}")
    result = analyze_valuation(ticker_input.upper(), peers)

    if not result['eps']:
        st.warning("⚠️ EPS not available for this stock — unable to calculate implied valuation.")
        st.stop()

    st.metric("EPS (TTM)", f"{result['eps']:.2f}")
    st.metric("Industry Avg P/E", f"{result['industry_pe_avg']:.2f}")

    st.subheader("Recommendation")
    st.success(result['recommendation'])

    st.subheader("📉 Valuation Range Visualization")
    plot_price_range(
        result['current_price'],
        result['implied_price_min'],
        result['implied_price_max'],
        result['implied_price']
    )

    gap = ((result['implied_price'] - result['current_price']) / result['implied_price']) * 100
    if gap > 0:
        st.caption(f"📉 Current price is **{gap:.1f}% below** peer-based valuation average.")
    else:
        st.caption(f"📈 Current price is **{abs(gap):.1f}% above** peer-based valuation average.")

    # News Sentiment Overlay
    st.subheader("📰 News Sentiment")
    try:
        sentiments = get_recent_news_sentiment(ticker_input.upper())
        for title, score in sentiments:
            sentiment_label = "🟢 Positive" if score > 0.2 else "🟡 Neutral" if score > -0.1 else "🔴 Negative"
            st.write(f"{sentiment_label} — *{title}*")
    except:
        st.caption("Could not load news sentiment.")

# Optional: Ticker Comparison
if compare_input:
    st.divider()
    st.subheader(f"📊 Comparison: {compare_input.upper()}")
    peers_2, _, _ = get_peers(compare_input.upper())
    if peers_2:
        result_2 = analyze_valuation(compare_input.upper(), peers_2)

        st.metric("EPS (TTM)", f"{result_2['eps']:.2f}" if result_2['eps'] else "N/A", label=compare_input.upper())
        st.metric("Industry Avg P/E", f"{result_2['industry_pe_avg']:.2f}")
        st.subheader("📉 Valuation Range Visualization")
        plot_price_range(
            result_2['current_price'],
            result_2['implied_price_min'],
            result_2['implied_price_max'],
            result_2['implied_price']
        )
