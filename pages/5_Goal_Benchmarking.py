import streamlit as st
import pydeck as pdk
import pandas as pd
from services.private_markets import get_private_equity_data
from utils.ui import page_header

# Header
page_header("Goal Benchmarking", "Private Equity Firms & Financial Benchmarks")

# Load data
df = get_private_equity_data()

# Ensure investor metrics exist in dataset
if "irr" not in df.columns:
    df["irr"] = ["21.5%", "18.2%", "24.1%", "19.8%", "22.0%", "17.9%", "16.4%", "20.3%"]
if "deal_size" not in df.columns:
    df["deal_size"] = ["$100M - $1B", "$50M - $500M", "$200M - $2B", "$20M - $200M", "$150M - $1.5B", "$100M - $800M", "$30M - $300M", "$80M - $600M"]
if "state" not in df.columns:
    df["state"] = df["city"].apply(lambda x: x.split(", ")[-1] if ", " in x else "")

st.markdown("### Private Equity Screener & Analytics")

# --- Dropdown Menu & Filters (Above the Table) ---
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    search_query = st.text_input(
        "Search Firm, City, or Brand", 
        placeholder="e.g. New York, Blackstone, Dunkin..."
    )

with col2:
    all_sectors = list(df["sector"].unique())
    selected_sectors = st.multiselect("Sector Dropdown", options=all_sectors, default=all_sectors)

with col3:
    all_states = sorted(list(df["state"].unique()))
    selected_states = st.multiselect("Location (State)", options=all_states, default=all_states)

# Filter Logic
filtered_df = df[
    (df["sector"].isin(selected_sectors)) & 
    (df["state"].isin(selected_states))
].copy()

if search_query.strip():
    q = search_query.lower()
    filtered_df = filtered_df[
        filtered_df["name"].str.lower().str.contains(q) |
        filtered_df["city"].str.lower().str.contains(q) |
        filtered_df["sector"].str.lower().str.contains(q) |
        filtered_df["restaurants"].str.lower().str.contains(q)
    ]

# --- 1. Analytical Table (Above Map) ---
st.markdown("#### Analytical Table")

if not filtered_df.empty:
    # Display formatted interactive table
    display_df = filtered_df[["name", "sector", "city", "aum", "irr", "deal_size", "restaurants"]].rename(
        columns={
            "name": "Firm Name",
            "sector": "Sector",
            "city": "Location",
            "aum": "Amount (AUM)",
            "irr": "Target Net IRR",
            "deal_size": "Target Deal Size",
            "restaurants": "Restaurant / Brand Portfolio"
        }
    )
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Amount (AUM)": st.column_config.TextColumn("Amount (AUM)", help="Assets Under Management"),
            "Target Net IRR": st.column_config.TextColumn("Target Net IRR"),
        }
    )
else:
    st.warning("No private equity firms match your current filter criteria.")

st.divider()

# --- 2. Interactive Map (Below Table) ---
st.markdown("#### 🗺️ Continental US Firm Locations")
print(filtered_df)

filtered_df['Result'] = filtered_df.apply(
        lambda row:500000 * (float(row['irr'].replace("%",''))/100),
        axis=1
 );
# Map setup
scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered_df,
    get_position=["lon", "lat"],
    get_fill_color="color",
    get_radius="Result",
    pickable=True,
    auto_highlight=True,
)

view_state = pdk.ViewState(
    latitude=38.8283,
    longitude=-96.5795,
    zoom=3.5,
    pitch=0
)

tooltip = {
    "html": """
        <div style="font-family: sans-serif; padding: 4px;">
            <b style="font-size: 14px; color: #4DA6FF;">{name}</b><br/>
            <b>Sector:</b> {sector}<br/>
            <b>Location:</b> {city}<br/>
            <b>Amount (AUM):</b> {aum}<br/>
            <b>Net IRR:</b> {irr}<br/>
            <b>Target Deal Size:</b> {deal_size}<br/>
            <b>Brands/Restaurants:</b> {restaurants}
        </div>
    """,
    "style": {
        "backgroundColor": "#1E1E1E",
        "color": "white",
        "fontSize": "12px",
        "borderRadius": "6px"
    }
}

deck = pdk.Deck(
    layers=[scatter_layer],
    initial_view_state=view_state,
    map_provider="carto",
    map_style="light",
    tooltip=tooltip
)

st.pydeck_chart(deck, use_container_width=True)

# Sector Legend
l1, l2, l3, l4 = st.columns(4)
l1.markdown("🟦 **Technology**")
l2.markdown("🟧 **Consumer & Dining**")
l3.markdown("🟩 **Healthcare**")
l4.markdown("🟪 **Energy & Industrials**")