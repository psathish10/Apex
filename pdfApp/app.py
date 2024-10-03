import streamlit as st
import pdfplumber
import pandas as pd
import re
import mysql.connector
import datetime

# Define your SQL database connection details
DB_CONFIG = {
                        'host': 'srv1508.hstgr.io',
                        'user': 'u840048117_Apex_demo',
                        'password': 'Toolfe@min10!',
                        'database': 'u840048117_Apex_demo'
                    }

# Define the fixed column names based on your provided table structure
FIXED_COLUMNS = [
    "S.No", "BillNo/Date", "Pharmacy Name", "City", "Batch", "Expiry", "Qty", 
    "Free", "Rpl", "PTS", "PTR", "MRP", "TotSales"
]

# Global variable to hold combined DataFrame
combined_df = pd.DataFrame()

def clean_and_fix_columns(data):
    df = pd.DataFrame(data)
    
    if len(df.columns) != len(FIXED_COLUMNS):
        df = df.iloc[:, :len(FIXED_COLUMNS)]
        df.columns = FIXED_COLUMNS[:len(df.columns)]
    else:
        df.columns = FIXED_COLUMNS
    
    df = df[~df.apply(lambda row: row.tolist() == FIXED_COLUMNS, axis=1)]
    df = df.dropna(how='any')
    df = df[df.apply(lambda row: all(row.astype(str).str.strip() != ''), axis=1)]
    df = df[~df.apply(lambda row: "Pharmacy Name" in row.values, axis=1)]
    
    if "BillNo/Date" in df.columns:
        df[['Bill No', 'Bill Date']] = df['BillNo/Date'].str.split('/', n=1, expand=True)
        df['Bill Date'] = df['Bill Date'].str.strip()
        df['Bill No'] = df['Bill No'].str.strip()
    
        


    df = df.drop(columns=['BillNo/Date'], errors='ignore')

    # Separate City and Pin Code
    if "City" in df.columns:
        df[['City', 'Pin Code']] = df['City'].str.extract(r'([A-Za-z\s]+)(\d{4,6})$')
    
    return df

def associate_product_names_by_batch(df, product_names):
    result = []
    current_product = None
    current_batch_prefix = None

    for _, row in df.iterrows():
        batch = str(row['Batch'])
        batch_prefix = batch[:3] if len(batch) >= 3 else batch

        if batch_prefix != current_batch_prefix:
            if product_names:
                current_product = product_names.pop(0)
            else:
                current_product = "Unknown Product"
            current_batch_prefix = batch_prefix

        row['Product Name'] = current_product
        result.append(row)

    return pd.DataFrame(result)

def extract_product_name(page):
    text = page.extract_text()
    match = re.search(r"Product Name\s*:\s*(.*)", text)
    return match.group(1).strip() if match else None

def extract_and_combine_tables(pdf_file):
    global combined_df
    combined_df = pd.DataFrame()  # Reset combined DataFrame
    product_names = []

    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                product_name = extract_product_name(page)
                if product_name:
                    product_names.append(product_name)
                
                extracted_tables = page.extract_tables()
                for table in extracted_tables:
                    df = clean_and_fix_columns(table)
                    if not df.empty:
                        combined_df = pd.concat([combined_df, df], ignore_index=True)

        if not combined_df.empty:
            combined_df = associate_product_names_by_batch(combined_df, product_names)
            st.write("Combined table from all pages with associated product names (based on Batch):")
            st.dataframe(combined_df)
        else:
            st.write("No valid data found in the PDF tables.")
    
    except Exception as e:
        st.error(f"Error occurred while extracting tables: {str(e)}")
        st.write("Please check if the PDF contains the expected table structure.")

def push_to_database():
    try:
        # Establish database connection
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Define your SQL insert statement
        insert_query = """
        INSERT INTO salesdata (Stockist_Code, Stockist_Name, Bill_No, Bill_Date, Chemist_Code,
                                       Chemist_Name, Address, City, Pin_Code, Material_Code, 
                                       Material_Name, Batch_No, Sale_Qty, Free_Qty, Rate, Value)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Iterate through the DataFrame and insert each row into the database
        for index, row in combined_df.iterrows():
            # Convert 'Bill Date' to 'yyyy-mm-dd' format
            bill_date = pd.to_datetime(row['Bill Date'], format='%d-%m-%Y', errors='coerce')
            bill_date_str = bill_date.strftime('%Y-%m-%d') if pd.notna(bill_date) else None

            data = (
                row['S.No'] if pd.notna(row['S.No']) else None,  # Assuming this corresponds to Stockist_Code
                row['Pharmacy Name'] if pd.notna(row['Pharmacy Name']) else None,  # Stockist Name
                row['Bill No'] if pd.notna(row['Bill No']) else None,
                bill_date_str,  # Use the formatted Bill Date here
                "Chemist Code",  # Replace with the actual Chemist Code
                "Chemist Name",  # Replace with the actual Chemist Name
                "Address",  # Replace with the actual Address
                row['City'] if pd.notna(row['City']) else None,
                row['Pin Code'] if pd.notna(row['Pin Code']) else None,
                "Material Code",  # Replace with the actual Material Code
                row['Product Name'] if pd.notna(row['Product Name']) else None,
                row['Batch'] if pd.notna(row['Batch']) else None,
                row['Qty'] if pd.notna(row['Qty']) else None,  # Assuming Sale_Qty corresponds to Qty
                row['Free'] if pd.notna(row['Free']) else None,  # Assuming Free_Qty corresponds to Free
                row['PTR'] if pd.notna(row['PTR']) else None,  # Rate mapped to PTR
                row['TotSales'] if pd.notna(row['TotSales']) else None  # Value mapped to TotSales
            )
            cursor.execute(insert_query, data)

        # Commit the transaction
        connection.commit()
        st.success("Data has been successfully inserted into the database.")

    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def main():
    st.title("Apex Lab's")
    pdf_file = st.file_uploader("Upload a PDF file", type=["pdf"])

    if pdf_file is not None:
        st.write("Processing the uploaded PDF...")
        extract_and_combine_tables(pdf_file)

        # Add a button to push data to the database
        if st.button("Insert Data into Database"):
            if not combined_df.empty:
                push_to_database()
            else:
                st.warning("No data to insert. Please ensure the PDF contains valid tables.")

if __name__ == "__main__":
    main()
