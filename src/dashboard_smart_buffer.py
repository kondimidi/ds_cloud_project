import streamlit as st
import pandas as pd
from pyathena import connect
import os

# Smart Buffer option
# Page settings
st.set_page_config(page_title="Vehicle Sales Dashboard", layout="wide")

# Connection function (uses local AWS Credentials)
def run_query(query):
    # Try to get credentials from Streamlit Secrets (Cloud),
    # otherwise fallback to local credentials (Local)
    try:
        aws_id = st.secrets["aws"]["aws_access_key_id"]
        aws_key = st.secrets["aws"]["aws_secret_access_key"]
        region = st.secrets["aws"]["region_name"]
    except:
        # If secrets don't exist, pyathena will use local ~/.aws/credentials
        aws_id, aws_key, region = None, None, None

    conn = connect(
        s3_staging_dir='s3://konrad-ds-project-data/athena-results/',
        region_name=region,
        aws_access_key_id=aws_id,
        aws_secret_access_key=aws_key
    )
    return pd.read_sql(query, conn)

st.title("Vehicle Sales Analytics")
st.markdown("---")

# --- SIDEBAR: Filters ---
st.sidebar.header("Filters settings")

# Retrieve unique brands (Makes) from Parquet table
@st.cache_data
def get_makes():
    return run_query("SELECT DISTINCT make FROM vehicle_sales_parquet ORDER BY make")['make'].tolist()

all_makes = get_makes()
selected_make = st.sidebar.selectbox("Select vehicle brand", all_makes)

# Function retrieving all data of specific brand
@st.cache_data
def get_data_for_brand(make):
    query = f"SELECT release_year, sellingprice, odometer, condition, state, model FROM vehicle_sales_parquet WHERE make = '{make}'"
    return run_query(query)

# ---APPLICATION LOGIC---

# Retrieve data for the brand (once per brand change in the select box)
df_brand_pool = get_data_for_brand(selected_make)

# Extract unique years directly from the already retrieved DataFrame
available_years = sorted(df_brand_pool['release_year'].unique().tolist(), reverse=True)
selected_year = st.sidebar.select_slider("Select the year", options = available_years)

# LOCAL filtering (Pandas) – happens with every slider movement
df_final = df_brand_pool[df_brand_pool['release_year'] == selected_year]

# Creating Data Frame for selected filters
total_offers = len(df_final)
avg_price = df_final['sellingprice'].mean() if total_offers > 0 else 0
avg_mileage = df_final['odometer'].mean() if total_offers > 0 else 0

# Column layout for metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Number of offers", f"{total_offers:,}")
with col2:
    st.metric("Average price ($)", f"${avg_price:,.2f}")
with col3:
    st.metric("Average mileage", f"{avg_mileage:,.0f} mil")

st.subheader(f"Price analysis for the brand {selected_make} ({selected_year})")

# Select columns for the charts
df_charts = df_final[['condition', 'sellingprice', 'odometer', 'model']]

# Create two charts side by side
col_left, col_right = st.columns(2)

with col_left:
    st.write("### Price vs Condition of the Vehicle")
    avg_price_conidtion = df_charts.groupby('condition')['sellingprice'].mean().sort_index()
    st.bar_chart(avg_price_conidtion)

with col_right:
    st.write("Price vs Mileage")
    st.scatter_chart(data=df_charts, x='odometer', y='sellingprice', color='model')

st.markdown("---")
st.subheader("Geopgraphic Analysis (States)")

df_states = df_final.groupby('state').agg(
    count=('sellingprice', 'count'),
    avg_price=('sellingprice', 'mean')
).sort_values('count', ascending=False).reset_index()

col_map, col_table = st.columns([2, 1])

with col_map:
    st.bar_chart(data=df_states, x='state', y='count')

with col_table:
    st.dataframe(df_states, use_container_width=True, hide_index=True)

# --- ADVANCED INSIGHTS: Top 5 Deals ---
st.markdown("---")
st.subheader(f"Top 5 Best Values Deals for {selected_make} ({selected_year})")

# Sort by price ascending to find the cheapest ones
# Filter out rows with price 0 or extremly low to avoid data errors
top_deals = df_final[df_final['sellingprice'] > 500].sort_values('sellingprice', ascending=True).head(5)

if not top_deals.empty:
    # Formatting the price column for better readability in the table
    # Creating a copy to avoid SettingWithCopyWarning
    display_deals = top_deals[['model', 'condition', 'odometer', 'state', 'sellingprice']].copy()
    display_deals['sellingprice'] = display_deals['sellingprice'].map("${:,.2f}".format)
    display_deals['odometer'] = display_deals['odometer'].map("{:,.0f} mi".format)

    st.table(display_deals)
else:
    st.write("No deals found for the current selection.")
