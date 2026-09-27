import pandas as pd

def get_private_equity_data() -> pd.DataFrame:
    """
    Returns data for private equity firms across the continental US
    with coordinates, industry sector, color coding, and portfolio investments.
    """
    data = [
        {
            "name": "Blackstone",
            "sector": "Technology",
            "city": "New York, NY",
            "lat": 40.7589,
            "lon": -73.9851,
            "color": [0, 122, 255, 200],  # Blue
            "hex_color": "#007AFF",
            "restaurants": "Jersey Mike's, Servpro",
            "aum": "$1.0 Trillion"
        },
        {
            "name": "Roark Capital Group",
            "sector": "Consumer & Dining",
            "city": "Atlanta, GA",
            "lat": 33.7490,
            "lon": -84.3880,
            "color": [255, 149, 0, 200],  # Orange
            "hex_color": "#FF9500",
            "restaurants": "Dunkin', Arby's, Subway, Sonic, Jimmy John's",
            "aum": "$37 Billion"
        },
        {
            "name": "KKR (Kohlberg Kravis Roberts)",
            "sector": "Healthcare",
            "city": "San Francisco, CA",
            "lat": 37.7749,
            "lon": -122.4194,
            "color": [52, 199, 89, 200],  # Green
            "hex_color": "#34C759",
            "restaurants": "First Reserve, US LBM",
            "aum": "$500 Billion"
        },
        {
            "name": "Sentinel Capital Partners",
            "sector": "Consumer & Dining",
            "city": "New York, NY",
            "lat": 40.7128,
            "lon": -74.0060,
            "color": [255, 149, 0, 200],  # Orange
            "hex_color": "#FF9500",
            "restaurants": "TGI Fridays, Fazoli's, Newk's Eatery",
            "aum": "$5.2 Billion"
        },
        {
            "name": "Thoma Bravo",
            "sector": "Technology",
            "city": "Chicago, IL",
            "lat": 41.8781,
            "lon": -87.6298,
            "color": [0, 122, 255, 200],  # Blue
            "hex_color": "#007AFF",
            "restaurants": "N/A (Software Focused)",
            "aum": "$130 Billion"
        },
        {
            "name": "TPG Capital",
            "sector": "Energy & Industrials",
            "city": "Fort Worth, TX",
            "lat": 32.7555,
            "lon": -97.3308,
            "color": [175, 82, 222, 200],  # Purple
            "hex_color": "#AF52DE",
            "restaurants": "Burger King (Historical), Mendocino Farms",
            "aum": "$220 Billion"
        },
        {
            "name": "Golden Gate Capital",
            "sector": "Consumer & Dining",
            "city": "San Francisco, CA",
            "lat": 37.7880,
            "lon": -122.4075,
            "color": [255, 149, 0, 200],  # Orange
            "hex_color": "#FF9500",
            "restaurants": "Red Lobster, California Pizza Kitchen, Bob Evans",
            "aum": "$19 Billion"
        },
        {
            "name": "Advent International",
            "sector": "Healthcare",
            "city": "Boston, MA",
            "lat": 42.3601,
            "lon": -71.0589,
            "color": [52, 199, 89, 200],  # Green
            "hex_color": "#34C759",
            "restaurants": "Bojangles, First Watch",
            "aum": "$90 Billion"
        }
    ]
    return pd.DataFrame(data)