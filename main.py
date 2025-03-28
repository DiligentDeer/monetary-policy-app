import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.policies.agg_monetary_policy3 import AggMonetaryPolicy3
from src.utils.calculations import *

# Set page config for wider layout
st.set_page_config(layout="wide")

# Update CSS for metric cards
st.markdown("""
    <style>
    .metric-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-bottom: 12px;
    }
    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }
    .metric-label {
        font-size: 0.95em;
        font-weight: 500;
    }
    .metric-value {
        font-size: 0.95em;
        font-weight: bold;
    }
    .param-box {
        background-color: #f0f2f6;
        padding: 8px;
        border-radius: 4px;
    }
    .param-label {
        font-size: 0.8em;
        color: #666;
    }
    .param-value {
        font-size: 1.1em;
        font-weight: bold;
        margin: 4px 0;
    }
    .contract-value {
        font-family: monospace;
        background-color: #e9ecef;
        padding: 2px 4px;
        border-radius: 2px;
        font-size: 0.8em;
        cursor: pointer;
    }
    .calculator-container {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .calculator-result {
        background-color: #252525;
        padding: 15px;
        border-radius: 6px;
        margin-top: 15px;
    }
    .result-label {
        color: #6ac69b;
        font-size: 0.9em;
        margin-bottom: 8px;
    }
    .result-value {
        font-family: 'Roboto Mono', monospace;
        font-size: 1.1em;
        margin-bottom: 8px;
    }
    .annual-rate {
        font-size: 1.2em;
        font-weight: bold;
        color: #6ac69b;
    }
    </style>
""", unsafe_allow_html=True)

def create_parameter_tooltip(title, description):
    return f"{title} ❓\n\n{description}"

