import streamlit as st
import pandas as pd
import re
from pdfDb import insert_into_mysql, connect_to_mysql
from pdfModules import *
from excel_module import extract_excel_tables, insert_excel_data_into_mysql
from word_module import extract_text_from_doc, process_structured_data_with_product_names, insert_word_data_into_db

def pdf_processor(pdf_file):
    st.write("Processing PDF file...")
    table, product_info = extract_text_and_build_table(pdf_file)
    
    if table is not None and not table.empty:
        table = table.iloc[9:]
        desired_headers = [
            "S.No", "BillNo/Date", "Pharmacy", 
            "City", "Batch", "Expiry", "Qty", 
            "Free", "Rpl", "PTS", "PTR", 
            "MRP", "TotSales"
        ]
        marked_table = mark_rows_with_headers(table.reset_index(drop=True), desired_headers)
        merged_table = merge_pharmacy_names(marked_table)
        populated_table = populate_with_below_row_data(merged_table)
        final_table = shift_non_empty_values(populated_table)
        separated_table = separate_text_and_digits(final_table)
        final_table_with_digits = concatenate_digits_with_sixth_column(separated_table)
        final_table_with_text = concatenate_text_with_third_column(final_table_with_digits)
        cleaned_table = remove_rows_with_too_many_falsy_values(final_table_with_text)
        
        new_data = pd.DataFrame(cleaned_table.iloc[:, :14])
        new_data.columns = [
            "S.No", "Bill No", "Bill Date", "Pharmacy", 
            "City", "Batch", "Expiry", "Qty", 
            "Free", "Rpl", "PTS", "PTR", 
            "MRP", "TotSales"
        ]
        fin = new_data.drop_duplicates()
        fin['City Name'] = fin['City'].str.extract(r'([A-Za-z\s]+)(\d{1,6})')[0].str.strip()
        fin['Pincode'] = fin['City'].str.extract(r'([A-Za-z\s]+)(\d{1,6})')[1] 
        fin['Batch'] = fin['Batch'].str.replace(" ", "", regex=False)
        fin['Batch'] = fin['Batch'].str.replace(".", "", regex=False)        
        fin = fin.drop("City", axis=1)
        final = fin.dropna()
        final['Bill No'] = pd.to_numeric(final['Bill No'], errors='coerce')
        final = final[final['Bill No'] >= 2000]
        final = assign_product_names(final, product_info)

        st.write("Extracted Product Information:")
        if product_info:
            product_df = pd.DataFrame(product_info)
        
        st.dataframe(final)

        if st.button('Insert PDF Data into MySQL'):
            connection = connect_to_mysql()
            if connection:
                try:
                    insert_into_mysql(final, connection)
                    st.success("PDF data successfully inserted into MySQL!")
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    connection.close()
            else:
                st.error("Failed to connect to the database.")
    else:
        st.error("No table found or rebuilt from text.")

def excel_processor(file):
    st.write("Processing Excel file...")
    df = extract_excel_tables(file)
    if df is not None:
        st.write("Extracted Table:")
        st.dataframe(df)

        if st.button("Insert Excel Data into MySQL"):
            insert_excel_data_into_mysql(df)

def word_processor(uploaded_file):
    st.write("Processing Word file...")
    extracted_text = extract_text_from_doc(uploaded_file)
    
    if extracted_text:
        df = process_structured_data_with_product_names(extracted_text)
        
        st.write("Extracted Table with Product Names:")
        st.dataframe(df)

        if st.button("Insert Word Data into Database"):
            insert_word_data_into_db(df)

def main():
    st.title("Combined Data Processing Application")
    
    uploaded_file = st.file_uploader("Upload your file", type=["pdf", "xlsx", "doc"])
    
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        
        if file_extension == "pdf":
            pdf_processor(uploaded_file)
        elif file_extension == "xlsx":
            excel_processor(uploaded_file)
        elif file_extension == "doc":
            word_processor(uploaded_file)
        else:
            st.error("Unsupported file type. Please upload a PDF, Excel, or Word file.")

if __name__ == "__main__":
    main()