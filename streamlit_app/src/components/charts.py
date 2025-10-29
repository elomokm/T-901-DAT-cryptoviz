import streamlit as st
import pandas as pd
import plotly.express as px


def line_price_chart(df: pd.DataFrame):
    if df.empty:
        st.warning("Aucune donnée à afficher")
        return
    fig = px.line(
        df,
        x="_time",
        y="_value",
        color="crypto",
        title="price_usd",
        labels={"_time": "Time", "_value": "USD"},
    )
    st.plotly_chart(fig, use_container_width=True)
