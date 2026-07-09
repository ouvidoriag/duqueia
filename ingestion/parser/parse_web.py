import os
import json
import requests
from html.parser import HTMLParser

class HTMLTextExtractor(HTMLParser):
    """Extrator de texto simples para remover tags HTML."""
    def __init__(self):
        super().__init__()
        self.result = []
        self.hide_content = False

    def handle_starttag(self, tag, attrs):
        if tag in ["script", "style", "head", "title", "nav", "footer"]:
            self.hide_content = True

    def handle_endtag(self, tag):
        if tag in ["script", "style", "head", "title", "nav", "footer"]:
            self.hide_content = False

    def handle_data(self, data):
        if not self.hide_content:
            text = data.strip()
            if text:
                self.result.append(text)

    def get_text(self):
        return "\n".join(self.result)

def extract_text_from_url(url: str) -> str:
    """Realiza requisição HTTP e extrai o texto principal."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Converte encoding se necessário
        response.encoding = response.apparent_encoding
        
        extractor = HTMLTextExtractor()
        extractor.feed(response.text)
        return extractor.get_text()
    except Exception as e:
        print(f"[Web Parser Error] Falha ao ler URL {url}: {e}")
        return ""

def main():
    raw_dir = os.path.join("data", "raw", "raw_web_urls")
    parsed_dir = os.path.join("data", "processed")
    
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(parsed_dir, exist_ok=True)
    
    urls_file = os.path.join(raw_dir, "urls.txt")
    
    if not os.path.exists(urls_file):
        print(f"[Web Parser Warning] Arquivo de URLs em '{urls_file}' não encontrado. Criando com sites oficiais de Duque de Caxias...")
        with open(urls_file, "w", encoding="utf-8") as f:
            f.write("# Adicione uma URL por linha. Linhas começando com '#' são ignoradas.\n")
            f.write("https://duquedecaxias.rj.gov.br/\n")
            f.write("https://duquedecaxias.rj.gov.br/noticia/prefeitura-de-duque-de-caxias-inaugura-nova-unidade-de-saude/4312\n")
            
    with open(urls_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
        
    print(f"[Web Parser] Iniciando extração de {len(urls)} sites...")
    for idx, url in enumerate(urls):
        print(f"[Web Parser] Raspando URL ({idx+1}/{len(urls)}): {url}")
        content = extract_text_from_url(url)
        
        if content:
            # Cria nome amigável para o arquivo baseado na URL
            clean_name = url.replace("https://", "").replace("http://", "").replace("/", "_").replace(".", "_")[:50]
            output_path = os.path.join(parsed_dir, f"web_{clean_name}.json")
            
            parsed_data = {
                "source": url,
                "title": f"Portal da Prefeitura: {url}",
                "content": content,
                "metadata": {
                    "category": "web_scraped",
                    "url": url
                }
            }
            
            with open(output_path, "w", encoding="utf-8") as out:
                json.dump(parsed_data, out, ensure_ascii=False, indent=2)
                
            print(f"[Web Parser] Site raspado e salvo com sucesso em: {output_path}")

if __name__ == "__main__":
    main()
