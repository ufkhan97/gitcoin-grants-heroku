import streamlit as st
import plotly.express as px
import pandas as pd

# Contoh data (Anda bisa mengganti dengan data asli dari database)
data = {
    'Tanggal': ['2024-01-01', '2024-02-01', '2024-03-01'],
        'Jumlah Donasi': [1000, 1500, 2000]
        }
        df = pd.DataFrame(data)
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])

        # Buat grafik garis menggunakan Plotly
        fig = px.line(df, x='Tanggal', y='Jumlah Donasi', title='Tren Donasi dari Waktu ke Waktu')

        # Tampilkan grafik di Streamlit
        st.plotly_chart(fig)