import pandas as pd


def find_sheet_name(excel_file, pattern):
    """Finds a sheet name in an Excel file matching a wildcard pattern (case-insensitive)."""
    xls = pd.ExcelFile(excel_file)
    pattern = pattern.lower().replace("*", "")

    for sheet in xls.sheet_names:
        if pattern in sheet.lower():
            return sheet
    return None


def compare_excel_files(base_path, comp_path):
    # 1. Resolve sheet names dynamically
    base_office_sheet = find_sheet_name(base_path, "*office")
    comp_sheet2 = find_sheet_name(comp_path, "*sheet2")

    print(f"Base Office Sheet Found: {base_office_sheet}")
    print(f"Base Academic Sheet Found: Academic")
    print(f"Comparison Sheet Found: {comp_sheet2}")

    # 2. Read Base File Sheets (Column B is index 1)
    df_base_office = pd.read_excel(
        base_path, sheet_name=base_office_sheet, usecols=[1]
    )
    df_base_academic = pd.read_excel(
        base_path, sheet_name="Academic", usecols=[1]
    )

    # Combine Base values from both sheets into a single set
    col_b_office = df_base_office.iloc[:, 0].dropna().unique()
    col_b_academic = df_base_academic.iloc[:, 0].dropna().unique()
    base_values = set(col_b_office).union(set(col_b_academic))

    # 3. Read Comparison File Sheet (Column A is index 0)
    df_comp = pd.read_excel(comp_path, sheet_name=comp_sheet2, usecols=[0])
    comp_values = set(df_comp.iloc[:, 0].dropna().unique())

    # 4. Compare Values
    matches = base_values.intersection(comp_values)
    only_in_base = base_values - comp_values
    only_in_comp = comp_values - base_values

    # 5. Display Results
    print("\n" + "=" * 40)
    print(f"SUMMARY OF COMPARISON")
    print("=" * 40)
    print(f"Total Unique Base Values (Col B): {len(base_values)}")
    print(f"Total Unique Comparison Values (Col A): {len(comp_values)}")
    print(f"Matching Values: {len(matches)}")
    print(f"Values in Base but missing in Comparison: {len(only_in_base)}")
    print(f"Values in Comparison but missing in Base: {len(only_in_comp)}")

    # 6. Export Results to Excel
    output_file = "comparison_results.xlsx"
    with pd.ExcelWriter(output_file) as writer:
        pd.DataFrame(list(matches), columns=["Matches"]).to_excel(
            writer, sheet_name="Matches", index=False
        )
        pd.DataFrame(
            list(only_in_base), columns=["Missing_in_Comparison"]
        ).to_excel(writer, sheet_name="Missing_in_Comp", index=False)
        pd.DataFrame(list(only_in_comp), columns=["Missing_in_Base"]).to_excel(
            writer, sheet_name="Missing_in_Base", index=False
        )

    print(f"\nDetailed report saved to: {output_file}")


# --- RUN SCRIPT ---
base_file_path = "base_file.xlsx"
comparison_file_path = "comparison_file.xlsx"

# Replace file paths with your actual filenames
compare_excel_files(base_file_path, comparison_file_path)
