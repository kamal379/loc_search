import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import pandas as pd
import re
import json
from datetime import datetime
# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_fetch = st.secrets["gcp_service_account"]
# Convert dict to JSON string if a library expects a file
creds = json.dumps(creds_fetch)
#creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

sheet = client.open("LOC Details").worksheet("Sheet3")
data = sheet.get_all_records()
df = pd.DataFrame(data)


st.title("🔎 Advanced FIR Search Tool (Optional Filters)")

# --- Dynamic Column Substring Search ---
st.subheader("Column Substring Search")
search_conditions = []
add_more = True
i = 1
while add_more:
    col = st.selectbox(f"Select column {i}:", df.columns, key=f"col_{i}")
    term = st.text_input(f"Enter search string for column {i}:", key=f"term_{i}").strip().lower()
    if term:
        search_conditions.append((col, term))
    add_more = st.checkbox("Add another column search?", key=f"add_{i}")
    i += 1

# --- AND / OR logic toggle ---
logic_option = st.radio("Combine search conditions using:", ("AND", "OR"))

# --- FIR Date Filter (Optional) ---
st.subheader("FIR Date Filter (Optional)")
enable_fir_filter = st.checkbox("Enable FIR date filter")

if enable_fir_filter:
    date_filter_col = st.radio(
        "Select column to apply date filter:",
        ("FIR Details", "Confirmation No.")
    )
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")

# --- Regex for date formats ---
date_pattern = r"\b\d{2}[-/]\d{2}[-/]\d{4}\b"

def row_matches_dates(row_text, start, end):
    """Return True if any date in the text falls within start-end range."""
    row_text = str(row_text)
    dates_found = re.findall(date_pattern, row_text)
    for d in dates_found:
        try:
            if "-" in d:
                dt = datetime.strptime(d, "%d-%m-%Y").date()
            elif "/" in d:
                dt = datetime.strptime(d, "%d/%m/%Y").date()
            else:
                continue
            if start <= dt <= end:
                return True
        except:
            continue
    return False

# --- Apply filters ---
filtered_df = df.copy()

# Dynamic substring search with AND/OR
if search_conditions:
    if logic_option == "AND":
        for col, term in search_conditions:
            filtered_df = filtered_df[filtered_df[col].astype(str).str.lower().str.contains(term)]
    elif logic_option == "OR":
        mask = pd.Series(False, index=filtered_df.index)
        for col, term in search_conditions:
            mask = mask | filtered_df[col].astype(str).str.lower().str.contains(term)
        filtered_df = filtered_df[mask]

# Apply date filter only if enabled
if enable_fir_filter:
    # Map user choice to actual column name
    if date_filter_col == "FIR Details":
        col_name = "Details of Cases"  # replace with actual FIR text column
    else:
        col_name = "Confirmation No."  # replace with actual column name

    filtered_df = filtered_df[filtered_df[col_name].apply(lambda x: row_matches_dates(x, start_date, end_date))]

st.subheader("Filtered Results")
st.write(filtered_df)
