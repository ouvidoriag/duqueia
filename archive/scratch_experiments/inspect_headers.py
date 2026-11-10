import openpyxl

xlsx_path = r"c:\Users\501379.PMDC\Desktop\PRODUCAO\Carta_Servicos_Secretaria_Municipal_de_Governo (5).xlsx"
wb = openpyxl.load_workbook(xlsx_path, data_only=True)
sheet = wb.active

for idx in range(1, 10):
    row_val = [c.value for c in sheet[idx]]
    if any(c is not None for c in row_val):
        print(f"Row {idx}: {row_val}")

wb.close()
