import streamlit as st
import pydeck as pdk
from services.private_markets import get_private_equity_data
from utils.ui import page_header

# Header
page_header("Goal Benchmarking", "Private Equity Firms & Financial Benchmarks")

# Load data
df = get_private_equity_data()

# Add mock investor metrics if not present in the base dataframe
if "irr" not in df.columns:
    df["irr"] = ["21.5%", "18.2%", "24.1%", "19.8%", "22.0%", "17.9%", "16.4%", "20.3%"]
if "deal_size" not in df.columns:
    df["deal_size"] = ["$100M - $1B", "$50M - $500M", "$200M - $2B", "$20M - $200M", "$150M - $1.5B", "$100M - $800M", "$30M - $300M", "$80M - $600M"]
if "state" not in df.columns:
    df["state"] = df["city"].apply(lambda x: x.split(", ")[-1] if ", " in x else "")

# --- Controls & Search Bar ---
col1, col2 = st.columns([2, 1])

with col1:
    search_query = st.text_input(
        "🔍 Search PE Firms", 
        placeholder="Type city, state, firm name, or restaurant brand (e.g. New York, CA, Dunkin)..."
    )

with col2:
    sectors = list(df["sector"].unique())
    selected_sectors = st.multiselect("Filter by Sector", options=sectors, default=sectors)

# Filter Logic
filtered_df = df[df["sector"].isin(selected_sectors)].copy()

if search_query.strip():
    q = search_query.lower()
    filtered_df = filtered_df[
        filtered_df["name"].str.lower().str.contains(q) |
        filtered_df["city"].str.lower().str.contains(q) |
        filtered_df["sector"].str.lower().str.contains(q) |
        filtered_df["restaurants"].str.lower().str.contains(q)
    ]

st.caption(f"Showing **{len(filtered_df)}** of **{len(df)}** private equity firms.")

# --- PyDeck Map Section ---
# Carto light style works out of the box without requiring a Mapbox API token
scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered_df,
    get_position=["lon", "lat"],
    get_fill_color="color",
    get_radius=90000,
    pickable=True,
    auto_highlight=True,
)

# Center initial view over US continental mainland
view_state = pdk.ViewState(
    latitude=38.8283,
    longitude=-96.5795,
    zoom=3.6,
    pitch=0
)

tooltip = {
    "html": """
        <div style="font-family: sans-serif; padding: 4px;">
            <b style="font-size: 14px; color: #4DA6FF;">{name}</b><br/>
            <b>Sector:</b> {sector}<br/>
            <b>Location:</b> {city}<br/>
            <b>AUM:</b> {aum}<br/>
            <b>Net IRR:</b> {irr}<br/>
            <b>Target Deal Size:</b> {deal_size}<br/>
            <b>Brands/Restaurants:</b> {restaurants}
        </div>
    """,
    "style": {
        "backgroundColor": "#1E1E1E",
        "color": "white",
        "fontSize": "12px",
        "borderRadius": "6px",
        "boxShadow": "0px 4px 10px rgba(0,0,0,0.3)"
    }
}

deck = pdk.Deck(
    layers=[scatter_layer],
    initial_view_state=view_state,
    map_provider="carto",
    map_style="light",
    tooltip=tooltip
)

st.pydeck_chart(deck)

# --- Sector Legend ---
st.markdown("### Sector Legend")
l1, l2, l3, l4 = st.columns(4)
l1.markdown("🟦 **Technology**")
l2.markdown("🟧 **Consumer & Dining**")
l3.markdown("🟩 **Healthcare**")
l4.markdown("🟪 **Energy & Industrials**")

st.divider()

# --- Investor Financial Overview Cards ---
st.markdown("### 📊 Investor Financial Summary")

if not filtered_df.empty:
    selected_firm = st.selectbox("Select a firm for detailed financial benchmarking:", filtered_df["name"].unique())
    firm_data = filtered_df[filtered_df["name"] == selected_firm].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Assets Under Management", firm_data["aum"])
    c2.metric("Target Net IRR", firm_data.get("irr", "N/A"))
    c3.metric("Target Deal Size", firm_data.get("deal_size", "N/A"))
    c4.metric("Headquarters", firm_data["city"])

    with st.expander(f"📁 Full Investor Dossier — {firm_data['name']}", expanded=True):
        st.write(f"**Primary Sector Focus:** {firm_data['sector']}")
        st.write(f"**Portfolio Brands & Restaurants:** {firm_data['restaurants']}")
        st.write(f"**Geographic Coordinates:** Lat `{firm_data['lat']}`, Lon `{firm_data['lon']}`")
else:
    st.warning("No private equity firms match your search or filter settings.")