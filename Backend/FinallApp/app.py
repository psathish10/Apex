import streamlit as st
import pandas as pd
import re
from pdfDb import insert_into_mysql, connect_to_mysql
from pdfModules import *
from excel_module import extract_excel_tables, insert_excel_data_into_mysql
from word_module import extract_text_from_doc, process_structured_data_with_product_names, insert_word_data_into_db
import base64



# Set page configuration
st.set_page_config(page_title="Data Processing App", page_icon="📊", layout="wide")

# Custom CSS for the entire app and the sidebar
st.markdown("""
<style>
    .stApp {
        background-color: black;
    }
    .stSidebar {
        background-color: #01071A;
        color: white;
    }
    .stSidebar .sidebar-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding-top: 20px;
    }
    .sidebar-content img {
        border-radius: 50%;
        width: 100px;
        margin-bottom: 20px;
    }
    .main {
        background-color: black;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .stButton>button {
        background-color: #ff4d4d;
        color: white !important;
        border-radius: 5px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
    
    }
   
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #01071A;
        color: white;
        text-align: center;
        padding: 10px 0;
    }
    h1, h2, h3,h4 {
        color: white;
        text-align: center;
        position: sticky;
        top: 0;
        background-color: black;
        padding: 10px;
        z-index: 100;
        margin-bottom: 10px;
        width: 100%;
    }
    .admin-link {
        position: left;
        right: 10px;
      
        color: white !important;
        padding: 10px 20px;
        border-radius: 5px;
        border: 1px solid white;
        font-weight: bold;
        text-align: center;
        text-decoration: none;
        transition: background-color 0.3s;
    }
   
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th {
        background-color: #d3d3d3;
        color: black;
        text-align: center;
        padding: 10px;
        border: 1px solid #a0a0a0;
    }
    td {
        background-color: #f9f9f9;
        padding: 10px;
        border: 1px solid #a0a0a0;
    }
    .dataframe-container {
        display: flex;
        justify-content: center;
        width: 100%;
        overflow-x: auto;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Function to load and display the logo
def load_logo():
    with open("./Assert/A-icon.png", "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# PDF Processor
def pdf_processor(pdf_file):
    with st.spinner("Processing PDF file..."):
        table, product_info = extract_text_and_build_table(pdf_file)

    # Process the PDF data
    if table is not None and not table.empty:
        table = table.iloc[9:]  # Remove the first 8 rows
        
        # Define the headers to look for
        desired_headers = [
            "S.No", "BillNo/Date", "Pharmacy", 
            "City", "Batch", "Expiry", "Qty", 
            "Free", "Rpl", "PTS", "PTR", 
            "MRP", "TotSales"
        ]

        # Perform processing tasks (marking, merging, populating rows)
        marked_table = mark_rows_with_headers(table.reset_index(drop=True), desired_headers)
        merged_table = merge_pharmacy_names(marked_table)
        populated_table = populate_with_below_row_data(merged_table)
        final_table = shift_non_empty_values(populated_table)
        separated_table = separate_text_and_digits(final_table)
        final_table_with_digits = concatenate_digits_with_sixth_column(separated_table)
        final_table_with_text = concatenate_text_with_third_column(final_table_with_digits)
        cleaned_table = remove_rows_with_too_many_falsy_values(final_table_with_text)
        
        # Prepare final data for MySQL insertion
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

        # Filter rows where 'Bill No' is less than 2000
        final = final[final['Bill No'] >= 2000]

        # Assign product names
        final = assign_product_names(final, product_info)

        # Display the extracted product information
       

        if st.button('Insert PDF Data into MySQL', key='pdf_insert'):
            with st.spinner("Inserting data into MySQL..."):
                connection = connect_to_mysql()
                if connection:
                    try:
                        rows_inserted = insert_into_mysql(final, connection)
                        st.toast(f"🎉Successfully inserted 📄PDF file data!")
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        connection.close()
                else:
                    st.error("Failed to connect to the database.")
        
        # Display the final processed table
        st.dataframe(final)

# Excel Processor
def excel_processor(file):
    with st.spinner("Processing Excel file..."):
        df = extract_excel_tables(file)
    
    if df is not None:
        st.toast("🎉 Excel file processed successfully!📊")
        if st.button("Insert Excel Data into MySQL", key='excel_insert'):
            with st.spinner("Inserting data into MySQL..."):
                rows_inserted = insert_excel_data_into_mysql(df)
                st.toast(f"🎉 Successfully inserted 📊Excel file data!")

        st.dataframe(df)

# Word Processor
def word_processor(uploaded_file):
    with st.spinner("Processing Word file..."):
        extracted_text = extract_text_from_doc(uploaded_file)
    
    if extracted_text:
        df = process_structured_data_with_product_names(extracted_text)
        st.toast("🎉 Word file processed successfully!📘")
        if st.button("Insert Word Data into MySQL", key='word_insert'):
            with st.spinner("Inserting data into MySQL..."):
                rows_inserted = insert_word_data_into_db(df)
                st.toast(f"🎉 Successfully inserted 📘Word file data!")

        st.dataframe(df)

# Main Function
def main():
    # Sidebar configuration
    logo = load_logo()
    st.sidebar.markdown(f"<div class='sidebar-content'><img src='data:image/png;base64,{logo}'/><h2 style='color: white;'>📁 File Upload</h2></div>", unsafe_allow_html=True)
    uploaded_file = st.sidebar.file_uploader("Upload your file", type=["pdf", "xlsx", "doc"])
   
    # Title at the center
    st.markdown("""
    <h1 style='text-align: center;'>
        Apex <span style='color: red;'>x</span> Toolfe
    </h1>
    """, unsafe_allow_html=True)
    st.sidebar.markdown("""<a href='http://localhost/apex/Frontend/apexdemo/dashboard/' class="admin-link">Admin Panel</a>""", unsafe_allow_html=True)

    # Welcome message
    st.markdown("""
    <h4 style='color: white;'>Transform Documents into Actionable Data Instantly - Demo</h4>

    """, unsafe_allow_html=True)
    
    # File processing logic
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        st.info(f"Processing {file_extension.upper()} file: {uploaded_file.name}")
        
        if file_extension == "pdf":
            pdf_processor(uploaded_file)
        elif file_extension == "xlsx":
            excel_processor(uploaded_file)
        elif file_extension == "doc":
            word_processor(uploaded_file)
        else:
            st.error("Unsupported file type. Please upload a PDF, Excel, or Word file.")

    # Footer
    st.markdown("""
    <div class="footer" style='color':'#01071A'>
       Form Generator, apex laboratories Pvt. Ltd.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()