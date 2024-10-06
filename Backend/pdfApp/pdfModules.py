
import pdfplumber
import pandas as pd
import re
# Function to extract text and process it into table format
def extract_text_and_build_table(pdf_file):
    table_data = []
    product_info = []  # List to store product names and serial numbers

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                rows = text.split("\n")  # Split lines based on newlines
                for row in rows:
                    columns = row.split()  # Adjust splitting logic based on table structure
                    
                    # Loop to remove cells containing "/" and shift cells
                    cleaned_columns = []
                    for col in columns:
                        if "/" not in col:  # If "/" is not in the column
                            cleaned_columns.append(col)
                    
                    if cleaned_columns:  # Ensure cleaned_columns is not empty
                        table_data.append(cleaned_columns)

            # Extract product names and serial numbers from the current page
            product_info.extend(extract_product_info(page))

    if table_data:
        return pd.DataFrame(table_data), product_info
    else:
        return None, None
    

    # Function to extract product name and serial number from PDF
def extract_product_info(page):
    text = page.extract_text()
    product_info_list = []
    
    # Regex to capture the format "S.No. Product Name : Product Name"
    pattern = r"(\d+)\s*\.\s*Product Name\s*:\s*(.*)"

    matches = re.findall(pattern, text)
    
    for match in matches:
        s_no = match[0].strip()  # Serial number
        product_name = match[1].strip()  # Product name
        product_info_list.append({"S.No": s_no, "Product Name": product_name})

    return product_info_list



# Function to add a column indicating whether rows contain specified headers
def mark_rows_with_headers(df, headers):
    mask = df.apply(lambda row: any(header in str(cell) for cell in row for header in headers), axis=1)
    df['Contains Headers'] = mask
    return df

# Function to merge pharmacy names into a single cell and adjust neighboring cells
def merge_pharmacy_names(df):
    date_col_index = 2  # Assuming 0-based index for the date column
    pharmacy_start_index = 3  # Pharmacy name starts at index 3
    city_col_index = -1  # Assuming city/pincode is in the last column

    for i in range(len(df)):
        if i < len(df) - 1:  # Check if not the last row
            try:
                # Parse the date to check if the row is valid (skip if parsing fails)
                pd.to_datetime(df.iloc[i, date_col_index], errors='raise')

                # Initialize a list to store pharmacy name parts
                pharmacy_name_parts = []

                # Loop through the columns starting from the pharmacy name, up to (but not including) the city/pincode
                for j in range(pharmacy_start_index, len(df.columns) - 1):
                    cell_value = str(df.iloc[i, j])

                    # Check if the current cell contains the city or pincode (e.g., starts with "CHENGALPATTU" or "CHENNAI")
                    if cell_value.startswith("CHENGALPATTU") or cell_value.startswith("CHENNAI") or cell_value.startswith("KANCHIPURAM"):
                        # Move the city/pincode to the last column
                        df.at[i, city_col_index] = cell_value
                        break  # Stop merging after city/pincode is encountered

                    # Add valid non-empty pharmacy name parts to the list
                    if cell_value and cell_value != 'None':
                        pharmacy_name_parts.append(cell_value)

                # Merge the collected pharmacy name parts into a single string
                merged_pharmacy_name = " ".join(pharmacy_name_parts)
                
                # Update the first pharmacy-related column with the merged name
                df.at[i, pharmacy_start_index] = merged_pharmacy_name

                # Clear the remaining pharmacy name columns, but leave other columns untouched
                for j in range(pharmacy_start_index + 1, pharmacy_start_index + len(pharmacy_name_parts)):
                    df.at[i, j] = None  # Clear merged cells

            except Exception as e:
                # Skip rows where date parsing fails
                continue

    return df

