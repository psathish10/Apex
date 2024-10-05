import streamlit as st
import pdfplumber
import pandas as pd
import re
import mysql.connector

# Define your SQL database connection details
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'apex'
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

    # Handle "BillNo/Date" split
    if "BillNo/Date" in df.columns:
        # Check if the split operation is successful
        split_columns = df['BillNo/Date'].str.split('/', n=1, expand=True)
        if split_columns.shape[1] == 2:
            df['Bill No'] = split_columns[0].str.strip()
            df['Bill Date'] = split_columns[1].str.strip()
        else:
            df['Bill No'] = None
            df['Bill Date'] = None

    df = df.drop(columns=['BillNo/Date'], errors='ignore')

    # Separate City and Pin Code
    if "City" in df.columns:
        df[['City', 'Pin Code']] = df['City'].str.extract(r'([A-Za-z\s]+)(\d{4,6})$')

    # Check if "Bill No" exists before applying any filters
    if "Bill No" in df.columns:
        df['Bill No'] = pd.to_numeric(df['Bill No'], errors='coerce')  # Convert to numeric, errors to NaN
        removed_df = df[df['Bill No'] < 2000]  # Filter rows where 'Bill No' < 2000
        df = df[df['Bill No'] >= 2000]  # Keep rows where 'Bill No' >= 2000
    else:
        removed_df = pd.DataFrame()  # No rows to remove if 'Bill No' is missing

    return df, removed_df



def associate_product_names(df, product_list):
    result = []
    product_index = 0  # Index for accessing product names
    product_count = len(product_list)

    for _, row in df.iterrows():
        # Check if S.No starts from 1 to assign a new product
        if pd.notna(row['S.No']) and int(row['S.No']) == 1 and product_index < product_count:
            # Assign the next product name and ID
            product_id, product_name = product_list[product_index]
            row['Product ID'] = product_id
            row['Product Name'] = product_name
            product_index += 1  # Move to the next product name
        else:
            # Carry forward the last assigned product name and ID if S.No is not starting from 1
            if product_index > 0:
                row['Product ID'] = product_list[product_index - 1][0]
                row['Product Name'] = product_list[product_index - 1][1]
            else:
                row['Product ID'] = None
                row['Product Name'] = None  # No product name available yet

        result.append(row)

    return pd.DataFrame(result)

def extract_product_names():
    # Define product list with IDs and names
    product_list = [
        (1, "CLEAR UTI ORAL .. SUSP 100ML"),
        (2, "TRIFER .. SYRUP 150ML"),
        (3, "ZINCOVIT .. DROPS 15ML"),
        (4, "ZINCOVIT .. SYRUP 200ML"),
        (5, "ZINCOVIT .. TAB 15'S"),
        (6, "SOFINOX 10GM CREAM 10Gms"),
        (7, "LACNID .. TAB 10'S"),
        (8, "TRIFER .. DROPS 15ML"),
        (9, "TRIFER .. TAB 15'S"),
        (10, "SOFINOX 5GM CREAM 1'S"),
        (11, "ZINCOVIT CL .. SYRUP 200ML"),
        (12, "DOCOWIZE VEG 100ML SUSP 1'S"),
        (13, "DOCOWIZE PLUS .. CAP 10'S"),
        (14, "NEUROZIN .. CAP 10'S"),
        (15, "ZINCOVIT W .. TAB 10'S"),
        (16, "TRIFER XT .. TAB 10'S"),
        (17, "ZINCOVIT ACTIVE APPLE .. LIQ 200ML"),
        (18, "ZINCOVIT ACTIVE ORANGE .. LIQ 200ML"),
        (19, "ZINCOVIT CD .. TAB 10'S"),
        (20, "CRESVIN BETA .. CAP 1'S")
    ]
    return product_list

def extract_and_combine_tables(pdf_file):
    global combined_df
    combined_df = pd.DataFrame()  # Reset combined DataFrame
    product_list = extract_product_names()

    try:
        with pdfplumber.open(pdf_file) as pdf:
            removed_data = pd.DataFrame()  # To store removed rows
            for page in pdf.pages:
                extracted_tables = page.extract_tables()
                for table in extracted_tables:
                    df, removed_df = clean_and_fix_columns(table)  # Capture both cleaned and removed data
                    if not df.empty:
                        combined_df = pd.concat([combined_df, df], ignore_index=True)
                    if not removed_df.empty:
                        removed_data = pd.concat([removed_data, removed_df], ignore_index=True)

        if not combined_df.empty:
            combined_df = associate_product_names(combined_df, product_list)
            st.write("Combined table from all pages with associated product names and IDs (based on S.No):")
            st.dataframe(combined_df)
        else:
            st.write("No valid data found in the PDF tables.")

        if not removed_data.empty:
            st.write("The following rows were removed because 'Bill No' was less than 2000:")
            st.dataframe(removed_data)

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
                row['Product ID'] if pd.notna(row['Product ID']) else None,  # Assign product ID here
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
    st.title("Apex Lab's PDF Data Extractor")

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
