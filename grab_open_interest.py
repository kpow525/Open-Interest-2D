import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans

# Function to fetch open interest data
def fetch_open_interest(ticker, expiry):
    stock = yf.Ticker(ticker)
    try:
        opt_chain = stock.option_chain(expiry)
        calls = opt_chain.calls[['strike', 'openInterest']].dropna()
        puts = opt_chain.puts[['strike', 'openInterest']].dropna()
        return calls, puts
    except Exception as e:
        messagebox.showerror("Error", f"Error fetching data: {e}")
        return None, None

# Function to fetch the latest price at the fastest interval
def get_current_price(ticker):
    stock = yf.Ticker(ticker)
    try:
        latest_data = stock.history(period="1d", interval="1m")  # Fetch 1-minute interval data
        return latest_data['Close'].iloc[-1]  # Get latest closing price
    except Exception as e:
        messagebox.showerror("Error", f"Error fetching real-time price: {e}")
        return None

# Function to cluster strike prices based on open interest
def cluster_strikes(data, n_clusters=3):
    if data.empty:
        return data
    
    X = data[['strike']].values
    kmeans = KMeans(n_clusters=min(n_clusters, len(data)), random_state=42, n_init=10)
    data['cluster'] = kmeans.fit_predict(X)
    return data.sort_values(by='strike')

# Function to plot open interest with a dark theme
def plot_open_interest(ticker, expiry, calls, puts, current_price):
    plt.style.use("dark_background")
    sns.set_style("darkgrid", {"axes.facecolor": "black"})  # Dark Seaborn grid

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
    
    plt.show()

# Function to analyze and plot data
def analyze_support_resistance():
    ticker = ticker_entry.get().upper()
    expiry = expiry_var.get()
    
    if not ticker or not expiry:
        messagebox.showerror("Error", "Please enter a ticker and select an expiration date.")
        return
    
    calls, puts = fetch_open_interest(ticker, expiry)
    if calls is None or puts is None:
        return
    
    current_price = get_current_price(ticker)
    if current_price is None:
        return

    clustered_calls = cluster_strikes(calls, n_clusters=3)
    clustered_puts = cluster_strikes(puts, n_clusters=3)
    
    # --- Save open interest data to file ---
    import datetime
    today = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"{ticker} {today} Open Interest.csv"
    
    # Merge calls & puts into one DataFrame with type column
    calls_df = clustered_calls.copy()
    calls_df["type"] = "call"
    
    puts_df = clustered_puts.copy()
    puts_df["type"] = "put"
    
    combined_df = pd.concat([calls_df, puts_df], ignore_index=True)
    combined_df.to_csv(filename, index=False)
    
    messagebox.showinfo("Data Saved", f"Open Interest data saved as:\n{filename}")
    # ---------------------------------------

    plot_open_interest(ticker, expiry, clustered_calls, clustered_puts, current_price)

# Function to update expiration dates when the user enters a ticker
def update_expirations():
    ticker = ticker_entry.get().upper()
    if not ticker:
        return
    
    stock = yf.Ticker(ticker)
    expirations = stock.options
    
    expiry_menu["menu"].delete(0, "end")  # Clear existing options
    if expirations:
        for exp in expirations:
            expiry_menu["menu"].add_command(label=exp, command=tk._setit(expiry_var, exp))
        expiry_var.set(expirations[0])  # Select the first available expiration
    else:
        expiry_var.set("No options available")
        messagebox.showerror("Error", "No options data found for this ticker.")

# Create the main GUI window
root = tk.Tk()
root.title("Options Data Visualizer")
root.geometry("500x300")
root.configure(bg="#121212")  # Dark background

# Ticker Label & Entry
tk.Label(root, text="Enter Stock Ticker:", bg="#121212", fg="white", font=("Arial", 12)).pack(pady=5)
ticker_entry = tk.Entry(root, bg="#333333", fg="white", insertbackground="white", font=("Arial", 12))
ticker_entry.pack(pady=5)

# Fetch Expiration Button
fetch_button = tk.Button(root, text="Fetch Expirations", bg="#1F1F1F", fg="white", font=("Arial", 12), command=update_expirations)
fetch_button.pack(pady=5)

# Expiration Dropdown Menu
tk.Label(root, text="Select Expiration Date:", bg="#121212", fg="white", font=("Arial", 12)).pack(pady=5)
expiry_var = tk.StringVar(root)
expiry_menu = ttk.OptionMenu(root, expiry_var, "Select a ticker first")
expiry_menu.pack(pady=5)

# Analyze Button
analyze_button = tk.Button(root, text="Analyze", bg="#1F1F1F", fg="white", font=("Arial", 12), command=analyze_support_resistance)
analyze_button.pack(pady=20)

# Run the application
root.mainloop()
