import streamlit as st
import pandas as pd
from utils.ui import page_header
from services.risk import calculate_goal_progress

page_header("Goal-Based Benchmarking", "Track wealth against real-life milestones.")

st.markdown("Set a target milestone (e.g., house down payment, retirement, or emergency fund) to see the required annual growth rate needed to reach your goal.")

# --- Form Inputs ---
with st.form("goal_benchmark_form"):
    col1, col2 = st.columns(2)
    with col1:
        goal_name = st.text_input("Goal Name", value="House Down Payment")
        current_val = st.number_input("Current Allocated Funds ($)", min_value=1.0, value=10000.0, step=500.0)
    with col2:
        target_val = st.number_input("Target Amount ($)", min_value=1.0, value=50000.0, step=1000.0)
        target_year = st.slider("Target Year", min_value=2026, max_value=2045, value=2031)
    
    submitted = st.form_submit_button("Calculate Benchmark Path", use_container_width=True)

# --- Calculations & Visualization ---
if current_val >= target_val:
    st.success("🎉 You have already reached or exceeded your target goal amount!")
else:
    cagr, trajectory = calculate_goal_progress(current_val, target_val, target_year)
    
    # Display Key Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Current Value", f"${current_val:,.2f}")
    m2.metric("Target Goal", f"${target_val:,.2f}")
    m3.metric("Required Annual Growth (CAGR)", f"{cagr * 100:.2f}%")
    
    # Plot Trajectory Chart
    df = pd.DataFrame(list(trajectory.items()), columns=["Year", "Target Path ($)"])
    st.subheader(f"Required Growth Path for: {goal_name}")
    st.line_chart(df.set_index("Year"))
    
    # Contextual Feedback
    if cagr > 0.12:
        st.warning("⚠️ **High Risk Profile Required:** Achieving over 12% annual return typically requires concentrated growth assets. Consider lowering your target or extending your timeline.")
    elif cagr > 0.06:
        st.info("📈 **Moderate Profile:** A balanced portfolio of equities and diversified ETFs can realistically target this return rate.")
    else:
        st.success("🛡️ **Conservative Profile:** This goal can likely be achieved using conservative income or broad index allocations.")
        