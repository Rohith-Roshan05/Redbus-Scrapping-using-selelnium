import streamlit as st
import pandas as pd
import mysql.connector
import time

# Initialize session state variables
if 'show_feedback' not in st.session_state:
    st.session_state.show_feedback = False
if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False

# Database Connection
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    port=3307,
    password="",
    database="red_bus_details"  # Your database name
)
mycursor = mydb.cursor(buffered=True)

# Streamlit App Title
st.title('REDBUS FILTERING APP 🚌')
st.snow()

# Sidebar for Filtering Options
with st.sidebar:
    st.title("Search Your Bus")
    
    # Predefined States for Selection
    states = [
        "Andhra Pradesh", "Telangana", "Kerala", "Karnataka", 
        "Goa", "Bihar", "Uttar Pradesh", "Haryana", 
        "Punjab", "West Bengal"
    ]
    
    # State Selection Box
    selected_state = st.selectbox("Select State", states)
    
    # Star Rating Slider
    star_rating = st.select_slider("Pick the Expected Bus Rating", [1, 2, 3, 4, 5])
    
    # Price Range Slider
    min_price, max_price = st.slider(
        "Select Price Range",
        min_value=100, max_value=5000, value=(100, 5000), step=50
    )
    
    # Fetch bus types dynamically from the database
    mycursor.execute("SELECT DISTINCT bus_type FROM bus_details")
    bus_types = [row[0] for row in mycursor.fetchall()]
    
    # Bus Type Select Box (dynamically populated)
    selected_bus_type = st.selectbox("Select Bus Type", bus_types)
    
    # Search Button
    submit_button = st.button("Search 🔎")

# Query and Fetch Data Based on Filters
if submit_button:
    with st.spinner("Please wait Searching your bus...."):
        # Simulate a delay (e.g., data fetching or processing)
        time.sleep(2)
        
        # SQL Query to Filter Data Based on Selected State, Star Rating, Price Range, and Bus Type
        query = """
        SELECT * 
        FROM bus_details
        WHERE bus_route_name LIKE %s 
        AND star_rating >= %s 
        AND price BETWEEN %s AND %s 
        AND bus_type LIKE %s
        """
        state_filter = f"%{selected_state}%"  # To match any route containing the state name
        bus_type_filter = f"%{selected_bus_type}%"  # To match the selected bus type
        mycursor.execute(query, (state_filter, star_rating, min_price, max_price, bus_type_filter))
        result = mycursor.fetchall()
        
        # Column Names from the Database Table
        columns = ["ID", "bus_route_name", "bus_route_link", "bus_name",
                   "bus_type", "departing_time", "duration", "reaching_time",
                   "star_rating", "price", "seat_availability"]
        
        # Display Results
        if result:
            df = pd.DataFrame(result, columns=columns)
            st.dataframe(df)
            st.success(f"✅ Found {len(df)} buses matching your criteria.")
            
            # Set search performed to True
            st.session_state.search_performed = True
            st.session_state.show_feedback = False

# Feedback Section
if st.session_state.search_performed:
    
    
    # Feedback Button
    if st.button("Give Feedback"):
        st.session_state.show_feedback = True

# Detailed Feedback Form
if st.session_state.show_feedback:
    st.header("Feedback Form")
    
    # Star Rating for Bus Experience
    feedback_rating = st.feedback("stars")
    
    # Feedback Text Area
    feedback_text = st.text_area("Share Your Detailed Feedback")
    
    # Submit Feedback Button
    if st.button("Submit Feedback Details"):
        if feedback_text.strip():
            # Here you can add logic to save feedback to database
            st.success("Thank you for your feedback! Your input helps us improve.")
            
            # Reset states
            st.session_state.show_feedback = False
            st.session_state.search_performed = False
        else:
            st.warning("Please provide some feedback before submitting.")

# Close the Database Connection
mycursor.close()
mydb.close()