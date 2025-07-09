import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt

# Updated Screener parser
def parse_pe_and_margin(html, symbol):
    soup = BeautifulSoup(html, 'lxml')

    pe_ratio = None
    net_margin = None

    try:
        # PE Ratio from summary cards
        for li in soup.select("ul.snapshot li"):
            span = li.find("span", string="P/E")
            if span:
                val = li.text.strip().split()[0].replace(",", "")
                pe_ratio = float(val)
                break
        if pe_ratio is None:
            st.warning(f"⚠️ Could not find PE label for {symbol}")
    except Exception as e:
        st.warning(f"⚠️ PE parsing error for {symbol}: {e}")

    try:
        # Net Margin from Ratios table
        tables = soup.find_all("table")
        for table in tables:
            if "Net profit margin" in table.text:
                for row in table.find_all("tr"):
                    cols = row.find_all("td")
                    if cols and "Net profit margin" in cols[0].text:
                        val = cols[1].text.strip().replace("%", "").replace(",", "")
                        net_margin = float(val)
                        break
        if net_margin is None:
            st.warning(f"⚠️ Could not find Net Margin for {symbol}")
    except Exception as e:
        st.warning(f"⚠️ Net Margin parsing error for {symbol}: {e}")

    return pe_ratio, net_margin

# Determine quadrant
def classify_stock(pe, margin):
    if pe is None or margin is None:
        return "Not classified"
    if pe < 25 and margin > 15:
        return "High Margin, Low PE"
    elif pe >= 25 and margin > 15:
        return "High Margin, High PE"
    elif pe < 25 and margin <= 15:
        return "Low Margin, Low PE"
    else:
        return "Low Margin, High PE"

# Fetch and parse data
def fetch_data(symbol):
    url = f"https://www.screener.in/company/{symbol}/consolidated/"
    st.write(f"📅 Fetching data for: {symbol}")
    st.write(f"🌐 Fetching URL: {url}")

    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            pe, margin = parse_pe_and_margin(response.text, symbol)
            return {
                "Name": symbol,
                "PE Ratio": pe,
                "Net Margin": margin,
                "Quadrant": classify_stock(pe, margin)
            }
        else:
            st.warning(f"⚠️ Failed to fetch data for {symbol}: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Error fetching data for {symbol}: {e}")

    return {
        "Name": symbol,
        "PE Ratio": None,
        "Net Margin": None,
        "Quadrant": "Not classified"
    }

# Streamlit UI
st.title("📊 Indian Stock Quadrant Analyzer (Screener.in)")

symbols_input = st.text_input("Enter stock symbols (comma-separated):", "TCS,INFY,HDFCBANK")
symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

if st.button("Analyze"):
    results = []
    for sym in symbols:
        data = fetch_data(sym)
        st.json(data)
        results.append(data)

    df = pd.DataFrame(results)

    st.subheader("📋 Stock Classification Table")
    st.dataframe(df)

    st.subheader("📈 Quadrant Plot")
    filtered = df.dropna(subset=["PE Ratio", "Net Margin"])
    if not filtered.empty:
        fig, ax = plt.subplots()
        for _, row in filtered.iterrows():
            ax.scatter(row["PE Ratio"], row["Net Margin"], label=row["Name"])
            ax.text(row["PE Ratio"], row["Net Margin"], row["Name"], fontsize=9)
        ax.axvline(x=25, color='red', linestyle='--', label="PE = 25")
        ax.axhline(y=15, color='blue', linestyle='--', label="Net Margin = 15%")
        ax.set_xlabel("PE Ratio")
        ax.set_ylabel("Net Margin (%)")
        ax.set_title("PE vs Net Margin Quadrant")
        ax.legend()
        st.pyplot(fig)
    else:
        st.info("No data available to plot.")

