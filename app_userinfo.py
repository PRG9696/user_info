import streamlit as st
import pandas as pd
import io

# --- Page Config ---
st.set_page_config(
    page_title="Multi-Sheet Excel Comparison Tool",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Multi-Sheet Excel Comparison Tool")
st.markdown("Upload two Excel files to identify missing sheets, missing columns, and missing/different rows.")

# --- File Uploader Sidebar ---
st.sidebar.header("📁 Upload Files")
file1 = st.sidebar.file_uploader("Upload File 1 (Base File)", type=["xlsx", "xls"], key="file1")
file2 = st.sidebar.file_uploader("Upload File 2 (Comparison File)", type=["xlsx", "xls"], key="file2")

if file1 and file2:
    try:
        # Load Excel files
        xls1 = pd.ExcelFile(file1)
        xls2 = pd.ExcelFile(file2)

        sheets1 = set(xls1.sheet_names)
        sheets2 = set(xls2.sheet_names)

        st.subheader("📋 1. Sheet Availability Summary")
        
        col1, col2, col3 = st.columns(3)
        common_sheets = sorted(list(sheets1.intersection(sheets2)))
        missing_in_file2 = sorted(list(sheets1 - sheets2))
        missing_in_file1 = sorted(list(sheets2 - sheets1))

        col1.metric("Common Sheets", len(common_sheets))
        col2.metric("Missing in File 2", len(missing_in_file2))
        col3.metric("Missing in File 1", len(missing_in_file1))

        # Show missing sheet alerts
        if missing_in_file2:
            st.warning(f"⚠️ **Sheets present in File 1 but MISSING in File 2:** {', '.join(missing_in_file2)}")
        if missing_in_file1:
            st.warning(f"⚠️ **Sheets present in File 2 but MISSING in File 1:** {', '.join(missing_in_file1)}")

        if not common_sheets:
            st.error("No matching sheet names found between the two files to compare content.")
        else:
            st.divider()
            st.subheader("🔬 2. Detailed Sheet Comparison")

            # Dropdown to select matching sheet
            selected_sheet = st.selectbox("Select a sheet to compare:", common_sheets)

            # Read selected sheets into dataframes
            df1 = pd.read_excel(xls1, sheet_name=selected_sheet)
            df2 = pd.read_excel(xls2, sheet_name=selected_sheet)

            st.write(f"**Selected Sheet:** `{selected_sheet}`")
            c_info1, c_info2 = st.columns(2)
            c_info1.info(f"**File 1 Shape:** {df1.shape[0]} rows × {df1.shape[1]} columns")
            c_info2.info(f"**File 2 Shape:** {df2.shape[0]} rows × {df2.shape[1]} columns")

            # Check Column differences
            cols1 = set(df1.columns)
            cols2 = set(df2.columns)
            missing_cols_in_2 = cols1 - cols2
            missing_cols_in_1 = cols2 - cols1

            if missing_cols_in_2:
                st.error(f"Columns missing in File 2 (`{selected_sheet}`): {list(missing_cols_in_2)}")
            if missing_cols_in_1:
                st.error(f"Columns missing in File 1 (`{selected_sheet}`): {list(missing_cols_in_1)}")

            # Row Comparison Strategy
            st.subheader("🔎 Row Comparison Settings")
            common_cols = list(cols1.intersection(cols2))

            if not common_cols:
                st.error("No matching columns to compare rows.")
            else:
                key_col = st.selectbox(
                    "Select Unique Identifier / Key Column (e.g., ID, SKU, Email):", 
                    options=["-- Compare Full Rows --"] + common_cols,
                    help="Select a column with unique values to match records across files."
                )

                if key_col != "-- Compare Full Rows --":
                    # Key-based comparison
                    df1_clean = df1.dropna(subset=[key_col])
                    df2_clean = df2.dropna(subset=[key_col])

                    keys1 = set(df1_clean[key_col])
                    keys2 = set(df2_clean[key_col])

                    missing_keys_in_2 = keys1 - keys2
                    missing_keys_in_1 = keys2 - keys1

                    r_col1, r_col2 = st.columns(2)

                    with r_col1:
                        st.markdown(f"### ❌ Records in File 1 but MISSING in File 2 ({len(missing_keys_in_2)})")
                        df_missing_2 = df1_clean[df1_clean[key_col].isin(missing_keys_in_2)]
                        st.dataframe(df_missing_2, use_container_width=True, hide_index=True)

                    with r_col2:
                        st.markdown(f"### ❌ Records in File 2 but MISSING in File 1 ({len(missing_keys_in_1)})")
                        df_missing_1 = df2_clean[df2_clean[key_col].isin(missing_keys_in_1)]
                        st.dataframe(df_missing_1, use_container_width=True, hide_index=True)

                else:
                    # Full row comparison
                    merged = pd.merge(df1[common_cols], df2[common_cols], how='outer', indicator=True)
                    
                    in_file1_only = merged[merged['_merge'] == 'left_only'].drop(columns=['_merge'])
                    in_file2_only = merged[merged['_merge'] == 'right_only'].drop(columns=['_merge'])

                    r_col1, r_col2 = st.columns(2)
                    with r_col1:
                        st.markdown(f"### Rows in File 1 only ({len(in_file1_only)})")
                        st.dataframe(in_file1_only, use_container_width=True, hide_index=True)

                    with r_col2:
                        st.markdown(f"### Rows in File 2 only ({len(in_file2_only)})")
                        st.dataframe(in_file2_only, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error processing files: {e}")

else:
    st.info("👆 Please upload **File 1** and **File 2** using the sidebar to begin comparison.")
