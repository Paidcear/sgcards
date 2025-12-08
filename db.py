import streamlit as st
from sqlalchemy import create_engine

HOST = st.secrets["DB_HOST"]
USER = st.secrets["DB_USER"]
PASSWD = st.secrets["DB_PASS"]
DB = st.secrets["DB_NAME"]
PORT = st.secrets["DB_PORT"]

# Crear motor de SQLAlchemy
engine = create_engine(f"mysql+pymysql://{USER}:{PASSWD}@{HOST}:{PORT}/{DB}")
