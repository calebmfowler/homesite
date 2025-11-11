from homesite.finance.utils import Transactions

import streamlit as st

# === Backend ===
sest = st.session_state

if "transactions" not in sest:
    sest.transactions = Transactions("transactions.csv", "chase")
    sest.fig, sest.receipt_agg_list, sest.expenditure_agg_list, sest.max_granularity = sest.transactions.visualize_transactions()

# === Frontend ===
st.set_page_config("transactions", "🛒", "wide")

if "transactions" in sest:
    st.markdown("## Aggregation")

    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("#### Granularity")
        granularity = st.number_input("Granularity", min_value=1, max_value=sest.max_granularity, width=150, label_visibility="collapsed")
        st.markdown("#### Receipts")
        st.dataframe(sest.receipt_agg_list[granularity])
        st.markdown("#### Expenditures")
        st.dataframe(sest.expenditure_agg_list[granularity])

    with col2:
        frame = sest.fig.frames[granularity]
        sest.fig.update(data=frame.data)
        st.plotly_chart(sest.fig)

    st.markdown("## Tabulation")
    st.dataframe(sest.transactions.df.sort_values(by="date", ascending=False).drop(["number", "color"], axis=1))


    st.markdown("## Plaid Tabulation")
    st.dataframe(sest.transactions.plaid_df)