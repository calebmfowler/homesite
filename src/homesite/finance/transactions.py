from homesite.finance.utils import Transactions

import streamlit as st

# === Backend ===
transactions = Transactions("transactions.csv", "chase")
fig, receipt_agg_list, expenditure_agg_list, max_granularity = transactions.visualize_transactions()

# === Frontend ===
st.markdown("## Aggregation")

col1, col2 = st.columns([1, 4])
with col1:
    st.markdown("#### Granularity")
    granularity = st.number_input("Granularity", min_value=1, max_value=max_granularity, width=150, label_visibility="collapsed")
    st.markdown("#### Receipts")
    st.dataframe(receipt_agg_list[granularity])
    st.markdown("#### Expenditures")
    st.dataframe(expenditure_agg_list[granularity])

with col2:
    frame = fig.frames[granularity]
    fig.update(data=frame.data)
    st.plotly_chart(fig)

st.markdown("## Tabulation")
st.dataframe(transactions.df.sort_values(by="date", ascending=False).drop(["number", "color"], axis=1))