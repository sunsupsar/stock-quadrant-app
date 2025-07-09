import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Quadrant function
def get_quadrant(net_margin, pe_ratio):
    if net_margin < 10 and pe_ratio < 15:
        return "Q1: Low margin, Low multiple"
    elif net_margin < 10 and pe_ratio >= 15:
        return "Q2: Low margin, High multiple"
    elif net_margin >= 10 and pe_ratio < 15:
        return "Q3: High margin, Low multiple"
    else:
        return "Q4: High margin, High multiple"

# Streamlit app
st.set_page_config(page_title="Stock Quadrant Analyzer", layout="wide")
st.title("📊 Indian Stock Quadrant Analyzer")

# Option to upload data
uploaded_file = st.file_uploader("Upload CSV with 'Name', 'Net Margin', 'PE Ratio'", type=['csv'])

# Sample data if nothing uploaded
if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    st.info("Using sample data. Upload your CSV to analyze custom data.")
    sample_data = [
        {"Name": "TCS", "Net Margin": 21.5, "PE Ratio": 28},
        {"Name": "Zomato", "Net Margin": -2.4, "PE Ratio": 120},
        {"Name": "Coal India", "Net Margin": 25.3, "PE Ratio": 9},
        {"Name": "Paytm", "Net Margin": -8.2, "PE Ratio": 100},
        {"Name": "HDFC Bank", "Net Margin": 22.0, "PE Ratio": 16},
        {"Name": "Suzlon", "Net Margin": 6.0, "PE Ratio": 11},
    ]
    df = pd.DataFrame(sample_data)

# Apply quadrant logic
df["Quadrant"] = df.apply(lambda row: get_quadrant(row["Net Margin"], row["PE Ratio"]), axis=1)

# Show table
st.subheader("📋 Stock Classification")
st.dataframe(df, use_container_width=True)

# Scatter plot
st.subheader("📈 Quadrant Visualization")

fig, ax = plt.subplots(figsize=(10, 6))
colors = {'Q1': 'red', 'Q2': 'orange', 'Q3': 'green', 'Q4': 'blue'}

for i, row in df.iterrows():
    quad = row["Quadrant"].split(":")[0]
    ax.scatter(row["PE Ratio"], row["Net Margin"], 
               color=colors.get(quad, "black"), s=80)
    ax.text(row["PE Ratio"]+0.5, row["Net Margin"], row["Name"], fontsize=9)

# Quadrant lines
ax.axhline(y=10, color='gray', linestyle='--')
ax.axvline(x=15, color='gray', linestyle='--')

ax.set_xlabel("PE Ratio")
ax.set_ylabel("Net Margin (%)")
ax.set_title("Stock Quadrant Map")
st.pyplot(fig)
