import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from io import BytesIO
import traceback

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
# Yahoo Finance API via RapidAPI
# ---------------------------
API_KEY = "54bca8a40bmsh3a8ba8452230a07p17c34djsn05a34956e4af"
API_HOST = "yahoo-finance15.p.rapidapi.com"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST
}

def get_financials(symbol):
    try:
        url = f"https://yahoo-finance15.p.rapidapi.com/api/yahoo/qu/quote/{symbol}.NS"
        resp = requests.get(url, headers=HEADERS)
        data = resp.json()
        st.code(f"📦 Raw API response for {symbol}:\n{str(data)[:500]}...")

        q = data.get("quote", {})
        pe = q.get("trailingPE")
        margin = q.get("profitMargins")
        net_margin = float(margin) * 100 if isinstance(margin, (float, int)) else None

        if pe is None:
            st.warning(f"⚠️ Could not find PE for {symbol}")
        if net_margin is None:
            st.warning(f"⚠️ Could not find Net Margin for {symbol}")

        return {"Name": symbol, "PE Ratio": pe, "Net Margin": net_margin}
    except Exception as e:
        st.error(f"❌ Error fetching {symbol}: {e}")
        st.code(traceback.format_exc())
        return {"Name": symbol, "PE Ratio": None, "Net Margin": None}

# ---------------------------
# Streamlit App
# ---------------------------
st.set_page_config(page_title="Stock Quadrant Analyzer", layout="wide")
st.title("📊 Indian Stock Quadrant Analyzer")

st.sidebar.subheader("Enter Stock Codes (e.g., TCS, HDFCBANK, INFY)")
stock_input = st.sidebar.text_area("Stock Codes (comma separated)", "TCS,HDFCBANK,INFY")
stock_codes = [c.strip().upper() for c in stock_input.split(',') if c.strip()]

stock_data = []
for code in stock_codes:
    st.markdown(f"### 📅 Fetching data for: `{code}`")
    data = get_financials(code)
    st.json(data)
    data["Quadrant"] = get_quadrant(data["Net Margin"], data["PE Ratio"])
    st.markdown(f"🧭 Assigned Quadrant: **{data['Quadrant']}**")
    stock_data.append(data)

df = pd.DataFrame(stock_data)

st.subheader("📋 Stock Classification Table")
st.dataframe(df, use_container_width=True)

# Download as Excel
excel_file = BytesIO()
df.to_excel(excel_file, index=False)
excel_file.seek(0)
st.download_button("📥 Download Excel", excel_file, file_name="stock_data.xlsx")

# Summary
st.subheader("📌 Insight Summary")
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
    st.info("ℹ️ No data available for summary.")

# Visualization
st.subheader("🧭 Quadrant Visualization")
fig, ax = plt.subplots(figsize=(10, 6))
colors = {'Q1': 'red', 'Q2': 'orange', 'Q3': 'green', 'Q4': 'blue'}
for _, row in df.iterrows():
    q = row["Quadrant"]
    if "Q" in q:
        quad_code = q.split(":")[0]
        x = row["PE Ratio"] or 0
        y = row["Net Margin"] or 0
        ax.scatter(x, y, color=colors.get(quad_code, "black"), s=80)
        ax.text(x + 0.5, y, row["Name"], fontsize=9)
ax.axhline(10, color='gray', linestyle='--')
ax.axvline(15, color='gray', linestyle='--')
ax.set_xlabel("PE Ratio")
ax.set_ylabel("Net Margin (%)")
ax.set_title("Stock Quadrant Map")
st.pyplot(fig)

# Filter
st.subheader("🔍 Filter Stocks")
min_margin = st.slider("Minimum Net Margin %", 0, 50, 10)
max_pe = st.slider("Maximum PE Ratio", 5, 100, 30)
filtered = df[(df["PE Ratio"] <= max_pe) & (df["Net Margin"].fillna(0) >= min_margin)]
st.dataframe(filtered, use_container_width=True)
