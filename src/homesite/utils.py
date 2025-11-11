import os
from pathlib import Path
import streamlit as st
import tomllib

APP_ROOT = Path(__file__).resolve().parents[2]

PRODUCTION_ENV = os.getenv("STREAMLIT_SERVER_HEADLESS") == "true"

if PRODUCTION_ENV:
    SECRETS = st.secrets
else:
    with open(APP_ROOT / "secrets.toml", "rb") as secrets_file:
        SECRETS = tomllib.load(secrets_file)

PRODUCTION_DATA = True