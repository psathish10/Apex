import re
import platform
import pandas as pd
import os
import streamlit as st
import mysql.connector
import pythoncom

is_windows = platform.system() == "Windows"

if is_windows:
    import win32com.client as win32

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'apex'
}

def extract_text_from_doc(file):
    if not is_windows:
        st.error("This functionality is only available on Windows.")
        return None
    
    try:
        temp_doc_path = os.path.join(os.getcwd(), "temp.doc")
        with open(temp_doc_path, "wb") as f:
            f.write(file.read())

        pythoncom.CoInitialize()
        word = win32.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(temp_doc_path)
        full_text = doc.Content.Text
        doc.Close(False)
        word.Quit()
        pythoncom.CoUninitialize()
        os.remove(temp_doc_path)
        return full_text
    except Exception as e:
        st.error(f"Error occurred while extracting text: {e}")
        return None

def process_structured_data_with_product_names(text):
    lines = text.splitlines()
    row_pattern = re.compile(r"([A-Za-z\s.]+)\s+(\d{6})\s+(-?\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)")
    
    stockist_name = "LIFECARE PHARMA PRIVATE LIMITED"
    data = []
    current_product_name = None
    next_line_is_product = False

    for line in lines:
        line = line.strip()
        if line.startswith('---'):
            next_line_is_product = True
            continue
        if next_line_is_product:
            current_product_name = line
            next_line_is_product = False
            continue
        match = row_pattern.match(line)
        if match:
            customer_name, pin, qty, gross_amt, net_amt = match.groups()
            data.append({
                "Stockist Name": stockist_name,
                "Product Name": current_product_name,
                "Customer Name": customer_name.strip(),
                "Pin": pin.strip(),
                "Qty": int(qty),
                "Gross Amt": float(gross_amt),
                "Net Amt": float(net_amt)
            })
    return pd.DataFrame(data)

def insert_word_data_into_db(df):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        insert_query = """
        INSERT INTO salesdata (
            Stockist_Code, Stockist_Name, Bill_No, Bill_Date, 
            Chemist_Code, Chemist_Name, Address, City, 
            Pin_Code, Material_Code, Material_Name, Batch_No, 
            Sale_Qty, Free_Qty, Rate, Value
        ) VALUES (
            %s, %s, %s, CURDATE(), 
            %s, %s, %s, %s, 
            %s, %s, %s, %s, 
            %s, %s, %s, %s
        )
        """

        for index, row in df.iterrows():
            values = (
                'CODE', row['Stockist Name'], 'BILL_NO', 'CHEMIST_CODE',
                row['Customer Name'], 'ADDRESS', 'CITY', row['Pin'],
                'MATERIAL_CODE', row['Product Name'], 'BATCH_NO',
                row['Qty'], 0, row['Gross Amt'], row['Net Amt'],
            )
            cursor.execute(insert_query, values)

        connection.commit()
        st.success("Data successfully inserted into the database.")
    except mysql.connector.Error as err:
        st.error(f"Error inserting data into MySQL: {err}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()