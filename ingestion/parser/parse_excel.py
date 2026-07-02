import os
import json
import pandas as pd

def main():
    raw_dir = "raw_excel_files"
    parsed_dir = "parsed_pdf_files"
    
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(parsed_dir, exist_ok=True)

    excel_files = [f for f in os.listdir(raw_dir) if f.endswith((".xlsx", ".xls"))]
    
    if not excel_files:
        print(f"[Excel Parser Warning] Nenhum arquivo Excel encontrado em '{raw_dir}'. Criando um arquivo mock de exemplo...")
        # Cria arquivo mock Excel com dados de postos de saúde de Duque de Caxias
        mock_path = os.path.join(raw_dir, "postos_saude_caxias.xlsx")
        df_mock = pd.DataFrame({
            "Unidade": ["UPA Parque Lafaiete", "Hospital Moacyr do Carmo", "UBS Xerém"],
            "Endereco": ["Av. Nilo Peçanha, s/n", "Rod. Washington Luíz, km 10", "Rua Vasconcelos, 12"],
            "Especialidades": ["Clínica Geral, Pediatria", "Alta Complexidade, Emergência", "Atenção Básica, Vacinação"]
        })
        # Salva usando openpyxl
        df_mock.to_excel(mock_path, index=False)
        excel_files = ["postos_saude_caxias.xlsx"]

    for excel_file in excel_files:
        excel_path = os.path.join(raw_dir, excel_file)
        print(f"[Excel Parser] Lendo Excel: {excel_path}")
        
        # Lê a planilha Excel
        df = pd.read_excel(excel_path)
        
        # Transforma o conteúdo em formato descritivo legível por texto
        records = df.to_dict(orient="records")
        text_content = f"Dados estruturados da planilha {excel_file.replace('.xlsx', '').replace('.xls', '')}:\n"
        for rec in records:
            row_desc = " | ".join(f"{col}: {val}" for col, val in rec.items())
            text_content += f"- {row_desc}\n"
            
        output_path = os.path.join(parsed_dir, excel_file.replace(".xlsx", ".json").replace(".xls", ".json"))
        
        parsed_data = {
            "source": excel_file,
            "title": f"Planilha: {excel_file.replace('.xlsx', '').replace('.xls', '')}",
            "content": text_content,
            "metadata": {
                "category": "excel_data",
                "rows_count": len(df),
                "columns": list(df.columns)
            }
        }
        
        with open(output_path, "w", encoding="utf-8") as out:
            json.dump(parsed_data, out, ensure_ascii=False, indent=2)
            
        print(f"[Excel Parser] Convertido com sucesso para: {output_path}")

if __name__ == "__main__":
    main()