def main():
    st.title("crvUSD Monetary Policy Simulator")
    
    policies = {
        "AggMonetaryPolicy3": AggMonetaryPolicy3(),
    }
    
    selected_policy_name = st.sidebar.selectbox(
        "Select Monetary Policy",
        options=list(policies.keys())
    )
    
    policy = policies[selected_policy_name]
    
    # Move parameters to sidebar with tooltips
    st.sidebar.header("Policy Parameters")
    params = {}
    
    # Oracle Price
    oracle_price = st.sidebar.slider(
        "Oracle Price",
        min_value=0.5,
        max_value=1.5,
        value=1.0,
        step=0.1,
        help="The current price of crvUSD relative to the peg (1.0). Values below 1.0 indicate the token is trading below peg."
    )
    
    # Sigma
    sigma_human = st.sidebar.slider(
        "Sigma",
        min_value=float(policy.MIN_SIGMA)/1e18,
        max_value=float(policy.MAX_SIGMA)/1e18,
        value=2e-2,
        format="%.2f",
        help="Volatility parameter that determines how aggressively rates change in response to price deviations from peg."
    )
    
    # Base rate
    base_rate_annual = st.sidebar.slider(
        "Base Rate (Annual %)",
        min_value=0,
        max_value=300,
        value=10,
        help="The baseline interest rate when price is at peg and other factors are neutral."
    )
    
    # Target debt fraction
    target_fraction = st.sidebar.slider(
        "Target Debt Fraction (%)",
        min_value=0,
        max_value=100,
        value=50,
        help="Target ratio for PegKeeper debt relative to total debt."
    )
    
    # Debt Fraction
    debt_fraction = st.sidebar.slider(
        "Debt Fraction (%)",
        min_value=0,
        max_value=100,
        value=10,
        help="Current ratio of PegKeeper debt to total debt."
    )
    
    # Market Utilization
    utilization = st.sidebar.slider(
        "Market Utilization (%)",
        min_value=0,
        max_value=100,
        value=50,
        help="Percentage of the market's debt ceiling currently in use."
    )

    # Set up parameters for calculations
    params = {
        'price': to_wei(oracle_price),
        'sigma': to_wei(sigma_human),
        'rate0': to_wei((1 + base_rate_annual/100) ** (1/365/24/60/60) - 1),
        'target_debt_fraction': to_wei(target_fraction/100),
        'pk_debt': to_wei(debt_fraction/100),
        'total_debt': to_wei(1.0),
        'debt_for': to_wei(utilization/100),
        'ceiling': to_wei(1.0)
    }

    # Create plots
    prices_human = np.linspace(0.5, 1.5, 1000)
    utilizations_human = np.linspace(0, 100, 1000)
    
    # Calculate rates
    annual_rates_by_price = []
    annual_rates_by_util = []
    
    for p in prices_human:
        current_params = params.copy()
        current_params['price'] = to_wei(p)
        rate = policy.calculate_rate(**current_params)
        annual_rates_by_price.append(calculate_annual_rate(rate) * 100)
    
    for u in utilizations_human:
        current_params = params.copy()
        current_params['debt_for'] = to_wei(u/100)
        rate = policy.calculate_rate(**current_params)
        annual_rates_by_util.append(calculate_annual_rate(rate) * 100)

    # Create plots with custom styling
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f"Annual Rate vs Oracle Price (Utilization: {utilization:.1f}%)",
            f"Annual Rate vs Utilization (Oracle Price: {oracle_price:.2f})"
        ),
        horizontal_spacing=0.1
    )

    # Custom theme colors
    COLORS = {
        'background': 'rgba(0,0,0,0)',  # Transparent background
        'primary': '#6ac69b',
        'secondary': '#127475',
        'text': '#ffffff'
    }

    # Add traces with custom styling
    fig.add_trace(
        go.Scatter(
            x=prices_human,
            y=annual_rates_by_price,
            line=dict(color=COLORS['primary'], width=2),
            name="Annual Rate"
        ),
        row=1, col=1
    )

    # Add vertical line at x=1 for the first chart
    fig.add_vline(
        x=1, 
        line_dash="dot", 
        line_color="rgba(255, 255, 255, 0.4)",  # Semi-transparent white
        row=1, 
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=utilizations_human,
            y=annual_rates_by_util,
            line=dict(color=COLORS['secondary'], width=2),
            name="Annual Rate"
        ),
        row=1, col=2
    )

    # Update layout with custom styling
    fig.update_layout(
        height=500,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot background
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent paper background
        font=dict(color=COLORS['text']),
        margin=dict(l=50, r=50, t=50, b=50)
    )

    # Update axes with labels and formatting
    fig.update_xaxes(
        gridcolor='rgba(255,255,255,0.1)',
        zerolinecolor='rgba(255,255,255,0.1)',
        title_font=dict(color=COLORS['text']),
        tickfont=dict(color=COLORS['text']),
        row=1, col=1,
        title_text="Oracle Price"
    )
    
    fig.update_xaxes(
        gridcolor='rgba(255,255,255,0.1)',
        zerolinecolor='rgba(255,255,255,0.1)',
        title_font=dict(color=COLORS['text']),
        tickfont=dict(color=COLORS['text']),
        row=1, col=2,
        title_text="Utilization (%)"
    )
    
    # Update y-axes with percentage format
    fig.update_yaxes(
        gridcolor='rgba(255,255,255,0.1)',
        zerolinecolor='rgba(255,255,255,0.1)',
        title_font=dict(color=COLORS['text']),
        tickfont=dict(color=COLORS['text']),
        title_text="Annual Rate (%)",
        ticksuffix="%",
        row=1, col=1
    )
    
    fig.update_yaxes(
        gridcolor='rgba(255,255,255,0.1)',
        zerolinecolor='rgba(255,255,255,0.1)',
        title_font=dict(color=COLORS['text']),
        tickfont=dict(color=COLORS['text']),
        title_text="Annual Rate (%)",
        ticksuffix="%",
        row=1, col=2
    )

    # Display the plots
    st.plotly_chart(fig, use_container_width=True)

    # Rate calculator section
    st.header("Rate Calculator")
    
    # Create three columns: two for inputs, one for result
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        calc_price = st.number_input(
            "Oracle Price:",
            value=oracle_price,
            min_value=0.5,
            max_value=1.5,
            step=0.1,
            format="%.1f"
        )
    
    with col2:
        calc_util = st.number_input(
            "Utilization (%):",
            value=utilization,
            min_value=0,
            max_value=100,
            step=1
        )

    # Calculate rates
    calc_params = params.copy()
    calc_params['price'] = to_wei(calc_price)
    calc_params['debt_for'] = to_wei(calc_util/100)
    
    calculated_rate = policy.calculate_rate(**calc_params)
    annual_rate = calculate_annual_rate(calculated_rate) * 100

    # Display just the annual rate in the third column
    with col3:
        st.markdown("<p style='margin-bottom: 0px;'>Annual Rate:</p>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='color: #6ac69b; margin-top: 0;'>{annual_rate:.2f}%</h4>", unsafe_allow_html=True)

    # Current Parameters section moved to bottom
    st.header("Current Parameters")
    
    

    # Create three columns for the parameters
    col1, col2, col3 = st.columns(3)

    # First row
    with col1:
        st.markdown("""
            <div class="metric-header">
                <span class="metric-label">Oracle Price</span>
                <span class="metric-value">{:.4f}</span>
            </div>
        """.format(oracle_price), unsafe_allow_html=True)
        st.code(str(to_wei(oracle_price)))

    with col2:
        st.markdown("""
            <div class="metric-header">
                <span class="metric-label">Sigma</span>
                <span class="metric-value">{:.4f}</span>
            </div>
        """.format(sigma_human), unsafe_allow_html=True)
        st.code(str(to_wei(sigma_human)))

    with col3:
        st.markdown("""
            <div class="metric-header">
                <span class="metric-label">Base Rate (Annual)</span>
                <span class="metric-value">{:.2f}%</span>
            </div>
        """.format(base_rate_annual), unsafe_allow_html=True)
        st.code(str(to_wei((1 + base_rate_annual/100) ** (1/365/24/60/60) - 1) * 100))

    # Second row
    with col1:
        st.markdown("""
            <div class="metric-header">
                <span class="metric-label">Target Debt Fraction</span>
                <span class="metric-value">{:.2f}%</span>
            </div>
        """.format(target_fraction), unsafe_allow_html=True)
        st.code(str(to_wei(target_fraction/100)))

    with col2:
        st.markdown("""
            <div class="metric-header">
                <span class="metric-label">Debt Fraction</span>
                <span class="metric-value">{:.2f}%</span>
            </div>
        """.format(debt_fraction), unsafe_allow_html=True)
        st.code(str(to_wei(debt_fraction/100)))

    with col3:
        st.markdown("""
            <div class="metric-header">
                <span class="metric-label">Market Utilization</span>
                <span class="metric-value">{:.2f}%</span>
            </div>
        """.format(utilization), unsafe_allow_html=True)
        st.code(str(to_wei(utilization/100)))

if __name__ == "__main__":
    main()