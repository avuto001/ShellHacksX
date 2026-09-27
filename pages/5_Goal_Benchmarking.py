import streamlit as st
import pydeck as pdk
from services.private_markets import get_private_equity_data
from utils.ui import page_header

# Set up page header
page_header("Goal Benchmarking", "Private Equity Firms across the Continental US")

st.markdown("Explore private equity firms categorized by industry sector. Hover over a location to see key details and restaurant investments.")

# Load PE firm data
df = get_private_equity_data()

# Sector Filter Sidebar / Multi-select
sectors = list(df["sector"].unique())
selected_sectors = st.multiselect("Filter by Sector:", options=sectors, default=sectors)

filtered_df = df[df["sector"].isin(selected_sectors)]

# Define PyDeck Layer
scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered_df,
    get_position=["lon", "lat"],
    get_fill_color="color",
    get_radius=80000,  # Radius in meters
    pickable=True,
    auto_highlight=True,
)

# Set initial map view centered over continental USA
view_state = pdk.ViewState(
    latitude=39.8283,
    longitude=-98.5795,
    zoom=3.5,
    pitch=0
)

# Tooltip configuration for hover info
tooltip = {
    "html": """
        <b>Firm Name:</b> {name}<br/>
        <b>Sector:</b> {sector}<br/>
        <b>Location:</b> {city}<br/>
        <b>Assets Under Management (AUM):</b> {aum}<br/>
        <b>Restaurant/Brand Investments:</b> {restaurants}
    """,
    "style": {
        "backgroundColor": "darkblue",
        "color": "white",
        "fontSize": "13px",
        "padding": "10px",
        "borderRadius": "5px"
    }
}

# Display Map
st.pydeck_chart(
    pdk.Deck(
        layers=[scatter_layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/light-v10",
        tooltip=tooltip
    )
)

# Display Sector Legend
st.markdown("### Sector Color Legend")
legend_cols = st.columns(len(sectors))
sector_colors = {
    "Technology": "🟦 Blue",
    "Consumer & Dining": "🟧 Orange",
    "Healthcare": "🟩 Green",
    "Energy & Industrials": "🟪 Purple"
}

for col, sector in zip(legend_cols, sectors):
    col.metric(label=sector, value=sector_colors.get(sector, "⚪ Gray"))

# Data Table below map
with st.expander("View Data Table"):
    st.dataframe(filtered_df[["name", "sector", "city", "aum", "restaurants"]], use_container_width=True)