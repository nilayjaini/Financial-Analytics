# master_data_app.py
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="P/E Back-test", layout="wide")

# -----------------------------------------------------------
# 1. Upload / read workbook
# -----------------------------------------------------------
DEFAULT_FILE = "Master_data_clean.xlsx"

uploaded = st.file_uploader(
    "Upload cleaned workbook (or leave blank to use Master_data_clean.xlsx)",
    type=["xlsx"],
)

if uploaded:
    raw_bytes = uploaded.read()
    wb = pd.ExcelFile(BytesIO(raw_bytes))
else:
    wb = pd.ExcelFile(DEFAULT_FILE)

st.sidebar.success("Workbook loaded ✔️")

# -----------------------------------------------------------
# 2. Load the four sheets into DataFrames
# -----------------------------------------------------------
meta_df   = wb.parse("Metadata")
eps_df    = wb.parse("EPS")
price_df  = wb.parse("Price")

# years from columns (int)
YEARS = [c for c in eps_df.columns if isinstance(c, int)]

# -----------------------------------------------------------
# 3. Helper: tidy → long format
# -----------------------------------------------------------
def wide_to_long(df, value_name):
    return (
        df.melt(id_vars=["Ticker"], value_vars=YEARS,
                var_name="Year", value_name=value_name)
    )

eps_long   = wide_to_long(eps_df,   "EPS")
price_long = wide_to_long(price_df, "Price")

# merge everything
data = (
    meta_df
    .merge(eps_long,   on="Ticker")
    .merge(price_long, on=["Ticker", "Year"])
)

# current-year P/E
data["PE"] = data["Price"] / data["EPS"]

# -----------------------------------------------------------
# 4. Peer median P/E by gsubind × year
# -----------------------------------------------------------
peer = (
    data
    .query("PE > 0 and PE < 200")            # same bounds as Excel
    .groupby(["gsubind", "Year"], as_index=False)["PE"]
    .median()
    .rename(columns={"PE": "Peer_PE"})
)

data = data.merge(peer, on=["gsubind", "Year"], how="left")

# -----------------------------------------------------------
# 5. Generate signal + realised direction
# -----------------------------------------------------------
data["Signal"] = (data["PE"] < data["Peer_PE"]).map(
    {True: "UNDER", False: "OVER"}
)

# future price (Year+1)
future_price = (
    price_long
    .assign(Year=lambda d: d["Year"] - 1)    # to align t with t+1
    .rename(columns={"Price": "Price_t_plus_1"})
)
data = data.merge(future_price, on=["Ticker", "Year"], how="left")

data["Price_Move"] = data["Price_t_plus_1"] > data["Price"]
data["Outcome"] = data.apply(
    lambda r: "UP"   if r["Price_Move"] else "DOWN", axis=1
)

# hit if UNDER & UP  or  OVER & DOWN
data["Hit"] = ((data["Signal"] == "UNDER") & (data["Outcome"] == "UP")) | \
              ((data["Signal"] == "OVER")  & (data["Outcome"] == "DOWN"))
data["Hit"] = data["Hit"].astype("int")      # 1 / 0

# -----------------------------------------------------------
# 6. Sidebar – ticker selection
# -----------------------------------------------------------
tickers = sorted(data["Ticker"].unique())
sel = st.sidebar.selectbox("Pick a ticker", tickers, index=0)

sub = data.query("Ticker == @sel").sort_values("Year")

# -----------------------------------------------------------
# 7. Main dashboard
# -----------------------------------------------------------
st.header(f"📈 {sel} – P/E vs. Peer Median")

st.line_chart(
    sub.set_index("Year")[["PE", "Peer_PE"]],
    height=300,
)

# yearly confusion table
conf = (
    sub.pivot_table(
        index="Signal", columns="Outcome",
        values="Hit", aggfunc="count", fill_value=0
    )
    .astype(int)
)
st.subheader("Signal vs. Price-move (count)")
st.dataframe(conf)

hit_rate = sub["Hit"].mean()
st.metric("Hit-rate", f"{hit_rate:.1%}")

# -----------------------------------------------------------
# 8. Portfolio-wide view
# -----------------------------------------------------------
st.subheader("Portfolio hit-rates")
port = (
    data.dropna(subset=["Hit"])
        .groupby("Ticker", as_index=False)["Hit"]
        .mean()
        .rename(columns={"Hit": "Hit_Rate"})
        .sort_values("Hit_Rate", ascending=False)
)
st.dataframe(port.style.format({"Hit_Rate": "{:.1%}"}), height=500)
