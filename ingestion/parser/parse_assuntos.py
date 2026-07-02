import os
import json
import csv
import re

def slugify(text):
    """Gera um slug simples a partir de um texto."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text)
    return text.strip('_')

def main():
    csv_path = os.path.join("bancoia", "assuntoXsecretaria.csv")
    parsed_dir = "parsed_pdf_files"
    
    if not os.path.exists(csv_path):
        print(f"[Error] Arquivo não encontrado: {csv_path}")
        return

    print(f"[Assuntos Parser] Lendo {csv_path}...")
    
    # Agrupa assuntos por secretaria
    groups = {}
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        # Pula cabeçalho
        header = next(reader, None)
        
        for row in reader:
            if not row or len(row) < 2:
                continue
            subject = row[0].strip()
            secretaria = row[1].strip()
            
            # Pula linhas vazias
            if not subject or not secretaria:
                continue
            
            # Pula mock/placeholder de dados vazios
            if "Não há dados" in subject or "Não há dados" in secretaria:
                continue
                
            if secretaria not in groups:
                groups[secretaria] = []
            groups[secretaria].append(subject)
            
    print(f"[Assuntos Parser] Encontradas {len(groups)} secretarias/órgãos no CSV.")
    
    for secretaria, subjects in groups.items():
        slug = slugify(secretaria)
        # Remove duplicados preservando a ordem
        unique_subjects = []
        for s in subjects:
            if s not in unique_subjects:
                unique_subjects.append(s)
                
        # Constrói o texto estruturado em Markdown
        content = f"# Assuntos e Demandas do Aplicativo Colab: {secretaria}\\n\\n"
        content += f"A **{secretaria}** é o órgão responsável por responder, fiscalizar e solucionar as seguintes solicitações, reclamações e demandas abertas pelos cidadãos através do aplicativo Colab:\\n\\n"
        
        for subj in unique_subjects:
            content += f"- **{subj}**\\n"
            
        content += "\\nPara reclamações de demora, grosseria, desvios ou falta de atendimento relacionados a estes assuntos, o cidadão também pode recorrer à Ouvidoria Geral do Município."

        output_file = f"assunto_secretaria_{slug}.json"
        output_path = os.path.join(parsed_dir, output_file)
        
        parsed_data = {
            "source": f"assunto_secretaria_{slug}.md",
            "title": f"Demandas Colab: {secretaria}",
            "content": content,
            "metadata": {
                "category": "secretarias",
                "secretaria": secretaria,
                "demandas_count": len(unique_subjects)
            }
        }
        
        with open(output_path, "w", encoding="utf-8") as out:
            json.dump(parsed_data, out, ensure_ascii=False, indent=2)
            
        print(f"[Assuntos Parser] Gerado JSON estruturado: {output_path} ({len(unique_subjects)} demandas)")

if __name__ == "__main__":
    main()
