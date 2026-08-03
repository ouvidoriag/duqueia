import urllib.request
import urllib.parse
import re
import html
import json
import sys

def search_official_web(query: str, domain: str = "duquedecaxias.rj.gov.br", max_results: int = 3) -> list:
    """
    Realiza busca externa controlada restrita a domínios oficiais municipais.
    Retorna lista de dicionários: [{'title': ..., 'url': ..., 'snippet': ...}]
    """
    search_term = f"site:{domain} {query}"
    encoded_q = urllib.parse.quote_plus(search_term)
    url = f"https://html.duckduckgo.com/html/?q={encoded_q}"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
        }
    )

    results = []
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            html_text = response.read().decode("utf-8", errors="ignore")

        # Extrai blocos de resultado
        matches = re.findall(r'<a class="result__url"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?<a class="result__snippet"[^>]*>(.*?)</a>', html_text, re.DOTALL)

        for raw_url, raw_url_text, raw_snippet in matches[:max_results]:
            # Decodifica URL do DuckDuckGo se necessário
            actual_url = raw_url
            if "uddg=" in raw_url:
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
                if "uddg" in parsed:
                    actual_url = parsed["uddg"][0]

            clean_snippet = re.sub(r'<[^>]+>', '', html.unescape(raw_snippet)).strip()
            clean_title = re.sub(r'<[^>]+>', '', html.unescape(raw_url_text)).strip()

            if clean_snippet and domain in actual_url:
                results.append({
                    "title": clean_title or f"Portal Oficial {domain}",
                    "url": actual_url,
                    "snippet": clean_snippet
                })

    except Exception as e:
        print(f"[WebSearch Warning] Erro de busca na web ({domain}): {e}", file=sys.stderr)

    return results

if __name__ == "__main__":
    q = "IPTU 2026 segunda via Duque de Caxias"
    res = search_official_web(q)
    print(f"Resultados da busca externa oficial para '{q}':")
    print(json.dumps(res, ensure_ascii=False, indent=2))
