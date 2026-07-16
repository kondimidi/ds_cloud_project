import streamlit as st
import pandas as pd
import requests
from pyathena import connect

st.set_page_config(page_title="Vehicle Market Storyteller", layout="wide")

API_URL = "https://2m33d7cna7.execute-api.eu-central-1.amazonaws.com/predict"
tab_analytics, tab_comparison, tab_prediction = st.tabs([
    "📈 Single Brand Story", 
    "⚔️ Compare Two Brands", 
    "🤖 Vehicle Valuation Calculator"
])

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

def run_query(query):
    try:
        aws_id = st.secrets["aws"]["aws_access_key_id"]
        aws_key = st.secrets["aws"]["aws_secret_access_key"]
        region = st.secrets["aws"]["region_name"]
        s3_staging = st.secrets["aws"]["s3_staging_dir"]
    except:
        aws_id, aws_key, region, = None, None, "eu-central-1"

    conn = connect(
    s3_staging_dir=s3_staging,
    region_name=region,
    aws_access_key_id=aws_id,
    aws_secret_access_key=aws_key
    )
    return pd.read_sql(query, conn)

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

@st.cache_data
def get_brand_peer_data():
    query = """
        SELECT make, clean_avg_price
        FROM mart_brand_peer_comparison
        """
    return run_query(query)

df_brand_peers = get_brand_peer_data()


# ==========================================
# TAB 1: SINGLE BRAND STORY
# ==========================================
with tab_analytics:
    st.title("Vehicle Market Storyteller")
    st.caption("Understand market trends, distributions, and positioning without the data noise.")
    st.markdown("---")

    selected_make = st.sidebar.selectbox("Select primary brand", all_makes, key="primary_brand")

    @st.cache_data
    def get_data_for_brand(make):
        query = f"""
            SELECT production_year, sale_year, sellingprice, odometer, condition, state, color, car_model
            FROM stg_vehicle_sales
            WHERE make = '{make}'
        """
        return run_query(query)

    df_brand_pool = get_data_for_brand(selected_make)

    min_year = int(df_brand_pool['sale_year'].min())
    max_year = int(df_brand_pool['sale_year'].max())    

    if min_year < max_year:
        selected_year_range = st.sidebar.slider(
            "Select Range of Sale Years",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year)
        )
    else:
        selected_year_range = (min_year, max_year)
        st.sidebar.info(f"Data available only for year: {min_year}")

    df_final = df_brand_pool[
        (df_brand_pool['sale_year'] >= selected_year_range[0]) & 
        (df_brand_pool['sale_year'] <= selected_year_range[1])
    ]

    # General size metric
    total_offers = len(df_final)
    st.metric("Total Available Offers in Selection", f"{total_offers:,}")
    st.markdown("---")

    # 10 neighbours
    st.subheader("🎯 Market Price Positioning (Trimmed Outliers)")
    st.markdown("How this brand ranks among 10 other brands with the closest average market value.")
    
    if selected_make in df_brand_peers['make'].values:
        target_price = df_brand_peers[df_brand_peers['make'] == selected_make]['clean_avg_price'].values[0]
        
        df_peers_calc = df_brand_peers.copy()
        df_peers_calc['price_diff'] = df_peers_calc['clean_avg_price'] - target_price
        
        cheaper_peers = df_peers_calc[df_peers_calc['price_diff'] < 0].sort_values('price_diff', ascending=False).head(5)
        expensive_peers = df_peers_calc[df_peers_calc['price_diff'] > 0].sort_values('price_diff', ascending=True).head(5)
        current_brand = df_peers_calc[df_peers_calc['make'] == selected_make]
        
        peer_group = pd.concat([cheaper_peers, current_brand, expensive_peers]).sort_values('clean_avg_price')
        
        st.bar_chart(data=peer_group, x='make', y='clean_avg_price', color=['#ff4b4b' if m == selected_make else '#1f77b4' for m in peer_group['make']])
    else:
        st.info("Insufficient baseline pricing data for peer ranking.")

    st.markdown("---")

    # Percentage share
    st.subheader("📊 Market Share & Structure Distributions")
    st.markdown("Proportional insights into car structural properties (Condition, Location, and Colors).")
    
    col_cond, col_state, col_color = st.columns(3)
    
    with col_cond:
        st.write("#### Technical Condition Share (%)")
        if not df_final.empty:
            cond_share = df_final['condition'].value_counts(normalize=True).sort_index() * 100
            st.bar_chart(cond_share)
        else:
            st.write("No data")
            
    with col_state:
        st.write("#### Availability by USA State (%)")
        if not df_final.empty:
            state_share = df_final['state'].value_counts(normalize=True).head(10) * 100
            st.bar_chart(state_share)
        else:
            st.write("No data")
            
    with col_color:
        st.write("#### Color Popularity Share (%)")
        if not df_final.empty:
            color_share = df_final['color'].value_counts(normalize=True).head(10) * 100
            st.bar_chart(color_share)
        else:
            st.write("No data")

    st.markdown("---")

    # Full depreciation history (Independent of the sales year filter)
    st.subheader("📉 Price Depreciation Profile over Manufacture Years")
    st.markdown("Historical overview of asset value relative to its original production year (Unfiltered by sale year range).")
    
    if not df_brand_pool.empty:
        df_depreciation = df_brand_pool.groupby('production_year')['sellingprice'].mean().reset_index()
        st.line_chart(data=df_depreciation, x='production_year', y='sellingprice')


