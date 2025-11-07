import streamlit as st

if __name__ == "__main__":
    st.set_page_config("home", "🪴", "wide")

    homesite = st.navigation(
        {
            "finance": [
                st.Page("finance/transactions.py", title="transactions", icon="🛒"),
                st.Page("finance/assets.py", title="assets", icon="🏛️")
            ],
        },
        position="top",
        expanded=True,
    )

    homesite.run()