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

# Fixed list of states
STATES = [
    "Andhra Pradesh",
    "Kerala",
    "Himachal Pradesh",
    "Punjab",
    "Bihar",
    "Goa",
    "Telagana",
    "Rajasthan",
    "South Bengal",
    "Uttar pradesh"
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
        if isinstance(filters['bus_route_name'], list):
            placeholders = ','.join(['%s'] * len(filters['bus_route_name']))
            base_query += f" AND bus_route_name IN ({placeholders})"
            params.extend(filters['bus_route_name'])
        else:
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
    st.title("Bus Booking System")
    
    connection = connect_to_database()
    
    if connection is None:
        st.error("Failed to connect to database. Please check your connection settings.")
        return

    # Sidebar filters
    st.sidebar.header("Search Filters")
    
    # State filter using fixed list
    selected_state = st.sidebar.selectbox(
        "Select State",
        options=["All States"] + STATES
    )
    
    # Route filter based on selected state
    if selected_state != "All States":
        state_routes = get_routes_for_state(connection, selected_state)
        route_options = ["All Routes"] + state_routes
    else:
        # Get all routes if no state is selected
        routes_df = pd.read_sql_query("SELECT DISTINCT bus_route_name FROM all_bus_details", connection)
        route_options = ["All Routes"] + routes_df['bus_route_name'].tolist()
    
    route_filter = st.sidebar.selectbox(
        "Select Route",
        options=route_options
    )
    
    # Rest of the filters
    bus_types_df = pd.read_sql_query("SELECT DISTINCT bus_type FROM all_bus_details", connection)
    bus_type_filter = st.sidebar.selectbox(
        "Select Bus Type",
        options=["All"] + bus_types_df['bus_type'].tolist()
    )
    
    departure_time = st.sidebar.time_input("Departure Time After")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_price = st.number_input("Min Price", min_value=0, value=0)
    with col2:
        max_price = st.number_input("Max Price", min_value=0, value=10000)
    
    min_rating = st.sidebar.slider("Minimum Star Rating", 0.0, 5.0, 0.0, 0.5)
    
    min_seats = st.sidebar.number_input(
        "Minimum Available Seats",
        min_value=0,
        value=1
    )
    
    # Apply filters
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

    # Fetch and display data
    df = fetch_filtered_data(connection, filters)
    
    # Display results
    if selected_state != "All States":
        st.subheader(f"Available Buses - {selected_state}")
    else:
        st.subheader("Available Buses - All States")
        
    if len(df) > 0:
        columns_order = [
            'bus_route_name', 'bus_name', 'bus_type', 
            'departing_time', 'duration', 'reaching_time',
            'star_rating', 'price', 'seat_availability'
        ]
        
        df['price'] = df['price'].apply(lambda x: f"₹{x:,.2f}")
        df['star_rating'] = df['star_rating'].apply(lambda x: f"⭐ {x:.1f}")
        
        st.dataframe(
            df[columns_order],
            use_container_width=True,
            hide_index=True
        )

        # Analytics Section
    if len(df) > 0:
        st.subheader("Quick Analytics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Available Buses", len(df))
        with col2:
            avg_price = df['price'].str.replace('₹', '').str.replace(',', '').astype(float).mean()
            st.metric("Average Price", f"₹{avg_price:,.2f}")
        with col3:
            avg_rating = df['star_rating'].str.replace('⭐ ', '').astype(float).mean()
            st.metric("Average Rating", f"⭐ {avg_rating:.1f}")
        
        # Booking section
        st.subheader("Book a Bus")
        selected_bus = st.selectbox("Select Bus to Book", df['bus_name'].unique())
        
        col1, col2 = st.columns(2)
        with col1:
            num_seats = st.number_input("Number of Seats", min_value=1, max_value=10, value=1)
        with col2:
            passenger_name = st.text_input("Passenger Name")
            
        if st.button("Proceed to Book"):
            st.success(f"Booking initiated for {num_seats} seat(s) on {selected_bus} for {passenger_name}")
            
    else:
        st.info("No buses found matching your criteria.")
    
    
    
    connection.close()

if __name__ == "__main__":
    main()
