import pymysql
import streamlit as st
import datetime
import pandas as pd

def connect_to_mysql():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='apex'
    )
# Function to insert data into the MySQL table
def insert_into_mysql(df, connection):
    cursor = connection.cursor()

    # SQL query to insert data into the MySQL salesdata table
    insert_query = """
        INSERT INTO salesdata (
            Stockist_Code, Stockist_Name, Bill_No, Bill_Date, 
            Chemist_Code, Chemist_Name, Address, City, 
            Pin_Code, Material_Code, Material_Name, Batch_No, 
            Sale_Qty, Free_Qty, Rate, Value
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
      # Loop through the dataframe and insert each row
    for _, row in df.iterrows():
        bill_date = pd.to_datetime(row['Bill Date'], format='%d-%m-%Y', errors='coerce')
        bill_date_str = bill_date.strftime('%Y-%m-%d') if pd.notna(bill_date) else None
        cursor.execute(insert_query, (
            'STK001',  # Stockist_Code (you can replace it with actual data if available)
            'PURANI HOSPITAL SUPPLIES PVT LTD',  # Stockist_Name
            row['Bill No'],  # Bill_No
           bill_date_str,  # Bill_Date
            'CHM001',  # Chemist_Code (replace with actual data)
            row['Pharmacy'],  # Chemist_Name
            'Some Address',  # Address (replace with actual data)
            row['City Name'],  # City
            row['Pincode'],  # Pin_Code
            'MAT001',  # Material_Code (replace with actual data)
            row['Product Name'],  # Material_Name (replace with actual data)
            row['Batch'],  # Batch_No
            row['Qty'],  # Sale_Qty
            row['Free'],  # Free_Qty
            row['PTS'],  # Rate
            row['TotSales']  # Value
        ))

    # Commit the transaction
    connection.commit()
    cursor.close()
    st.write(f"Inserted {len(df)} rows into MySQL successfully.")