import streamlit as st
import pandas as pd
from pyathena import connect
import os

# Cloud-Heavy option
# Page settings
st.set_page_config(page_title="Vehicle Sales Dashboard", layout="wide")

# Connection function (uses local AWS Credentials)
def run_query(query):
    conn = connect(
        s3_staging_dir='s3://konrad-ds-project-data/athena-results/',
        region_name='eu-central-1'
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

# Collect production years for the selected brand
@st.cache_data
def get_years(make):
    query = f"SELECT DISTINCT release_year FROM vehicle_sales_parquet WHERE make = '{make}' ORDER BY release_year DESC"
    return  run_query(query)['release_year'].tolist()

available_years = get_years(selected_make)
selected_year = st.sidebar.select_slider("Select the year", options = available_years)

# Downloading data for selected filters
query_main = f"""
    SELECT
        count(*) as total_offers,
        avg(sellingprice) as avg_price,
        avg(odometer) as avg_mileage
    FROM vehicle_sales_parquet
    WHERE make = '{selected_make}' AND release_year = {selected_year} 
"""

df_metrics = run_query(query_main)

# Column layout for metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Number of offers", df_metrics['total_offers'][0])
with col2:
    st.metric("Average price ($)", f"{df_metrics['avg_price'][0]:,.2f}")
with col3:
    st.metric("Average mileage", f"{df_metrics['avg_mileage'][0]:,.0f} mil")

st.subheader(f"Price analysis for the brand {selected_make} ({selected_year})")

# Download a broader set of data for the charts
query_charts = f"""
    SELECT condition, sellingprice, odometer, model
    FROM vehicle_sales_parquet
    WHERE make = '{selected_make}' AND release_year = {selected_year}
"""

@st.cache_data
def get_chart_data(query):
    return run_query(query)

df_charts = get_chart_data(query_charts)

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

query_states = f"""
    SELECT state, count(*) as count, avg(sellingprice) as avg_price
    FROM vehicle_sales_parquet
    WHERE make = '{selected_make}' AND release_year = {selected_year}
    GROUP BY state
    ORDER BY count DESC
"""

df_states = run_query(query_states)

col_map, col_table = st.columns([2, 1])

with col_map:
    st.bar_chart(data=df_states, x='state', y='count')

with col_table:
    st.dataframe(df_states, use_container_width=True, hide_index=True)