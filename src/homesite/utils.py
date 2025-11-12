import os
from pathlib import Path
import streamlit as st
import tomllib

APP_ROOT = Path(__file__).resolve().parents[2]

PRODUCTION_ENV = not os.path.exists(APP_ROOT / "secrets.toml")

if PRODUCTION_ENV:
    SECRETS = st.secrets
else:
    with open(APP_ROOT / "secrets.toml", "rb") as secrets_file:
        SECRETS = tomllib.load(secrets_file)

PRODUCTION_DATA = True