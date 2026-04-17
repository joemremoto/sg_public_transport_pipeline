"""
Singapore Public Transport Analytics Dashboard

A Streamlit dashboard for visualizing LTA public transport journey data.
Shows trip counts by origin location and time periods with interactive filters.
"""

import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from dotenv import load_dotenv

from utils.bigquery_client import (
    get_bigquery_client,
    get_available_months,
    get_origins,
    get_trip_count_by_origin,
    get_trip_count_by_time_period
)

# Load environment variables from current directory or parent
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try parent directory
    parent_env = Path(__file__).parent.parent / '.env'
    load_dotenv(parent_env)

# Page configuration
st.set_page_config(
    page_title="SG Transport Analytics",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .filter-section {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application function"""
    
    # Header
    st.markdown('<div class="main-header">🚇 Singapore Public Transport Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">LTA Origin-Destination Journey Data Visualization</div>', unsafe_allow_html=True)
    
    # Initialize BigQuery client
    try:
        client = get_bigquery_client()
    except Exception as e:
        st.error(f"Failed to connect to BigQuery: {e}")
        st.info("Please ensure GOOGLE_APPLICATION_CREDENTIALS is set correctly in your .env file")
        st.stop()
    
    # Sidebar - Filters
    st.sidebar.header("🎛️ Filters")
    
    # Mode selection
    mode = st.sidebar.radio(
        "Transport Mode",
        options=["Train", "Bus"],
        index=0,
        help="Select between train or bus journey data"
    )
    
    st.sidebar.markdown("---")
    
    # Get available months for selected mode
    available_months = get_available_months(client, mode)
    
    if not available_months:
        st.error(f"No data available for {mode} mode. Please check your BigQuery dataset.")
        st.stop()
    
    # Year-Month filter
    year_month = st.sidebar.selectbox(
        "Year-Month",
        options=available_months,
        index=0,
        format_func=lambda x: f"{x[:4]}-{x[4:]}",
        help="Select the month of data to analyze"
    )
    
    # Day type filter
    day_type = st.sidebar.selectbox(
        "Day Type",
        options=["WEEKDAY", "WEEKENDS/HOLIDAY"],
        index=0,
        help="Filter by weekdays or weekends/holidays"
    )
    
    st.sidebar.markdown("---")
    
    # Origin filter
    st.sidebar.subheader("Origin Filter")
    
    with st.spinner("Loading origins..."):
        origins_df = get_origins(client, mode, year_month, day_type)
    
    if origins_df.empty:
        st.error("No origin locations found for the selected filters.")
        st.stop()
    
    # Create origin options
    if mode == "Bus":
        origin_col = "origin_bus_stop_key"
    else:
        origin_col = "origin_station_key"
    
    # Multi-select for origins (optional filter)
    filter_origins = st.sidebar.checkbox(
        "Filter by specific origins",
        value=False,
        help="Enable to filter by specific stations/stops"
    )
    
    selected_origins = None
    if filter_origins:
        selected_origin_names = st.sidebar.multiselect(
            "Select Origins",
            options=origins_df['origin_name'].tolist(),
            default=None,
            help="Select one or more origins to filter"
        )
        
        if selected_origin_names:
            selected_origins = origins_df[
                origins_df['origin_name'].isin(selected_origin_names)
            ][origin_col].tolist()
    
    # Top N filter for origin visualization
    top_n = st.sidebar.slider(
        "Top N Origins",
        min_value=10,
        max_value=50,
        value=10,
        step=5,
        help="Number of top origins to display in the chart"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info(f"📊 Analyzing **{mode}** data for **{year_month[:4]}-{year_month[4:]}** ({day_type})")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"🎯 Current Selection")
    
    with col2:
        if selected_origins:
            st.metric("Selected Origins", len(selected_origins))
        else:
            st.metric("View", "All Origins")
    
    st.markdown("---")
    
    # Fetch data
    with st.spinner("Fetching data from BigQuery..."):
        origin_data = get_trip_count_by_origin(
            client, mode, year_month, day_type, selected_origins, top_n
        )
        time_data = get_trip_count_by_time_period(
            client, mode, year_month, day_type, selected_origins
        )
    
    if origin_data.empty or time_data.empty:
        st.warning("No data found for the selected filters.")
        st.stop()
    
    # Display metrics
    total_trips = origin_data['total_trips'].sum()
    avg_trips_per_origin = origin_data['total_trips'].mean()
    peak_origin = origin_data.iloc[0]['origin_name'] if not origin_data.empty else "N/A"
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total Trips",
            value=f"{total_trips:,.0f}",
            help="Total trip count for selected filters"
        )
    
    with col2:
        st.metric(
            label="Avg Trips per Origin",
            value=f"{avg_trips_per_origin:,.0f}",
            help=f"Average across top {top_n} origins"
        )
    
    with col3:
        st.metric(
            label="Busiest Origin",
            value=peak_origin.split(' - ')[0] if ' - ' in peak_origin else peak_origin,
            help="Origin with highest trip count"
        )
    
    st.markdown("---")
    
    # Visualization 1: Trip Count by Origin
    st.subheader(f"📍 Trip Count by Origin {mode.title()} {'Stop' if mode == 'Bus' else 'Station'}")
    
    fig_origin = px.bar(
        origin_data,
        x='total_trips',
        y='origin_name',
        orientation='h',
        title=f"Top {top_n} Origins by Trip Count",
        labels={
            'total_trips': 'Total Trips',
            'origin_name': f"Origin {'Stop' if mode == 'Bus' else 'Station'}"
        },
        color='total_trips',
        color_continuous_scale='Blues',
        height=max(400, top_n * 20)
    )
    
    fig_origin.update_layout(
        xaxis_title="Total Trips",
        yaxis_title="",
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False,
        hovermode='y unified'
    )
    
    st.plotly_chart(fig_origin, use_container_width=True)
    
    # Show data table
    with st.expander("📋 View Origin Data Table"):
        st.dataframe(
            origin_data.style.format({'total_trips': '{:,.0f}'}),
            use_container_width=True
        )
    
    st.markdown("---")
    
    # Visualization 2: Trip Count by Time Period
    st.subheader("⏰ Trip Count by Time Period")
    
    # Add hour labels
    time_data['hour_label'] = time_data['hour'].apply(lambda x: f"{x:02d}:00")
    
    # Create bar chart with peak hour highlighting
    fig_time = go.Figure()
    
    # Color by peak hour
    colors = ['#ef553b' if is_peak else '#636efa' 
              for is_peak in time_data['is_peak_hour']]
    
    fig_time.add_trace(go.Bar(
        x=time_data['hour_label'],
        y=time_data['total_trips'],
        marker_color=colors,
        text=time_data['total_trips'],
        textposition='outside',
        texttemplate='%{text:,.0f}',
        hovertemplate='<b>%{x}</b><br>' +
                      'Period: %{customdata[0]}<br>' +
                      'Trips: %{y:,.0f}<br>' +
                      '<extra></extra>',
        customdata=time_data[['time_period_name']].values
    ))
    
    fig_time.update_layout(
        title="Trip Distribution Across 24 Hours",
        xaxis_title="Hour of Day",
        yaxis_title="Total Trips",
        height=500,
        showlegend=False,
        hovermode='x unified'
    )
    
    # Add peak hour annotation
    fig_time.add_annotation(
        text="🔴 Peak Hours | 🔵 Off-Peak Hours",
        xref="paper", yref="paper",
        x=0.5, y=1.05,
        showarrow=False,
        font=dict(size=12)
    )
    
    st.plotly_chart(fig_time, use_container_width=True)
    
    # Show data table
    with st.expander("📋 View Time Period Data Table"):
        display_cols = ['hour', 'time_period_name', 'is_peak_hour', 'total_trips']
        st.dataframe(
            time_data[display_cols].style.format({'total_trips': '{:,.0f}'}),
            use_container_width=True
        )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        <p>📊 Data Source: LTA DataMall API | 🏗️ Built with Streamlit & BigQuery</p>
        <p>Singapore Public Transport Analytics Pipeline - Joseph Emmanuel Remoto</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
