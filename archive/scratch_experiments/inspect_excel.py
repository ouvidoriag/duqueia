import openpyxl
import os

xlsx_path = r"c:\Users\501379.PMDC\Desktop\PRODUCAO\Carta_Servicos_Secretaria_Municipal_de_Governo (5).xlsx"

if not os.path.exists(xlsx_path):
    print(f"File not found: {xlsx_path}")
else:
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    print("Sheets in workbook:", wb.sheetnames)
    sheet = wb.active
    rows = list(sheet.iter_rows(values_only=True))
    print(f"Total rows in sheet '{sheet.title}': {len(rows)}")
    if len(rows) > 0:
        print("Header row (Row 1):", rows[0])
        print("\nSample Row 2:", rows[1] if len(rows) > 1 else "None")

    # Search for saxofone in all cells
    sax_matches = []
    for idx, row in enumerate(rows, start=1):
        row_str = " | ".join([str(c) for c in row if c is not None])
        if "saxofone" in row_str.lower():
            sax_matches.append((idx, row_str))

    print(f"\nFound {len(sax_matches)} rows matching 'saxofone':")
    for r_idx, r_str in sax_matches[:5]:
        print(f" Row {r_idx}: {r_str[:200]}...")

    wb.close()
