import streamlit as st
import pandas as pd
import requests
from pyathena import connect

st.set_page_config(page_title="Vehicle Sales Dashboard", layout="wide")

API_URL = "https://2m33d7cna7.execute-api.eu-central-1.amazonaws.com/predict"
tab_analytics, tab_prediction = st.tabs(["Market Analysis", "Vehicle Valuation"])

body_clean = ['Access Cab', 'Beetle Convertible', 'Cab Plus', 'Cab Plus 4',
       'Club Cab', 'Convertible', 'Coupe', 'Crew Cab', 'Crewmax Cab',
       'Cts Coupe', 'Cts Wagon', 'Cts-V Coupe', 'Cts-V Wagon',
       'Double Cab', 'E-Series Van', 'Elantra Coupe', 'Extended Cab',
       'G Convertible', 'G Coupe', 'G Sedan', 'G37 Convertible',
       'G37 Coupe', 'Genesis Coupe', 'Granturismo Convertible',
       'Hatchback', 'King Cab', 'Koup', 'Mega Cab', 'Minivan', 'Nan',
       'Navitgation', 'Promaster Cargo Van', 'Q60 Convertible',
       'Q60 Coupe', 'Quad Cab', 'Ram Van', 'Regular Cab', 'Regular-Cab',
       'Sedan', 'Supercab', 'Supercrew', 'Suv', 'Transit Van',
       'Tsx Sport Wagon', 'Van', 'Wagon', 'Xtracab']

state_usa = ['al','ak','az','ar','ct','sd','nd','de','fl','ga','hi','id','il','in',
             'ia','ca','ks','sc','nc','ky','co','la','me','md','ma','mi','mn','ms',
             'mo','mt','ne','nv','nh','nj','ny','nm','oh','ok','or','pa','ri','tx',
             'tn','ut','vt','wa','va','wv','wi','wy']

with tab_analytics:
    # Smart Buffer option
    # Page settings
    # Connection function (uses local AWS Credentials)
    def run_query(query):
        # Try to get credentials from Streamlit Secrets (Cloud),
        # otherwise fallback to local credentials (Local)
        try:
            aws_id = st.secrets["aws"]["aws_access_key_id"]
            aws_key = st.secrets["aws"]["aws_secret_access_key"]
            region = st.secrets["aws"]["region_name"]
            s3_staging = st.secrets["aws"]["s3_staging_dir"]
        except:
            # If secrets don't exist, pyathena will use local ~/.aws/credentials
            aws_id, aws_key, region = None, None, "eu-central-1"

        conn = connect(
            s3_staging_dir=s3_staging,
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
        query = """
            SELECT DISTINCT make
            FROM vehicle_sales_parquet
            WHERE make IS NOT NULL AND make != 'Nan'
            ORDER BY make
        """
        return run_query(query)['make'].tolist()

    all_makes = get_makes()
    selected_make = st.sidebar.selectbox("Select vehicle brand", all_makes)

    # Function retrieving all data of specific brand
    @st.cache_data
    def get_data_for_brand(make):
        query = f"""
            SELECT release_year, sellingprice, odometer, condition, state, model
            FROM vehicle_sales_parquet
            WHERE make = '{make}'
        """
        return run_query(query)

    # ---APPLICATION LOGIC---

    # Retrieve data for the brand (once per brand change in the select box)
    df_brand_pool = get_data_for_brand(selected_make)

    # Extract unique years directly from the already retrieved DataFrame
    available_years = sorted(df_brand_pool['release_year'].unique().tolist(), reverse=True)
    # Check if there is more than one year to avoid RangeError
    if len(available_years) > 1:
        selected_year = st.sidebar.select_slider("Select the year", options=available_years)
    else:
        # If only one year exists, just select it and show info
        selected_year = available_years[0]
        st.sidebar.info(f"Only model year {selected_year} available for {selected_make}")

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

    pass

with tab_prediction:
    st.header("Smart Price Calculator")
    st.write("Enter your vehicle details to receive an accurate AI-powered quote.")

    with st.form("prediction_form"):
        col1, col2 = st.columns(2)

        with col1:
            # Using brands from Athena
            make = st.selectbox("Marka", all_makes)
            model = st.text_input("Model (e.g. Fusion, Escape)", "Fusion")
            year = st.number_input("Manufacture year", min_value=1990, max_value=2025, value=2014)
            body = st.selectbox("Body style (Nan - no information available)", body_clean)

        with col2:
            odometer = st.number_input("Mileage (miles)", min_value=0, value=50000)
            condition = st.slider("Technical condition (1-49)", 1, 49, 20, step=1)
            state = st.selectbox("USA State (code, e.g. ca, tx, fl)", state_usa)

        submit_button = st.form_submit_button("Get a quote")

    if submit_button:
        # Preparing data for the API
        payload = {
            "car_data": {
                "year": year,
                "make": make,
                "model": model,
                "body": body,
                "state": state,
                "condition": condition,
                "odometer": odometer
            }
        }

        try:
            with st.spinner("Market data is currently being analyzed ..."):
                response = requests.post(API_URL, json=payload)
                result = response.json()

            if response.status_code == 200:
                # In the HTTP API, `result` the response (e.g., {'predicted_price': ...})
                price = result.get('predicted_price')
                
                if price:
                    st.success(f"### Estimated market value: ${price:,.2f}")
                else:
                    st.write(result)

                st.info("Please note that this estimate is based on historical data and may differ from offers at dealerships.")
            else:
                st.error(f"API error ({response.status_code}): {result.get('error', 'Unknown error')}")
        except Exception as e:
            st.error(f"Unable to connect to the pricing server: {e}")