# Function to populate current row with data from the row below
def populate_with_below_row_data(df):
    below_cols = ['Below_Col1', 'Below_Col2', 'Below_Col3']  # Define the new column names
    for col in below_cols:
        df[col] = None

    for i in range(len(df) - 1):
        below_row = df.iloc[i + 1]

        # Count non-empty cells in the below row
        non_empty_count = below_row.count() - below_row.isna().sum()  # Total cells - NaN cells

        # Only populate if the count of non-empty cells is 2 or fewer
        if non_empty_count <= 2:
            for j, col in enumerate(below_cols):
                value = below_row[j] if j < len(below_row) and pd.notna(below_row[j]) and str(below_row[j]).strip() != "" else None
                if value is not None:
                    df.at[i, col] = value

    return df

# Function to shift next non-empty values into None or empty cells
def shift_non_empty_values(df):
    for i in range(len(df)):
        for j in range(len(df.columns) - 1):  # Exclude the last column
            if pd.isna(df.iloc[i, j]) or str(df.iloc[i, j]).strip() == "":
                for k in range(j + 1, len(df.columns)):
                    if pd.notna(df.iloc[i, k]) and str(df.iloc[i, k]).strip() != "":
                        df.at[i, j] = df.iloc[i, k]
                        df.at[i, k] = None  # Set the shifted cell to None
                        break  # Break out of the inner loop once shifted

    return df

# Function to separate text and digits from Below Col1 and Below Col2
def separate_text_and_digits(df):
    df['Text'] = None
    df['Digits'] = None

    for i in range(len(df)):
        below_col1 = df.at[i, 'Below_Col1']
        below_col2 = df.at[i, 'Below_Col2']

        if pd.notna(below_col1):
            if str(below_col1).isdigit() and len(str(below_col1)) <= 3:  # If it's digits and has 3 or fewer digits
                df.at[i, 'Digits'] = below_col1
            else:  # It's text
                df.at[i, 'Text'] = below_col1

        if pd.notna(below_col2):
            if str(below_col2).isdigit() and len(str(below_col2)) <= 3:  # If it's digits and has 3 or fewer digits
                df.at[i, 'Digits'] = below_col2  # Overwrite if digits
            else:  # It's text
                if pd.isna(df.at[i, 'Text']):  # Only assign if text is empty
                    df.at[i, 'Text'] = below_col2

    return df

# Function to concatenate Digits into the sixth column
def concatenate_digits_with_sixth_column(df):
    sixth_col_index = 5  # Sixth column is at index 5
    for i in range(len(df)):
        if pd.notna(df.at[i, 'Digits']):
            current_value = df.iloc[i, sixth_col_index] if sixth_col_index < len(df.columns) else ''
            df.iloc[i, sixth_col_index] = f"{current_value} {df.at[i, 'Digits']}".strip()  # Concatenate the digits

    return df

# Function to concatenate Text into the third column
def concatenate_text_with_third_column(df):
    third_col_index = 3  # Third column is at index 2
    for i in range(len(df)):
        if pd.notna(df.at[i, 'Text']):
            current_value = df.iloc[i, third_col_index] if third_col_index < len(df.columns) else ''
            df.iloc[i, third_col_index] = f"{current_value} {df.at[i, 'Text']}".strip()  # Concatenate the text

    return df

# Function to remove rows with more than a specified number of False values
def remove_rows_with_too_many_falsy_values(df, threshold=7):
    # Count the number of False values in each row
    falsy_count = (df == False).sum(axis=1)  # Count cells that are False
    # Keep only rows where the count of False values is less than or equal to the threshold
    df_filtered = df[falsy_count <= threshold]
    return df_filtered

# New function to assign product names to rows
def assign_product_names(df, product_info):
    product_index = 0
    current_product = product_info[product_index]['Product Name'] if product_info else None
    df['Product Name'] = ''

    for i, row in df.iterrows():
        if pd.notna(row['S.No']) and str(row['S.No']).strip() == '1':
            if product_index < len(product_info):
                current_product = product_info[product_index]['Product Name']
                product_index += 1
        
        df.at[i, 'Product Name'] = current_product

    return df

