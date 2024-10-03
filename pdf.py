# pdf.py

import streamlit as st
import pandas as pd
import pdfplumber
import re
import mysql.connector
from db_config import DB_CONFIG

FIXED_COLUMNS = ["S.No", "BillNo/Date", "Pharmacy Name", "City", "Batch", "Expiry", "Qty", "Free", "Rpl", "PTS", "PTR", "MRP", "TotSales"]

# Clean and fix columns from PDF
def clean_and_fix_columns(data):
    df = pd.DataFrame(data)
    df = df.iloc[:, :len(FIXED_COLUMNS)]
    df.columns = FIXED_COLUMNS[:len(df.columns)]
    df = df.dropna(how='any').reset_index(drop=True)
    
    if "BillNo/Date" in df.columns:
        df[['Bill No', 'Bill Date']] = df['BillNo/Date'].str.split('/', expand=True)
        df['Bill No'] = df['Bill No'].str.strip()
        df['Bill Date'] = df['Bill Date'].str.strip()

    if "City" in df.columns:
        df[['City', 'Pin Code']] = df['City'].str.extract(r'([A-Za-z\s]+)(\d{4,6})$')

    return df.drop(columns=['BillNo/Date'], errors='ignore')

# Extract tables from PDF
def extract_pdf_tables(file):
    try:
        combined_df = pd.DataFrame()
        product_names = []

        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    df = clean_and_fix_columns(table)
                    if not df.empty:
                        combined_df = pd.concat([combined_df, df], ignore_index=True)
        
        if not combined_df.empty:
            st.dataframe(combined_df)
            if st.button("Insert PDF Data"):
                insert_pdf_data_into_db(combined_df)
        else:
            st.write("No valid data found in the PDF.")
    except Exception as e:
        st.error(f"Error: {e}")

# Insert data into MySQL from PDF
def insert_pdf_data_into_db(df):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        insert_query = """
        INSERT INTO salesdata (Stockist_Code, Stockist_Name, Bill_No, Bill_Date, Chemist_Code, Chemist_Name, Address, City, Pin_Code, Material_Code, Material_Name, Batch_No, Sale_Qty, Free_Qty, Rate, Value)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        for _, row in df.iterrows():
            values = (
                row.get('S.No', None),
                "PURANI HOSPITAL SUPPLIES PVT LTD",
                row.get('Bill No', None),
                pd.to_datetime(row['Bill Date'], format='%d-%m-%Y').strftime('%Y-%m-%d') if pd.notna(row['Bill Date']) else None,
                "Chemist Code",
                row.get('Pharmacy Name', None),
                row.get('Address', None),
                row.get('City', None),
                row.get('Pin Code', None),
                "Material Code",
                row.get('Product Name', None),
                row.get('Batch', None),
                row.get('Qty', None),
                row.get('Free', None),
                row.get('Rate', None),
                row.get('TotSales', None)
            )
            cursor.execute(insert_query, values)

        connection.commit()
        st.success("PDF data inserted successfully.")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
