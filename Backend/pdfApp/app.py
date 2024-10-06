import streamlit as st
import pandas as pd
import re
from pdfDb import insert_into_mysql,connect_to_mysql
from pdfModules import *

# Streamlit app UI
st.title("PDF Text Extractor and Table Rebuilder")

# File uploader for PDF
pdf_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if pdf_file is not None:
    st.write("Extracting text and rebuilding table...")

    # Extract text and build a table
    table, product_info = extract_text_and_build_table(pdf_file)

    # Remove the first 8 rows
    if table is not None and not table.empty:
        table = table.iloc[9:]  # Slicing to remove the first 8 rows

        # Define the headers to look for
        desired_headers = [
            "S.No", "BillNo/Date", "Pharmacy", 
            "City", "Batch", "Expiry", "Qty", 
            "Free", "Rpl", "PTS", "PTR", 
            "MRP", "TotSales"
        ]

        # Mark rows based on specified headers
        marked_table = mark_rows_with_headers(table.reset_index(drop=True), desired_headers)
        
        # Merge pharmacy names into a single cell
        merged_table = merge_pharmacy_names(marked_table)
        
        # Populate the current row with data from the row below
        populated_table = populate_with_below_row_data(merged_table)
        
        # Shift non-empty values into None or empty cells
        final_table = shift_non_empty_values(populated_table)
        
        # Separate text and digits from Below Col1 and Below Col2
        separated_table = separate_text_and_digits(final_table)

        # Concatenate Digits into the sixth column
        final_table_with_digits = concatenate_digits_with_sixth_column(separated_table)

        # Concatenate Text into the third column
        final_table_with_text = concatenate_text_with_third_column(final_table_with_digits)

        # Remove rows with more than 7 False values
        cleaned_table = remove_rows_with_too_many_falsy_values(final_table_with_text)
        
        new_data = pd.DataFrame(cleaned_table.iloc[:, :14])
        new_data.columns = [
            "S.No", "Bill No", "Bill Date", "Pharmacy", 
            "City", "Batch", "Expiry", "Qty", 
            "Free", "Rpl", "PTS", "PTR", 
            "MRP", "TotSales"
        ]
        fin = new_data.drop_duplicates()
        fin['City Name'] = fin['City'].str.extract(r'([A-Za-z\s]+)(\d{1,6})')[0].str.strip()  # City name part
        fin['Pincode'] = fin['City'].str.extract(r'([A-Za-z\s]+)(\d{1,6})')[1] 
        fin['Batch'] = fin['Batch'].str.replace(" ", "", regex=False)
        fin['Batch'] = fin['Batch'].str.replace(".", "", regex=False)        
        fin = fin.drop("City", axis=1)
        final = fin.dropna()
        final['Bill No'] = pd.to_numeric(final['Bill No'], errors='coerce')

        # Filter out rows where 'Batch' is less than 2000 or NaN
        final = final[final['Bill No'] >= 2000]


        # Assign product names to rows
        final = assign_product_names(final, product_info)

        # Display the extracted product information
        st.write("Extracted Product Information:")
        if product_info:
            product_df = pd.DataFrame(product_info)
            # st.dataframe(product_df)

        # st.write(len(final))
        st.dataframe(final)
    if st.button('Insert into MySQL'):
    # Connect to MySQL
        connection = connect_to_mysql()

        if connection:
                try:
                    # Insert data into MySQL
                    insert_into_mysql(final, connection)
                except Exception as e:
                    st.write(f"Error: {e}")
                finally:
                    connection.close()
        else:
                st.write("Failed to connect to the database.")
    else:
        st.write("No table found or rebuilt from text.")