import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="Stock Quadrant App", layout="wide")

def get_financials(symbol):
    base_url = f"https://www.screener.in/company/{symbol}/consolidated/"
    st.write(f"📅 Fetching data for: {symbol}")
    st.write(f"🌐 Fetching URL: {base_url}")

    try:
        response = requests.get(base_url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            st.warning(f"❌ HTTP Error {response.status_code} for {symbol}")
            return None, None
        html = response.text
        return parse_pe_and_margin(html, symbol)
    except Exception as e:
        st.error(f"❌ Exception while fetching data for {symbol}: {e}")
        return None, None

def parse_pe_and_margin(html, symbol):
    soup = BeautifulSoup(html, 'lxml')

    pe_ratio = None
    net_margin = None

    try:
        # P/E Ratio
        ratios_block = soup.find("ul", class_="ranges")
        if ratios_block:
            for li in ratios_block.find_all("li"):
                label = li.find("span", class_="sub")
                if label and "P/E" in label.text:
                    value = li.get_text(strip=True).replace("P/E", "").strip()
                    pe_ratio = float(value)
                    break
        if pe_ratio is None:
            st.warning(f"⚠️ Could not find PE label for {symbol}")
    except Exception as e:
        st.warning(f"⚠️ PE parsing error for {symbol}: {e}")

    try:
        # Net Margin
        ratio_table = soup.find("section", id="ratio")
        if ratio_table:
            rows = ratio_table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if cols and "Net profit margin" in cols[0].text:
                    value = cols[1].text.replace("%", "").strip()
                    if value:
                        net_margin = float(value)
                    break
        if net_margin is None:
            st.warning(f"⚠️ Could not find Net Margin for {symbol}")
    except Exception as e:
        st.warning(f"⚠️ Net Margin parsing error for {symbol}: {e}")

    return pe_ratio, net_margin

def classify_stock(pe, margin):
    if pe is None or margin is None:
        return "Not classified"
    if pe < 20 and margin > 15:
        return "High Margin - Low PE"
    elif pe >= 20 and margin > 15:
        return "High Margin - High PE"
    elif pe < 20 and margin <= 15:
        return "Low Margin - Low PE"
    else:
        return "Low Margin - High PE"

def main():
    st.title("📊 Indian Stock Quadrant Classifier")

    symbols_input = st.text_input("Enter stock symbols (comma-separated):", "TCS,INFY,HDFCBANK")
    symbols = [sym.strip().upper() for sym in symbols_input.split(",")]

    results = []

    for symbol in symbols:
        pe, margin = get_financials(symbol)
        quadrant = classify_stock(pe, margin)

        stock_data = {
            "Name": symbol,
            "PE Ratio": pe,
            "Net Margin": margin,
            "Quadrant": quadrant
        }

        st.json(stock_data)
        results.append(stock_data)
        time.sleep(1.5)  # Avoid hammering Screener

    df = pd.DataFrame(results)

    st.subheader("📋 Stock Classification Table")
    st.dataframe(df)

    st.subheader("🧭 Quadrant Chart")

    fig, ax = plt.subplots()
    colors = {
        "High Margin - Low PE": "green",
        "High Margin - High PE": "blue",
        "Low Margin - Low PE": "orange",
        "Low Margin - High PE": "red",
        "Not classified": "gray"
    }

    for _, row in df.iterrows():
        if pd.notna(row["PE Ratio"]) and pd.notna(row["Net Margin"]):
            ax.scatter(row["PE Ratio"], row["Net Margin"],
                       color=colors.get(row["Quadrant"], "black"), label=row["Name"])
            ax.text(row["PE Ratio"], row["Net Margin"], row["Name"])

    ax.axhline(15, color='gray', linestyle='--', linewidth=1)
    ax.axvline(20, color='gray', linestyle='--', linewidth=1)
    ax.set_xlabel("P/E Ratio")
    ax.set_ylabel("Net Margin (%)")
    ax.set_title("Stock Quadrant Classification")
    st.pyplot(fig)

if __name__ == "__main__":
    main()