# ==========================================
# TAB 2: COMPARE TWO BRANDS
# ==========================================
with tab_comparison:
    st.title("⚔️ Brand Side-by-Side Comparison")
    st.write("Compare structural properties and value between two selected makers.")
    st.markdown("---")
    
    col_b1, col_b2 = st.columns(2)
    
    with col_b1:
        comp_make_1 = st.selectbox("Select Brand A", all_makes, index=all_makes.index(selected_make) if selected_make in all_makes else 0)
        df_comp1 = get_data_for_brand(comp_make_1)
        st.metric(f"{comp_make_1} Total Volume", f"{len(df_comp1):,}")
        st.write("##### Condition Share (%)")
        st.bar_chart(df_comp1['condition'].value_counts(normalize=True).sort_index() * 100)
        st.write("##### Price Depreciation Timeline")
        st.line_chart(data=df_comp1.groupby('production_year')['sellingprice'].mean().reset_index(), x='production_year', y='sellingprice')

    with col_b2:
        # Domyślnie ustawiamy drugą markę na inną pozycję
        comp_make_2 = st.selectbox("Select Brand B", all_makes, index=min(1, len(all_makes)-1))
        df_comp2 = get_data_for_brand(comp_make_2)
        st.metric(f"{comp_make_2} Total Volume", f"{len(df_comp2):,}")
        st.write("##### Condition Share (%)")
        st.bar_chart(df_comp2['condition'].value_counts(normalize=True).sort_index() * 100)
        st.write("##### Price Depreciation Timeline")
        st.line_chart(data=df_comp2.groupby('production_year')['sellingprice'].mean().reset_index(), x='production_year', y='sellingprice')


# ==========================================
# TAB 3: VEHICLE VALUATION CALCULATOR
# ==========================================
with tab_prediction:
    st.header("Smart Price Calculator")
    st.write("Enter your vehicle details to receive an accurate AI-powered quote.")

    with st.form("prediction_form"):
        col1, col2 = st.columns(2)

        with col1:
            make = st.selectbox("Brand", all_makes)
            model = st.text_input("Model (e.g. Fusion, Escape)", "Fusion")
            year = st.number_input("Manufacture year", min_value=1990, max_value=2026, value=2015)
            body = st.selectbox("Body style", body_clean)

        with col2:
            odometer = st.number_input("Mileage (miles)", min_value=0, value=50000)
            condition = st.slider("Technical condition (1-49)", 1, 49, 20, step=1)
            state = st.selectbox("USA State", state_usa)

        submit_button = st.form_submit_button("Get a quote")

    if submit_button:
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