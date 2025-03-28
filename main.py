import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from src.policies.agg_monetary_policy3 import AggMonetaryPolicy3
from src.utils.calculations import *

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
    
    st.sidebar.header("Policy Parameters")
    st.sidebar.write(f"Using: {policy.policy_name}")
    
    # Basic parameters
    params = {}
    
    # Oracle Price
    oracle_price = st.sidebar.slider(
        "Oracle Price",
        min_value=0.5,
        max_value=1.5,
        value=1.0,
        step=0.01
    )
    params['price'] = to_wei(oracle_price)

    # Sigma
    sigma_human = st.sidebar.slider(
        "sigma",
        min_value=float(policy.MIN_SIGMA)/1e18,
        max_value=float(policy.MAX_SIGMA)/1e18,
        value=2e-2,
        format="%.4f"
    )
    params['sigma'] = to_wei(sigma_human)

    # Base rate (as annual percentage)
    base_rate_annual = st.sidebar.slider(
        "Base Rate (Annual %)",
        min_value=0.0,
        max_value=300.0,
        value=10.0
    )
    seconds_in_year = 365 * 24 * 60 * 60
    base_rate = to_wei((1 + base_rate_annual/100) ** (1/seconds_in_year) - 1)
    params['rate0'] = base_rate

    # Target debt fraction as percentage
    target_fraction = st.sidebar.slider(
        "Target Debt Fraction (%)",
        min_value=0.0,
        max_value=100.0,
        value=50.0
    )
    params['target_debt_fraction'] = to_wei(target_fraction/100)

    # Advanced parameters in expander
    with st.sidebar.expander("Advanced Parameters"):
        st.markdown("### Debt Fraction Parameters")
        use_debt_fraction = st.checkbox("Use direct debt fraction instead of pk_debt/total_debt")
        
        if use_debt_fraction:
            debt_fraction = st.slider(
                "Debt Fraction (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                help="PegKeeper debt / Total debt ratio"
            )
            params['pk_debt'] = to_wei(debt_fraction/100)
            params['total_debt'] = to_wei(1.0)
        else:
            col1, col2 = st.columns(2)
            with col1:
                pk_debt = st.number_input(
                    "PegKeeper Debt",
                    min_value=0.0,
                    value=0.0,
                    help="Total debt in PegKeeper contracts"
                )
                params['pk_debt'] = to_wei(pk_debt)
            
            with col2:
                total_debt = st.number_input(
                    "Total Debt",
                    min_value=0.0,
                    value=0.0,
                    help="Total system debt"
                )
                params['total_debt'] = to_wei(total_debt)

        st.markdown("### Market Parameters")
        utilization = st.slider(
            "Market Utilization (%)",
            min_value=0.0,
            max_value=100.0,
            value=50.0,
            help="Current market utilization (debt/ceiling ratio)"
        )
        params['debt_for'] = to_wei(utilization/100)
        params['ceiling'] = to_wei(1.0)

    # Create three plots: Rate vs Price, Rate vs Utilization, and Annual Rate vs Price
    fig = plt.figure(figsize=(15, 15))
    gs = fig.add_gridspec(3, 1, hspace=0.3)
    ax1, ax2, ax3 = [fig.add_subplot(gs[i]) for i in range(3)]

    # 1. Rate vs Price (with fixed utilization)
    prices_human = np.linspace(0.5, 1.5, 1000)
    prices = [to_wei(p) for p in prices_human]
    rates_by_price = []
    annual_rates_by_price = []
    
    for p in prices:
        current_params = params.copy()
        current_params['price'] = p
        rate = policy.calculate_rate(**current_params)
        rates_by_price.append(rate)
        annual_rates_by_price.append(calculate_annual_rate(rate) * 100)

    ax1.plot(prices_human, [from_wei(r) for r in rates_by_price])
    ax1.set_xlabel("Oracle Price")
    ax1.set_ylabel("Contract Rate")
    ax1.set_title(f"Contract Rate vs Oracle Price (Utilization: {utilization:.1f}%)")
    ax1.grid(True)

    # 2. Rate vs Utilization (with fixed price)
    utilizations_human = np.linspace(0, 100, 1000)
    rates_by_util = []
    annual_rates_by_util = []
    
    for u in utilizations_human:
        current_params = params.copy()
        current_params['debt_for'] = to_wei(u/100)
        rate = policy.calculate_rate(**current_params)
        rates_by_util.append(rate)
        annual_rates_by_util.append(calculate_annual_rate(rate) * 100)

    ax2.plot(utilizations_human, annual_rates_by_util)
    ax2.set_xlabel("Market Utilization (%)")
    ax2.set_ylabel("Annual Rate (%)")
    ax2.set_title(f"Annual Rate vs Utilization (Oracle Price: {oracle_price:.2f})")
    ax2.grid(True)

    # 3. Annual Rate vs Price
    ax3.plot(prices_human, annual_rates_by_price)
    ax3.set_xlabel("Oracle Price")
    ax3.set_ylabel("Annual Rate (%)")
    ax3.set_title(f"Annual Rate vs Oracle Price (Utilization: {utilization:.1f}%)")
    ax3.grid(True)

    # Display the plots
    st.pyplot(fig)

    # Rate calculator
    st.header("Rate Calculator")
    col1, col2 = st.columns(2)
    with col1:
        calc_price = st.number_input("Oracle Price:", value=1.0)
    with col2:
        calc_util = st.number_input("Utilization (%):", value=utilization)

    calc_params = params.copy()
    calc_params['price'] = to_wei(calc_price)
    calc_params['debt_for'] = to_wei(calc_util/100)
    
    calculated_rate = policy.calculate_rate(**calc_params)
    annual_rate = calculate_annual_rate(calculated_rate) * 100

    st.write(f"Contract Rate: {from_wei(calculated_rate):.6f}")
    st.write(f"Annual Rate: {annual_rate:.2f}%")

if __name__ == "__main__":
    main()