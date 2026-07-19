import streamlit as st
import pandas as pd
import requests
from pyathena import connect
import altair as alt

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

condition_bins = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 55]
condition_labels = ['1-5', '6-10', '11-15', '16-20', '21-25', '26-30', '31-35', '36-40', '41-45', '46-50']

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
        SELECT make, release_year, clean_avg_price
        FROM mart_brand_peer_comparison
        """
    return run_query(query)

df_brand_peers = get_brand_peer_data()

@st.cache_data
def get_data_for_brand(make):
    query = f"""
        SELECT car_age, sale_year, release_year, sellingprice, odometer, condition, state, color, car_model, body_type
        FROM stg_vehicle_sales
        WHERE make = '{make}'
    """
    return run_query(query)


# ==========================================
# TAB 1: SINGLE BRAND STORY
# ==========================================
with tab_analytics:
    st.title("Vehicle Market Storyteller")
    st.caption("Understand market trends, distributions, and positioning without the data noise.")
    st.markdown("---")

    st.subheader("🛠️ Configuration Filter")
    col_f1, col_f2 = st.columns([1, 2])
    
    with col_f1:
        selected_make = st.selectbox("Select primary brand", all_makes, key="primary_brand")
        df_brand_pool = get_data_for_brand(selected_make).copy()

    with col_f2:
        min_year = int(df_brand_pool['release_year'].min())
        max_year = int(df_brand_pool['release_year'].max())    
        if min_year < max_year:
            selected_year_range = st.slider(
                "Select Range of Manufacture Years",
                min_value=min_year,
                max_value=max_year,
                value=(min_year, max_year)
            )
        else:
            selected_year_range = (min_year, max_year)
            st.info(f"Data available only for year: {min_year}")

    df_final = df_brand_pool[
        (df_brand_pool['release_year'] >= selected_year_range[0]) & 
        (df_brand_pool['release_year'] <= selected_year_range[1])
    ].copy()

    st.markdown("---")

    col_met1, col_met2 = st.columns(2)
    total_offers = len(df_final)
    avg_price_selected = df_final['sellingprice'].mean() if total_offers > 0 else 0
    
    with col_met1:
        st.metric("Total Available Offers in Selection", f"{total_offers:,}")
    with col_met2:
        st.metric("Dynamic Average Price ($)", f"${avg_price_selected:,.2f}")
        
    st.markdown("---")

    st.subheader("🎯 Market Price Positioning (Dynamic Range & Trimmed Outliers)")
    st.markdown("How this brand ranks among 10 other brands with the closest average market value calculated **exactly for the selected range of years**.")
    
    if not df_brand_peers.empty:
        df_peers_filtered = df_brand_peers[
            (df_brand_peers['release_year'] >= selected_year_range[0]) & 
            (df_brand_peers['release_year'] <= selected_year_range[1])
        ]
        
        df_peers_dynamic = df_peers_filtered.groupby('make')['clean_avg_price'].mean().reset_index()
        
        if selected_make in df_peers_dynamic['make'].values:
            target_price = df_peers_dynamic[df_peers_dynamic['make'] == selected_make]['clean_avg_price'].values[0]
            
            df_peers_calc = df_peers_dynamic.copy()
            df_peers_calc['price_diff'] = df_peers_calc['clean_avg_price'] - target_price
            
            cheaper_peers = df_peers_calc[df_peers_calc['price_diff'] < 0].sort_values('price_diff', ascending=False).head(5)
            expensive_peers = df_peers_calc[df_peers_calc['price_diff'] > 0].sort_values('price_diff', ascending=True).head(5)
            current_brand = df_peers_calc[df_peers_calc['make'] == selected_make]
            
            peer_group = pd.concat([cheaper_peers, current_brand, expensive_peers]).sort_values('clean_avg_price')
            
            peer_group['Brand Group'] = peer_group['make'].apply(
                lambda m: f"Current Brand ({selected_make})" if m == selected_make else "Similar Budget Brands"
            )
            
            base_chart = alt.Chart(peer_group).encode(
                x=alt.X('make:N', sort='y', title='Brand'),
                y=alt.Y('clean_avg_price:Q', axis=None, title=None),
                color=alt.Color('Brand Group:N', scale=alt.Scale(domain=[f"Current Brand ({selected_make})", "Similar Budget Brands"], range=['#ff4b4b', '#1f77b4']))
            )
            
            bars = base_chart.mark_bar()
            text_labels = base_chart.mark_text(align='center', baseline='bottom', dy=-5).encode(
                text=alt.Text('clean_avg_price:Q', format='$,.0f')
            )
            
            st.altair_chart(bars + text_labels, width='stretch')
        else:
            st.info("No pricing data available for the selected range of years to generate rankings.")

    st.markdown("---")

    st.subheader("📊 Market Share & Structure Distributions")
    col_cond, col_state, col_color = st.columns(3)
    
    with col_cond:
        st.write("#### Technical Condition Share (%)")
        if not df_final.empty:
            df_final['condition_bin'] = pd.cut(df_final['condition'], bins=condition_bins, labels=condition_labels)
            cond_share = df_final['condition_bin'].value_counts(normalize=True).reset_index()
            cond_share.columns = ['Condition Range', 'Share (%)']
            cond_share['Share (%)'] *= 100
            
            chart_cond_single = alt.Chart(cond_share).mark_bar().encode(
                x=alt.X('Condition Range:N', sort=condition_labels),
                y=alt.Y('Share (%):Q')
            )
            st.altair_chart(chart_cond_single, width='stretch')
        else:
            st.write("No data")
            
    with col_state:
        st.write("#### Availability by USA State (%)")
        if not df_final.empty:
            state_share = df_final['state'].value_counts(normalize=True).head(10).reset_index()
            state_share.columns = ['State', 'Share (%)']
            state_share['Share (%)'] *= 100
            st.altair_chart(alt.Chart(state_share).mark_bar().encode(x='State:N', y='Share (%):Q'), width='stretch')
        else:
            st.write("No data")
            
    with col_color:
        st.write("#### Color Popularity Share (%)")
        if not df_final.empty:
            color_share = df_final['color'].value_counts(normalize=True).head(10).reset_index()
            color_share.columns = ['Color', 'Share (%)']
            color_share['Share (%)'] *= 100
            st.altair_chart(alt.Chart(color_share).mark_bar().encode(x='Color:N', y='Share (%):Q'), width='stretch')
        else:
            st.write("No data")

    st.markdown("---")

    st.subheader("📉 Price Depreciation & Supply Volume Profile")
    st.markdown("Historical overview of average asset value matched with absolute market volume per manufacture year.")
    
    if not df_brand_pool.empty:
        df_depreciation = df_brand_pool.groupby('release_year').agg(
            avg_price=('sellingprice', 'mean'),
            volume=('sellingprice', 'count')
        ).reset_index()
        
        base_deprec = alt.Chart(df_depreciation).encode(
            x=alt.X('release_year:Q', title='Manufacture Year', axis=alt.Axis(format='d'))
        )
        
        # Słupki reprezentujące wolumen (nałożone w tle z niską przezroczystością)
        volume_bars = base_deprec.mark_bar(opacity=0.15, color='#9467bd').encode(
            y=alt.Y('volume:Q', title='Volume (Number of Offers)')
        )
        
        # Linia ceny średniej
        price_line = base_deprec.mark_line(strokeWidth=3, color='#1f77b4').encode(
            y=alt.Y('avg_price:Q', title='Average Price ($)')
        )
        
        # Połączenie wykresów z niezależnymi osiami Y
        dual_axis_chart = alt.layer(volume_bars, price_line).resolve_scale(y='independent')
        st.altair_chart(dual_axis_chart, width='stretch')

# ==========================================
# TAB 2: COMPARE TWO BRANDS
# ==========================================
with tab_comparison:
    st.title("⚔️ Brand Side-by-Side Comparison")
    st.write("Compare structural properties, colors, body styles and value between two selected makers on integrated multi-layered charts.")
    st.markdown("---")
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        comp_make_1 = st.selectbox("Select Brand A", all_makes, index=all_makes.index(selected_make) if selected_make in all_makes else 0)
        df_comp1 = get_data_for_brand(comp_make_1).copy()
    with col_sel2:
        comp_make_2 = st.selectbox("Select Brand B", all_makes, index=min(1, len(all_makes)-1))
        df_comp2 = get_data_for_brand(comp_make_2).copy()

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(f"{comp_make_1} Total Volume", f"{len(df_comp1):,}")
        st.metric(f"{comp_make_1} Average Price", f"${df_comp1['sellingprice'].mean():,.2f}")
    with col_m2:
        st.metric(f"{comp_make_2} Total Volume", f"{len(df_comp2):,}")
        st.metric(f"{comp_make_2} Average Price", f"${df_comp2['sellingprice'].mean():,.2f}")

    st.markdown("---")
    
    st.write("### Integrated Condition Share Comparison (%)")
    df_comp1['condition_bin'] = pd.cut(df_comp1['condition'], bins=condition_bins, labels=condition_labels)
    df_comp2['condition_bin'] = pd.cut(df_comp2['condition'], bins=condition_bins, labels=condition_labels)
    
    c1 = df_comp1['condition_bin'].value_counts(normalize=True).reset_index()
    c1.columns = ['Condition Range', 'Share (%)']
    c1['Share (%)'] *= 100
    c1['Brand'] = comp_make_1
    
    c2 = df_comp2['condition_bin'].value_counts(normalize=True).reset_index()
    c2.columns = ['Condition Range', 'Share (%)']
    c2['Share (%)'] *= 100
    c2['Brand'] = comp_make_2
    
    df_cond_comp = pd.concat([c1, c2])
    
    chart_cond = alt.Chart(df_cond_comp).mark_bar(opacity=0.6).encode(
        x=alt.X('Condition Range:N', sort=condition_labels, title='Condition Range'),
        y=alt.Y('Share (%):Q', title='Share (%)', stack=None),
        color=alt.Color('Brand:N', scale=alt.Scale(range=['#1f77b4', '#ff7f0e']))
    )
    st.altair_chart(chart_cond, width='stretch')

    st.write("### Price Depreciation Timeline Comparison")
    dep1 = df_comp1.groupby('release_year')['sellingprice'].mean().reset_index()
    dep1['Brand'] = comp_make_1
    dep2 = df_comp2.groupby('release_year')['sellingprice'].mean().reset_index()
    dep2['Brand'] = comp_make_2
    df_dep_comp = pd.concat([dep1, dep2])
    
    chart_dep = alt.Chart(df_dep_comp).mark_line(strokeWidth=3, opacity=0.8).encode(
        x=alt.X('release_year:Q', title='Manufacture Year', axis=alt.Axis(format='d')),
        y=alt.Y('sellingprice:Q', title='Average Price ($)'),
        color=alt.Color('Brand:N', scale=alt.Scale(range=['#1f77b4', '#ff7f0e']))
    )
    st.altair_chart(chart_dep, width='stretch')

    st.markdown("---")
    col_chart_left, col_chart_right = st.columns(2)
    
    with col_chart_left:
        st.write("### Top 10 Color Popularity Comparison (%)")
        col1 = df_comp1['color'].value_counts(normalize=True).head(10).reset_index()
        col1.columns = ['Color', 'Share (%)']
        col1['Share (%)'] *= 100
        col1['Brand'] = comp_make_1
        
        col2 = df_comp2['color'].value_counts(normalize=True).head(10).reset_index()
        col2.columns = ['Color', 'Share (%)']
        col2['Share (%)'] *= 100
        col2['Brand'] = comp_make_2
        
        df_color_comp = pd.concat([col1, col2])
        
        chart_color = alt.Chart(df_color_comp).mark_bar(opacity=0.6).encode(
            x=alt.X('Color:N', title='Color', sort='-y'),
            y=alt.Y('Share (%):Q', title='Share (%)', stack=None),
            color=alt.Color('Brand:N', scale=alt.Scale(range=['#1f77b4', '#ff7f0e']))
        )
        st.altair_chart(chart_color, width='stretch')

    with col_chart_right:
        st.write("### Top 10 Body Style Comparison (%)")
        b1 = df_comp1['body_type'].value_counts(normalize=True).head(10).reset_index()
        b1.columns = ['Body Type', 'Share (%)']
        b1['Share (%)'] *= 100
        b1['Brand'] = comp_make_1
        
        b2 = df_comp2['body_type'].value_counts(normalize=True).head(10).reset_index()
        b2.columns = ['Body Type', 'Share (%)']
        b2['Share (%)'] *= 100
        b2['Brand'] = comp_make_2
        
        df_body_comp = pd.concat([b1, b2])
        
        chart_body = alt.Chart(df_body_comp).mark_bar(opacity=0.6).encode(
            x=alt.X('Body Type:N', title='Body Type', sort='-y'),
            y=alt.Y('Share (%):Q', title='Share (%)', stack=None),
            color=alt.Color('Brand:N', scale=alt.Scale(range=['#1f77b4', '#ff7f0e']))
        )
        st.altair_chart(chart_body, width='stretch')

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