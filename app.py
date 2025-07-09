import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
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
# Screener.in Data Fetcher
# ---------------------------
def get_financials(symbol):
    try:
        url = f"https://www.screener.in/company/{symbol}/consolidated/"
        st.text(f"🌐 Fetching URL: {url}")
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

        if response.status_code != 200:
            st.warning(f"⚠️ Could not fetch data for {symbol}. HTTP {response.status_code}")
            return {"Name": symbol, "PE Ratio": None, "Net Margin": None}

        soup = BeautifulSoup(response.text, "lxml")

        # --- 1. Extract PE Ratio
        pe_ratio = None
        for li in soup.select("ul.data-list li"):
            if "Stock P/E" in li.text:
                try:
                    pe_ratio = float(li.find("span").text.replace(",", ""))
                except:
                    st.warning(f"⚠️ Couldn't parse PE for {symbol}")

        # --- 2. Extract Net Margin = Net Profit / Sales (last year)
        net_margin = None
        try:
            for table in soup.find_all("table"):
                if "Profit & Loss" in table.text:
                    df = pd.read_html(str(table))[0]
                    df.columns = df.columns.fillna("Metric")
                    df.rename(columns={df.columns[0]: "Metric"}, inplace=True)
                    df.set_index("Metric", inplace=True)
                    sales = df.loc["Sales"].dropna().astype(float)
                    profit = df.loc["Net Profit"].dropna().astype(float)
                    if not sales.empty and not profit.empty:
                        net_margin = (profit.iloc[-1] / sales.iloc[-1]) * 100
                    break
        except Exception as e:
            st.warning(f"⚠️ Could not parse P&L table for {symbol}")
            st.code(traceback.format_exc())

        return {
            "Name": symbol,
            "PE Ratio": round(pe_ratio, 2) if pe_ratio else None,
            "Net Margin": round(net_margin, 2) if net_margin else None
        }

    except Exception as e:
        st.error(f"❌ Error fetching {symbol}: {e}")
        st.code(traceback.format_exc())
        return {"Name": symbol, "PE Ratio": None, "Net Margin": None}

# ---------------------------
# Streamlit App
# ---------------------------
st.set_page_config(page_title="Indian Stock Quadrant Analyzer", layout="wide")
st.title("📊 Indian Stock Quadrant Analyzer")

st.sidebar.subheader("🔎 Enter Stock Symbols (NSE)")
input_symbols = st.sidebar.text_area("Symbols (comma separated)", "TCS,HDFCBANK,INFY")
symbols = [s.strip().upper() for s in input_symbols.split(",") if s.strip()]

results = []
for sym in symbols:
    st.markdown(f"### 📅 Fetching data for: `{sym}`")
    data = get_financials(sym)
    st.json(data)
    data["Quadrant"] = get_quadrant(data["Net Margin"], data["PE Ratio"])
    st.markdown(f"🧭 Assigned Quadrant: **{data['Quadrant']}**")
    results.append(data)

# ---------------------------
# Show Data
# ---------------------------
df = pd.DataFrame(results)
st.subheader("📋 Stock Classification Table")
st.dataframe(df, use_container_width=True)

# ---------------------------
# Export to Excel
# ---------------------------
excel = BytesIO()
df.to_excel(excel, index=False)
excel.seek(0)
st.download_button("📥 Download Excel", excel, file_name="stock_quadrant_data.xlsx")

# ---------------------------
# Insight Summary
# ---------------------------
st.subheader("📌 Insight Summary")
summary = []
for _, row in df.iterrows():
    q = row['Quadrant']
    if "Q" in q:
        if 'Q4' in q:
            summary.append(f"- {row['Name']} is in {q}: Premium valued strong performer.")
        elif 'Q3' in q:
            summary.append(f"- {row['Name']} is in {q}: Potentially undervalued high performer.")
        elif 'Q2' in q:
            summary.append(f"- {row['Name']} is in {q}: Lower margin stock with higher valuation.")
        else:
            summary.append(f"- {row['Name']} is in {q}: Low margin & low valuation.")
if summary:
    st.markdown("\n".join(summary))
else:
    st.info("ℹ️ No insights yet — check if data was fetched properly.")

# ---------------------------
# Quadrant Chart
# ---------------------------
st.subheader("📈 Quadrant Visualization")
fig, ax = plt.subplots(figsize=(10, 6))
colors = {'Q1': 'red', 'Q2': 'orange', 'Q3': 'green', 'Q4': 'blue'}
for _, row in df.iterrows():
    q = row["Quadrant"]
    if "Q" in q:
        quad_code = q.split(":")[0]
        ax.scatter(row["PE Ratio"] or 0, row["Net Margin"] or 0, color=colors.get(quad_code, "gray"), s=80)
        ax.text((row["PE Ratio"] or 0) + 0.5, (row["Net Margin"] or 0), row["Name"], fontsize=9)
ax.axhline(10, color='gray', linestyle='--')
ax.axvline(15, color='gray', linestyle='--')
ax.set_xlabel("PE Ratio")
ax.set_ylabel("Net Margin (%)")
ax.set_title("Quadrant Map")
st.pyplot(fig)

# ---------------------------
# Filter Section
# ---------------------------
st.subheader("🔍 Filter Stocks")
min_margin = st.slider("Minimum Net Margin %", 0, 50, 10)
max_pe = st.slider("Maximum PE Ratio", 5, 100, 30)
filtered = df[(df["PE Ratio"] <= max_pe) & (df["Net Margin"].fillna(0) >= min_margin)]
st.dataframe(filtered, use_container_width=True)
