import pandas as pd
import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="Custom Excel Comparison Tool", page_icon="🔍", layout="wide"
)

st.title("🔍 Excel Data Comparison Tool")
st.markdown("""
This app compares your uploaded files using the following rules:
- **Base File:** Looks at **Column B** across sheets ending in `*office` and named `academic`.
- **Comparison File:** Looks at **Column A** across sheets ending in `*sheet2`.
""")

# --- Sidebar Inputs ---
st.sidebar.header("📁 Upload Files")
base_file = st.sidebar.file_uploader(
    "Upload Base File", type=["xlsx", "xls"], key="base"
)
comp_file = st.sidebar.file_uploader(
    "Upload Comparison File", type=["xlsx", "xls"], key="comp"
)


def find_matching_sheets(xls_obj, pattern):
    """Finds all sheet names matching a pattern (case-insensitive, handles wildcards)."""
    pattern_clean = pattern.lower().replace("*", "")
    matched = []
    for sheet in xls_obj.sheet_names:
        if pattern.startswith("*"):
            if sheet.lower().endswith(pattern_clean):
                matched.append(sheet)
        elif pattern_clean in sheet.lower():
            matched.append(sheet)
    return matched


# --- Main Processing Logic ---
if base_file and comp_file:
    try:
        xls_base = pd.ExcelFile(base_file)
        xls_comp = pd.ExcelFile(comp_file)

        # 1. Identify Target Sheets in Base File (*office & academic)
        office_sheets = find_matching_sheets(xls_base, "*office")
        academic_sheets = [
            s for s in xls_base.sheet_names if s.lower() == "academic"
        ]
        base_sheets = office_sheets + academic_sheets

        # 2. Identify Target Sheets in Comparison File (*sheet2)
        comp_sheets = find_matching_sheets(xls_comp, "*sheet2")

        st.subheader("📋 Detected Target Sheets")
        col_b1, col_b2 = st.columns(2)

        with col_b1:
            st.info(
                f"**Base File Target Sheets:** {', '.join(base_sheets) if base_sheets else 'None found'}"
            )
        with col_b2:
            st.info(
                f"**Comparison File Target Sheets:** {', '.join(comp_sheets) if comp_sheets else 'None found'}"
            )

        if not base_sheets:
            st.error(
                "❌ Could not find any sheet ending with 'office' or named 'academic' in Base File."
            )
        elif not comp_sheets:
            st.error(
                "❌ Could not find any sheet ending with 'sheet2' in Comparison File."
            )
        else:
            # 3. Extract Column B values from Base File target sheets
            base_values = set()
            for sheet in base_sheets:
                df = pd.read_excel(xls_base, sheet_name=sheet, usecols=[1])
                if not df.empty:
                    base_values.update(df.iloc[:, 0].dropna().astype(str).str.strip().unique())

            # 4. Extract Column A values from Comparison File target sheets
            comp_values = set()
            for sheet in comp_sheets:
                df = pd.read_excel(xls_comp, sheet_name=sheet, usecols=[0])
                if not df.empty:
                    comp_values.update(df.iloc[:, 0].dropna().astype(str).str.strip().unique())

            # 5. Perform Comparison
            matches = sorted(list(base_values.intersection(comp_values)))
            missing_in_comp = sorted(list(base_values - comp_values))
            missing_in_base = sorted(list(comp_values - base_values))

            st.divider()
            st.subheader("📊 Comparison Summary")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Base Values (Col B)", len(base_values))
            m2.metric("Comparison Values (Col A)", len(comp_values))
            m3.metric("Matching Values", len(matches))
            m4.metric("Missing in Comparison", len(missing_in_comp))

            # 6. Display Results in Tabs
            t1, t2, t3 = st.tabs([
                f"❌ Missing in Comparison ({len(missing_in_comp)})",
                f"❌ Missing in Base ({len(missing_in_base)})",
                f"✅ Matching Values ({len(matches)})",
            ])

            with t1:
                st.write("Values present in Base File (Col B) but **MISSING** in Comparison File (Col A):")
                st.dataframe(
                    pd.DataFrame(missing_in_comp, columns=["Missing in Comparison File"]),
                    use_container_width=True,
                    hide_index=True,
                )

            with t2:
                st.write("Values present in Comparison File (Col A) but **MISSING** in Base File (Col B):")
                st.dataframe(
                    pd.DataFrame(missing_in_base, columns=["Missing in Base File"]),
                    use_container_width=True,
                    hide_index=True,
                )

            with t3:
                st.write("Values that match across both files:")
                st.dataframe(
                    pd.DataFrame(matches, columns=["Matching Values"]),
                    use_container_width=True,
                    hide_index=True,
                )

    except Exception as e:
        st.error(f"Error processing files: {e}")

else:
    st.info("👈 Please upload both **Base File** and **Comparison File** from the sidebar to begin.")
