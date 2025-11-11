import streamlit as st

if __name__ == "__main__":
    pages = {
        "home": [
            st.Page("home/home.py", title="home", icon="🪴")
        ],
        "finance": [
            st.Page("finance/transactions.py", title="transactions", icon="🛒"),
            st.Page("finance/assets.py", title="assets", icon="🏛️")
        ],
    }

    homesite = st.navigation(pages, position="top", expanded=True)

    homesite.run()