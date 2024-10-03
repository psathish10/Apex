# word.py

import os
import re
import pandas as pd
import streamlit as st
import mysql.connector
import win32com.client as win32
from db_config import DB_CONFIG

# Function to extract text from .doc file using pywin32
def extract_text_from_doc(file):
    try:
        # Save the uploaded file to a temporary path
        temp_doc_path = os.path.join(os.getcwd(), "temp.doc")
        with open(temp_doc_path, "wb") as f:
            f.write(file.read())

        # Initialize Word application
        word = win32.Dispatch("Word.Application")
        word.Visible = False

        # Open the .doc file using the absolute path
        doc = word.Documents.Open(temp_doc_path)

        # Extract the text from the document
        full_text = doc.Content.Text

        # Close the document
        doc.Close(False)
        word.Quit()

        # Delete the temporary file
        os.remove(temp_doc_path)

        return full_text

    except Exception as e:
        st.error(f"Error occurred while extracting text: {e}")
        return None

# Function to process and extract the structured table data from the text
# Function to process and extract the structured table data from the text
def process_structured_data_with_product_names(text):
    lines = text.splitlines()

    # Regular expression to match rows with customer name, pin, qty, and amounts
    row_pattern = re.compile(r"([A-Za-z\s.]+)\s+(\d{6})\s+(-?\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)")

    # Define the stockist name
    stockist_name = "LIFECARE PHARMA PRIVATE LIMITED"

    # List to hold the extracted data
    data = []
    current_product_name = None
    next_line_is_product = False

    for line in lines:
        line = line.strip()

        # Check for the hyphen separator line
        if line.startswith('---'):
            next_line_is_product = True  # The next line is the product name
            continue

        # If the next line is product name, store it and reset the flag
        if next_line_is_product:
            current_product_name = line
            next_line_is_product = False
            continue

        # Check if the line matches the row pattern
        match = row_pattern.match(line)

        if match:
            # Extract row details and append the current product name and stockist name
            customer_name, pin, qty, gross_amt, net_amt = match.groups()
            data.append({
                "Stockist Name": stockist_name,  # Add stockist name to each row
                "Product Name": current_product_name,
                "Customer Name": customer_name.strip(),
                "Pin": pin.strip(),
                "Qty": int(qty),
                "Gross Amt": float(gross_amt),
                "Net Amt": float(net_amt)
            })

    # Convert the list to a DataFrame
    df = pd.DataFrame(data)
    
    return df
    lines = text.splitlines()

    # Regular expression to match rows with customer name, pin, qty, and amounts
    row_pattern = re.compile(r"([A-Za-z\s.]+)\s+(\d{6})\s+(-?\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)")
    
    # List to hold the extracted data
    data = []
    current_product_name = None
    next_line_is_product = False

    for line in lines:
        line = line.strip()

        # Check for the hyphen separator line
        if line.startswith('---'):
            next_line_is_product = True  # The next line is the product name
            continue

        # If the next line is product name, store it and reset the flag
        if next_line_is_product:
            current_product_name = line
            next_line_is_product = False
            continue

        # Check if the line matches the row pattern
        match = row_pattern.match(line)

        if match:
            # Extract row details and append the current product name to it
            customer_name, pin, qty, gross_amt, net_amt = match.groups()
            data.append({
                "Product Name": current_product_name,
                "Customer Name": customer_name.strip(),
                "Pin": pin.strip(),
                "Qty": int(qty),
                "Gross Amt": float(gross_amt),
                "Net Amt": float(net_amt)
            })

    # Convert the list to a DataFrame
    df = pd.DataFrame(data)
    
    return df

# Function to insert extracted data into MySQL database
def insert_data_into_db(df):
    try:
        # Establish a database connection
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # SQL insert query with dummy text for missing columns
        insert_query = """
        INSERT INTO salesdata (
            Stockist_Code, Stockist_Name, Bill_No, Bill_Date, 
            Chemist_Code, Chemist_Name, Address, City, 
            Pin_Code, Material_Code, Material_Name, Batch_No, 
            Sale_Qty, Free_Qty, Rate, Value
        )
        VALUES (
            %s, %s, %s, CURDATE(), 
            %s, %s, %s, %s, 
            %s, %s, %s, %s, 
            %s, %s, %s, %s
        )
        """

        for index, row in df.iterrows():
            values = (
                'CODE',           # Stockist_Code
                row['Stockist Name'],    # Stockist_Name
                'BILL_NO',         # Bill_No
                'CHEMIST_CODE',    # Chemist_Code
                row['Customer Name'],    # Chemist_Name
                'ADDRESS',         # Address
                'CITY',            # City
                row['Pin'],              # Pin_Code
                'MATERIAL_CODE',   # Material_Code
                row['Product Name'],     # Material_Name
                'BATCH_NO',        # Batch_No
                row['Qty'],              # Sale_Qty
                0,                       # Free_Qty
                row['Gross Amt'],        # Rate (Gross Amt)
                row['Net Amt'],          # Value (Net Amt)
            )

            cursor.execute(insert_query, values)

        # Commit the transaction
        connection.commit()
        st.success("All data has been successfully inserted into the database.")
        
    except mysql.connector.Error as err:
        st.error(f"Error inserting data into MySQL: {err}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()