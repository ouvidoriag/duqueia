import os
import json
import pandas as pd

def main():
    raw_dir = "raw_csv_files"
    parsed_dir = "parsed_pdf_files" # Usamos o mesmo diretório de destino unificado
    
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(parsed_dir, exist_ok=True)

    csv_files = [f for f in os.listdir(raw_dir) if f.endswith(".csv")]
    
    if not csv_files:
        print(f"[CSV Parser Warning] Nenhum arquivo CSV encontrado em '{raw_dir}'. Criando um arquivo mock de exemplo...")
        # Cria arquivo mock de dados de bairros de Duque de Caxias
        mock_path = os.path.join(raw_dir, "bairros_caxias.csv")
        df_mock = pd.DataFrame({
            "bairro": ["Jardim Primavera", "Xerém", "Imbarié", "Centro"],
            "populacao_estimada": [45000, 32000, 50000, 28000],
            "zona": ["2º Distrito", "4º Distrito", "3º Distrito", "1º Distrito"]
        })
        df_mock.to_csv(mock_path, index=False, encoding="utf-8")
        csv_files = ["bairros_caxias.csv"]

    for csv_file in csv_files:
        csv_path = os.path.join(raw_dir, csv_file)
        print(f"[CSV Parser] Lendo CSV: {csv_path}")
        
        try:
            df = pd.read_csv(csv_path, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, encoding="latin1")
            
        # Converte as linhas do DataFrame para texto descritivo e estruturado
        records = df.to_dict(orient="records")
        text_content = f"Dados estruturados da tabela {csv_file.replace('.csv', '')}:\n"
        for rec in records:
            row_desc = " | ".join(f"{col}: {val}" for col, val in rec.items())
            text_content += f"- {row_desc}\n"
            
        output_path = os.path.join(parsed_dir, csv_file.replace(".csv", ".json"))
        
        parsed_data = {
            "source": csv_file,
            "title": f"Tabela de Dados: {csv_file.replace('.csv', '')}",
            "content": text_content,
            "metadata": {
                "category": "csv_data",
                "rows_count": len(df),
                "columns": list(df.columns)
            }
        }
        
        with open(output_path, "w", encoding="utf-8") as out:
            json.dump(parsed_data, out, ensure_ascii=False, indent=2)
            
        print(f"[CSV Parser] Convertido com sucesso para: {output_path}")

if __name__ == "__main__":
    main()
