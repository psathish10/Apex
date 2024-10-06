import re
import platform
import pandas as pd
import os
import streamlit as st
import mysql.connector
import pythoncom

# Check platform
is_windows = platform.system() == "Windows"

if is_windows:
    import win32com.client as win32

# Define your SQL database connection details
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'apex'
}

def extract_text_from_doc(file):
    if is_windows:
        try:
            temp_doc_path = os.path.join(os.getcwd(), "temp.doc")
            with open(temp_doc_path, "wb") as f:
                f.write(file.read())

            # Initialize COM library
            pythoncom.CoInitialize()

            # Initialize Word application
            word = win32.Dispatch("Word.Application")
            word.Visible = False

            # Open the .doc file
            doc = word.Documents.Open(temp_doc_path)
            full_text = doc.Content.Text

            # Close the document
            doc.Close(False)
            word.Quit()

            # Uninitialize COM library
            pythoncom.CoUninitialize()

            # Delete the temporary file
            os.remove(temp_doc_path)

            return full_text

        except Exception as e:
            st.error(f"Error occurred while extracting text: {e}")
            return None
    else:
        st.error("This functionality is only available on Windows.")
        return None
# Function to process and extract structured data from the extracted text
def process_structured_data_with_product_names(text):
    lines = text.splitlines()

    # Regular expression to match rows with customer name, pin, qty, and amounts
    row_pattern = re.compile(r"([A-Za-z\s.]+)\s+(\d{6})\s+(-?\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)")
    
    stockist_name = "LIFECARE PHARMA PRIVATE LIMITED"
    data = []
    current_product_name = None
    next_line_is_product = False

    for line in lines:
        line = line.strip()

        # Check for separator lines (product names appear after "---" lines)
        if line.startswith('---'):
            next_line_is_product = True
            continue

        if next_line_is_product:
            current_product_name = line
            next_line_is_product = False
            continue

        # Extract rows that match the regular expression
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

# Function to insert extracted data into MySQL database
def insert_data_into_db(df):
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
                'CODE',  # Placeholder for Stockist_Code
                row['Stockist Name'],
                'BILL_NO',  # Placeholder for Bill_No
                'CHEMIST_CODE',  # Placeholder for Chemist_Code
                row['Customer Name'],
                'ADDRESS',  # Placeholder for Address
                'CITY',  # Placeholder for City
                row['Pin'],
                'MATERIAL_CODE',  # Placeholder for Material_Code
                row['Product Name'],
                'BATCH_NO',  # Placeholder for Batch_No
                row['Qty'],
                0,  # Free_Qty as default 0
                row['Gross Amt'],
                row['Net Amt'],
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

# Streamlit app to upload .doc file and process data
def main():
    st.title("Extract and Insert Table Data with Product Names into Database")

    uploaded_file = st.file_uploader("Upload a Microsoft Word 97-2003 Document (.doc)", type=["doc"])
    
    if uploaded_file:
        extracted_text = extract_text_from_doc(uploaded_file)
        
        if extracted_text:
            df = process_structured_data_with_product_names(extracted_text)
            
            st.write("Extracted Table with Product Names:")
            st.dataframe(df)

            if st.button("Insert Data into Database"):
                insert_data_into_db(df)

if __name__ == "__main__":
    main()
