import mysql.connector
import streamlit as st
import pandas as pd

# Function to connect to the MySQL database using mysql.connector
def connect_to_mysql():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',  # Add your password here if applicable
        database='u840048117_Apex_demo'
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
            '1007',  # Stockist_Code (you can replace it with actual data if available)
            'PURANI HOSPITAL SUPPLIES PVT LTD',  # Stockist_Name
            row['Bill No'],  # Bill_No
            bill_date_str,  # Bill_Date
            'CHM001',  # Chemist_Code (replace with actual data)
            row['Pharmacy'],  # Chemist_Name
            'Some Address',  # Address (replace with actual data)
            row['City Name'],  # City
            row['Pincode'],  # Pin_Code
            'MAT001',  # Material_Code (replace with actual data)
            row['Product Name'],  # Material_Name
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

