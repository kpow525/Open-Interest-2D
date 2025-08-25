import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
import streamlit as st
import datetime

# ---------------- Functions ---------------- #

def fetch_open_interest(ticker, expiry):
    stock = yf.Ticker(ticker)
    try:
        opt_chain = stock.option_chain(expiry)
        calls = opt_chain.calls[['strike', 'openInterest']].dropna()
        puts = opt_chain.puts[['strike', 'openInterest']].dropna()
        return calls, puts
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None, None

def get_current_price(ticker):
    stock = yf.Ticker(ticker)
    try:
        latest_data = stock.history(period="1d", interval="1m")
        return latest_data['Close'].iloc[-1]
    except Exception as e:
        st.error(f"Error fetching real-time price: {e}")
        return None

def cluster_strikes(data, n_clusters=3):
    if data.empty:
        return data
    X = data[['strike']].values
    kmeans = KMeans(n_clusters=min(n_clusters, len(data)), random_state=42, n_init=10)
    data['cluster'] = kmeans.fit_predict(X)
    return data.sort_values(by='strike')

def plot_open_interest(ticker, expiry, calls, puts, current_price):
    plt.style.use("dark_background")
    sns.set_style("darkgrid", {"axes.facecolor": "black"})

    plt.figure(figsize=(10, 6))

    cool_colors = sns.color_palette("cool", n_colors=len(calls['cluster'].unique()))
    warm_colors = sns.color_palette("autumn", n_colors=len(puts['cluster'].unique()))

    for i, color in enumerate(cool_colors):
        clustered_calls = calls[calls['cluster'] == i]
        plt.scatter(clustered_calls['strike'], clustered_calls['openInterest'],
                    color=color, alpha=0.8, s=80, label=f"Call Cluster {i+1}")

    for i, color in enumerate(warm_colors):
        clustered_puts = puts[puts['cluster'] == i]
        plt.scatter(clustered_puts['strike'], clustered_puts['openInterest'],
                    color=color, alpha=0.8, s=80, label=f"Put Cluster {i+1}")

    plt.axvline(x=current_price, color='white', linestyle='dashed', linewidth=1.5, label="Current Price")

    plt.xlabel("Strike Price", color="white")
    plt.ylabel("Open Interest", color="white")
    plt.title(f"Clustered Open Interest for {ticker} (Exp: {expiry})", color="white")
    plt.legend()
    plt.grid(True, linestyle="dotted", color="gray")

    st.pyplot(plt)

# ---------------- Streamlit UI ---------------- #

st.set_page_config(page_title="Options Data Visualizer", layout="centered", page_icon="📊")

st.title("📊 Options Data Visualizer")

ticker = st.text_input("Enter Stock Ticker (e.g. SPY, AAPL):").upper()

if ticker:
    stock = yf.Ticker(ticker)
    expirations = stock.options

    if expirations:
        expiry = st.selectbox("Select Expiration Date:", expirations)
        if st.button("Analyze"):
            calls, puts = fetch_open_interest(ticker, expiry)
            if calls is not None and puts is not None:
                current_price = get_current_price(ticker)
                if current_price:
                    clustered_calls = cluster_strikes(calls, n_clusters=3)
                    clustered_puts = cluster_strikes(puts, n_clusters=3)

                    # Merge calls & puts
                    calls_df = clustered_calls.copy()
                    calls_df["type"] = "call"
                    puts_df = clustered_puts.copy()
                    puts_df["type"] = "put"
                    combined_df = pd.concat([calls_df, puts_df], ignore_index=True)

                    # Save CSV
                    today = datetime.date.today().strftime("%Y-%m-%d")
                    filename = f"{ticker}_{today}_OpenInterest.csv"
                    csv = combined_df.to_csv(index=False).encode("utf-8")

                    st.success(f"Open Interest data ready for {ticker} (Exp: {expiry})")
                    st.download_button("Download Open Interest Data", csv, file_name=filename, mime="text/csv")

                    # Show plot
                    plot_open_interest(ticker, expiry, clustered_calls, clustered_puts, current_price)
    else:
        st.error("No options data found for this ticker.")