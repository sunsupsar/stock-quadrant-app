# Stock Quadrant Analyzer using Screener.in HTML scraping
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from io import BytesIO
import traceback
import time

# ---------------------------
# Screener fetch function (scrapes PE and Net Margin from HTML)
# ---------------------------
def get_financials_screener(symbol):
    url = f"https://www.screener.in/company/{symbol}/"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            st.warning(f"⚠️ HTTP {response.status_code} error for {symbol}")
            return {"Name": symbol, "PE Ratio": None, "Net Margin": None}

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract PE Ratio
        pe_ratio = None
        pe_tag = soup.find("li", string=lambda s: s and "Stock P/E" in s)
        if pe_tag:
            try:
                pe_ratio = float(pe_tag.find("span").text.strip())
            except:
                st.warning(f"⚠️ PE parsing failed for {symbol}")

        # Extract Net Profit Margin from table
        net_margin = None
        ratios_table = soup.find("section", {"id": "ratio-analysis"})
        if ratios_table:
            rows = ratios_table.find_all("tr")
            for row in rows:
                if "Net profit margin" in row.text:
                    try:
                        net_margin = float(row.find_all("td")[-1].text.replace("%", "").strip())
                        break
                    except:
                        st.warning(f"⚠️ Net Margin parsing failed for {symbol}")

        return {"Name": symbol, "PE Ratio": pe_ratio, "Net Margin": net_margin}

    except Exception as e:
        st.error(f"❌ Error fetching {symbol}: {e}")
        st.code(traceback.format_exc())
        return {"Name": symbol, "PE Ratio": None, "Net Margin": None}

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
# Streamlit app
# ---------------------------
st.set_page_config(page_title="Stock Quadrant Analyzer - Screener", layout="wide")
st.title("📊 Indian Stock Quadrant Analyzer (Screener.in Edition)")

st.sidebar.subheader("Enter Stock Codes (e.g., TCS, INFY, HDFCBANK)")
stock_input = st.sidebar.text_area("Stock Codes (comma separated)", "TCS,INFY,HDFCBANK")
stock_codes = [c.strip().upper() for c in stock_input.split(',') if c.strip()]

stock_data = []
for code in stock_codes:
    st.markdown(f"### 📅 Fetching data for: `{code}`")
    data = get_financials_screener(code)
    st.json(data)
    data["Quadrant"] = get_quadrant(data["Net Margin"], data["PE Ratio"])
    st.markdown(f"🧭 Assigned Quadrant: **{data['Quadrant']}**")
    stock_data.append(data)
    time.sleep(1)  # polite scraping

df = pd.DataFrame(stock_data)

st.subheader("📋 Stock Classification Table")
st.dataframe(df, use_container_width=True)

excel_file = BytesIO()
df.to_excel(excel_file, index=False)
excel_file.seek(0)
st.download_button("Download Excel", excel_file, file_name="screener_stock_data.xlsx")

st.subheader("💡 Insight Summary")
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

st.subheader("📈 Quadrant Visualization")
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

st.subheader("🔍 Filter Stocks")
min_margin = st.slider("Minimum Net Margin %", 0, 50, 10)
max_pe = st.slider("Maximum PE Ratio", 5, 100, 30)
filtered = df[(df["PE Ratio"] <= max_pe) & (df["Net Margin"].fillna(0) >= min_margin)]
st.dataframe(filtered, use_container_width=True)
