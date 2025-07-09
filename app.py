import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt

# -------------------- UTILITY FUNCTIONS --------------------

def fetch_screener_data(symbol):
    url = f"https://www.screener.in/company/{symbol}/consolidated/"
    st.write(f"\n\U0001F310 Fetching URL: {url}")

    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            st.warning(f"Failed to fetch data for {symbol} (Status {response.status_code})")
            return None

        soup = BeautifulSoup(response.text, 'lxml')

        # Find all ratios
        ratios = soup.find_all("li", class_="flex flex-space-between")
        pe_ratio = None
        net_margin = None

        for r in ratios:
            label = r.find('span')
            value = r.find_all('span')[-1]
            if not label or not value:
                continue

            label_text = label.text.strip()
            value_text = value.text.strip().replace('%', '')

            if label_text == "P/E":
                pe_ratio = safe_float(value_text)
            elif label_text == "Net Profit Margin":
                net_margin = safe_float(value_text)

        if pe_ratio is None:
            st.warning(f"\u26A0\uFE0F Could not find PE label for {symbol}")
        if net_margin is None:
            st.warning(f"\u26A0\uFE0F Could not find Net Margin for {symbol}")

        return {
            "Name": symbol,
            "PE Ratio": pe_ratio,
            "Net Margin": net_margin,
        }

    except Exception as e:
        st.error(f"Error for {symbol}: {e}")
        return None

def safe_float(value):
    try:
        return float(value.replace(',', ''))
    except:
        return None

def classify_quadrant(pe, margin):
    if pe is None or margin is None:
        return "Not classified"
    if pe < 20 and margin > 20:
        return "Bargain Quality"
    elif pe >= 20 and margin > 20:
        return "Premium Quality"
    elif pe < 20 and margin <= 20:
        return "Undervalued Low Margin"
    else:
        return "Overpriced Low Margin"

# -------------------- STREAMLIT UI --------------------

def main():
    st.title("\U0001F4CA Indian Stock Quadrant Analyzer (Screener.in)")
    user_input = st.text_input("Enter stock symbols (comma-separated):", "TCS,INFY,HDFCBANK")

    if not user_input:
        return

    stock_symbols = [s.strip().upper() for s in user_input.split(",") if s.strip()]
    all_data = []

    for symbol in stock_symbols:
        st.write(f"\n\U0001F4C5 Fetching data for: {symbol}")
        data = fetch_screener_data(symbol)

        if data:
            data['Quadrant'] = classify_quadrant(data['PE Ratio'], data['Net Margin'])
            st.json(data)
            all_data.append(data)

    if all_data:
        df = pd.DataFrame(all_data)
        st.subheader("\U0001F4CB Stock Classification Table")
        st.dataframe(df)

        # Optional: quadrant plot
        st.subheader("\U0001F3A8 Quadrant Plot")
        fig, ax = plt.subplots()
        for i, row in df.iterrows():
            if pd.notna(row['PE Ratio']) and pd.notna(row['Net Margin']):
                ax.scatter(row['PE Ratio'], row['Net Margin'], label=row['Name'])
                ax.annotate(row['Name'], (row['PE Ratio'], row['Net Margin']))
        ax.axhline(20, color='gray', linestyle='--')
        ax.axvline(20, color='gray', linestyle='--')
        ax.set_xlabel("PE Ratio")
        ax.set_ylabel("Net Margin (%)")
        ax.set_title("Stock Classification by PE and Margin")
        st.pyplot(fig)

if __name__ == "__main__":
    main()
