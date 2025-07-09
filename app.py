import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import traceback
import time
from io import BytesIO

# ---------------------------
# Quadrant classification logic
# ---------------------------
def get_quadrant(net_margin, pe_ratio):
    if net_margin is None or pe_ratio is None:
        return "Not classified"
    if net_margin < 10 and pe_ratio < 15:
        return "Q1: Low margin, Low multiple"
    elif net_margin < 10 and pe_ratio >= 15:
        return "Q2: Low margin, High multiple"
    elif net_margin >= 10 and pe_ratio < 15:
        return "Q3: High margin, Low multiple"
    else:
        return "Q4: High margin, High multiple"

# ---------------------------
# YFinance fallback method with retries
# ---------------------------
def get_financials(symbol, retries=3):
    for attempt in range(retries):
        try:
            stock = yf.Ticker(symbol + ".NS")
            info = stock.info
            pe = info.get("trailingPE")
            fin = stock.financials

            if not fin.empty and "Net Income" in fin.index and "Total Revenue" in fin.index:
                ni = fin.loc["Net Income"].iloc[0]
                rev = fin.loc["Total Revenue"].iloc[0]
                nm = (ni / rev) * 100 if rev else None
            else:
                nm = None

            return {"Name": symbol, "PE Ratio": pe, "Net Margin": nm}

        except Exception as e:
            st.warning(f"⚠️ Attempt {attempt+1} failed for {symbol}: {e}")
            st.code(traceback.format_exc())
            time.sleep(5)

    st.error(f"❌ All retries failed for {symbol}")
    return {"Name": symbol, "PE Ratio": None, "Net Margin": None}

# ---------------------------
# Streamlit app
# ---------------------------
st.set_page_config(page_title="Stock Quadrant Analyzer", layout="wide")
st.title("Indian Stock Quadrant Analyzer")

st.sidebar.subheader("Enter Stock Codes (e.g., TCS, HDFCBANK, INFY)")
stock_input = st.sidebar.text_area("Stock Codes (comma separated)", "TCS,HDFCBANK,INFY")
stock_codes = [c.strip().upper() for c in stock_input.split(',') if c.strip()]

stock_data = []
for code in stock_codes:
    st.markdown(f"### \U0001F4C5 Fetching data for: `{code}`")
    data = get_financials(code)
    st.json(data)
    data["Quadrant"] = get_quadrant(data["Net Margin"], data["PE Ratio"])
    st.markdown(f"\U0001F9ED Assigned Quadrant: **{data['Quadrant']}**")
    stock_data.append(data)

df = pd.DataFrame(stock_data)

st.subheader("Stock Classification Table")
st.dataframe(df, use_container_width=True)

excel_file = BytesIO()
df.to_excel(excel_file, index=False)
excel_file.seek(0)
st.download_button("Download Excel", excel_file, file_name="stock_data.xlsx")

st.subheader("Insight Summary")
summaries = []
for _, row in df.iterrows():
    q = row['Quadrant']
    if "Q" in q:
        if 'Q4' in q:
            summaries.append(f"{row['Name']} is in {q}, suggesting it is a premium valued strong performer.")
        elif 'Q3' in q:
            summaries.append(f"{row['Name']} is in {q}, suggesting it is a potentially undervalued high performer.")
        elif 'Q2' in q:
            summaries.append(f"{row['Name']} is in {q}, suggesting it is a lower margin stock with higher valuation.")
        else:
            summaries.append(f"{row['Name']} is in {q}, suggesting it is a lower margin stock with lower valuation.")
if summaries:
    st.markdown("\n".join(f"- {s}" for s in summaries))
else:
    st.info("\u2139\ufe0f No data available for summary.")

st.subheader("Quadrant Visualization")
fig, ax = plt.subplots(figsize=(10, 6))
colors = {'Q1': 'red', 'Q2': 'orange', 'Q3': 'green', 'Q4': 'blue'}
for _, row in df.iterrows():
    q = row["Quadrant"]
    if "Q" in q:
        quad_code = q.split(":")[0]
        ax.scatter(row["PE Ratio"] or 0, row["Net Margin"] or 0, color=colors.get(quad_code, "black"), s=80)
        ax.text((row["PE Ratio"] or 0) + 0.5, (row["Net Margin"] or 0), row["Name"], fontsize=9)
ax.axhline(10, color='gray', linestyle='--')
ax.axvline(15, color='gray', linestyle='--')
ax.set_xlabel("PE Ratio")
ax.set_ylabel("Net Margin (%)")
ax.set_title("Stock Quadrant Map")
st.pyplot(fig)

st.subheader("Filter Stocks")
min_margin = st.slider("Minimum Net Margin %", 0, 50, 10)
max_pe = st.slider("Maximum PE Ratio", 5, 100, 30)
filtered = df[(df["PE Ratio"] <= max_pe) & (df["Net Margin"].fillna(0) >= min_margin)]
st.dataframe(filtered, use_container_width=True)
