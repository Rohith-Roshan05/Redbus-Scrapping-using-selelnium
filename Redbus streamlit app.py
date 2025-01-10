import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            port=3307,
            password="",
            database="red_bus_details"
        )
        return connection
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

STATES = [
    "Andhra Pradesh", "Kerala", "Himachal Pradesh", "Punjab", "Bihar", 
    "Goa", "Telagana", "Rajasthan", "South Bengal", "Uttar pradesh"
]

def get_routes_for_state(connection, selected_state):
    query = """
    SELECT DISTINCT bus_route_name 
    FROM all_bus_details 
    WHERE bus_route_name LIKE %s 
    ORDER BY bus_route_name
    """
    param = f"%{selected_state}%"
    df = pd.read_sql_query(query, connection, params=[param])
    return df['bus_route_name'].tolist()

def fetch_filtered_data(connection, filters):
    base_query = "SELECT * FROM all_bus_details WHERE 1=1"
    params = []
    
    if filters.get('bus_route_name'):
        base_query += " AND bus_route_name = %s"
        params.append(filters['bus_route_name'])
    
    if filters.get('state'):
        base_query += " AND bus_route_name LIKE %s"
        params.append(f"%{filters['state']}%")
    
    if filters.get('bus_type'):
        base_query += " AND bus_type = %s"
        params.append(filters['bus_type'])
        
    if filters.get('departing_time'):
        base_query += " AND departing_time >= %s"
        params.append(filters['departing_time'])
        
    if filters.get('min_price'):
        base_query += " AND price >= %s"
        params.append(filters['min_price'])
        
    if filters.get('max_price'):
        base_query += " AND price <= %s"
        params.append(filters['max_price'])
        
    if filters.get('min_rating'):
        base_query += " AND star_rating >= %s"
        params.append(filters['min_rating'])
        
    if filters.get('seat_availability'):
        base_query += " AND seat_availability >= %s"
        params.append(filters['seat_availability'])

    return pd.read_sql_query(base_query, connection, params=params)

def main():
    if 'search_clicked' not in st.session_state:
        st.session_state.search_clicked = False
        
    st.markdown(
        """
        <style>
        .main-title {
            text-align: center;
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 30px;
        }
        .section-title {
            text-align: center;
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="main-title">Bus Filtering App 🚌</div>', unsafe_allow_html=True)
    
    connection = connect_to_database()
    
    if connection is None:
        st.error("Failed to connect to database. Please check your connection settings.")
        return

    st.sidebar.header("Search Filters")
    selected_state = st.sidebar.selectbox("Select State", options=["All States"] + STATES)
    
    if selected_state != "All States":
        state_routes = get_routes_for_state(connection, selected_state)
        route_options = ["All Routes"] + state_routes
    else:
        routes_df = pd.read_sql_query("SELECT DISTINCT bus_route_name FROM all_bus_details", connection)
        route_options = ["All Routes"] + routes_df['bus_route_name'].tolist()
    
    route_filter = st.sidebar.selectbox("Select Route", options=route_options)
    bus_types_df = pd.read_sql_query("SELECT DISTINCT bus_type FROM all_bus_details", connection)
    bus_type_filter = st.sidebar.selectbox("Select Bus Type", options=["All"] + bus_types_df['bus_type'].tolist())
    departure_time = st.sidebar.time_input("Departure Time After")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_price = st.number_input("Min Price", min_value=0, value=0)
    with col2:
        max_price = st.number_input("Max Price", min_value=0, value=10000)
    
    min_rating = st.sidebar.slider("Minimum Star Rating", 0.0, 5.0, 0.0, 0.5)
    min_seats = st.sidebar.number_input("Minimum Available Seats", min_value=0, value=1)
    
    if st.sidebar.button("🔍 Search Buses", type="primary", use_container_width=True):
        st.session_state.search_clicked = True
        st.empty()
    
    if not st.session_state.search_clicked:
        st.snow()
        welcome_container = st.container()
        with welcome_container:
            st.image(
                "https://cdn.dribbble.com/users/467332/screenshots/2970496/media/e4ae0dc0fba85df2de35fad88a2c5021.png",
                caption="Welcome to Bus Booking System",
                use_container_width=True
            )
    
    if st.session_state.search_clicked:
        filters = {}
        if selected_state != "All States":
            filters['state'] = selected_state
        if route_filter != "All Routes":
            filters['bus_route_name'] = route_filter
        if bus_type_filter != "All":
            filters['bus_type'] = bus_type_filter
        if departure_time:
            filters['departing_time'] = departure_time.strftime("%H:%M:%S")
        if min_price > 0:
            filters['min_price'] = min_price
        if max_price < 10000:
            filters['max_price'] = max_price
        if min_rating > 0:
            filters['min_rating'] = min_rating
        if min_seats > 0:
            filters['seat_availability'] = min_seats

        df = fetch_filtered_data(connection, filters)
        
        if selected_state != "All States":
            st.markdown(f'<div class="section-title">Available Buses - {selected_state}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="section-title">Available Buses - All States</div>', unsafe_allow_html=True)
            
        if len(df) > 0:
            df['price'] = df['price'].apply(lambda x: f"₹{x:,.2f}")
            df['star_rating'] = df['star_rating'].apply(lambda x: f"⭐ {x:.1f}")
            df['bus_route_link'] = df['bus_route_link'].apply(
                lambda x: f'<a href="{x}" target="_blank" style="text-decoration: none; background-color: #FF4B4B; color: white; padding: 5px 10px; border-radius: 5px;">Book Now</a>' if pd.notna(x) else "N/A"
            )
            
            columns_order = [
                'bus_route_name', 'bus_name', 'bus_type', 
                'departing_time', 'duration', 'reaching_time',
                'star_rating', 'price', 'seat_availability', 'bus_route_link'
            ]
            
            st.write(
                f"""
                <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 50px;">
                    {df[columns_order].to_html(escape=False, index=False)}
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                """
                <div style="text-align: center; margin-top: 50px; margin-bottom: 30px;">
                    <h1 style="font-size: 36px; font-weight: bold;">Quick Analytics</h1>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            with st.container():
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Available Buses", len(df))
                with col2:
                    avg_price = df['price'].str.replace("₹", "").str.replace(",", "").astype(float).mean()
                    st.metric("Average Price", f"₹{avg_price:,.2f}")
                with col3:
                    avg_rating = df['star_rating'].str.replace("⭐", "").astype(float).mean()
                    st.metric("Average Rating", f"⭐ {avg_rating:.1f}")
        else:
            st.info("No buses found matching your criteria.")

    connection.close()

if __name__ == "__main__":
    main()
