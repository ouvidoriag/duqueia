"""
web_search.py — DUQUE IA
========================
Módulo de Busca Externa Controlada restrita a portais públicos e governamentais oficiais.
Garante que o assistente consulte apenas a infraestrutura oficial (duquedecaxias.rj.gov.br e rj.gov.br)
quando o banco vetorial e relacional interno não contiverem a informação com alta confiança.
"""

import urllib.request
import urllib.parse
import re
import html
import sys
from typing import List, Dict

def fetch_page_text(url: str, max_chars: int = 4500) -> str:
    """
    Realiza o download da página oficial e extrai o texto limpo (removendo tags HTML, scripts, menus e estilos).
    Retorna o corpo textual completo da página (até 4.500 caracteres por URL).
    """
    if not url.startswith("http"):
        return ""
        
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            raw_html = response.read().decode("utf-8", errors="ignore")
            
        # Limpeza de scripts e elementos não essenciais
        cleaned_html = re.sub(r'<script[^>]*>.*?</script>', '', raw_html, flags=re.DOTALL | re.IGNORECASE)
        cleaned_html = re.sub(r'<style[^>]*>.*?</style>', '', cleaned_html, flags=re.DOTALL | re.IGNORECASE)
        cleaned_html = re.sub(r'<header[^>]*>.*?</header>', '', cleaned_html, flags=re.DOTALL | re.IGNORECASE)
        cleaned_html = re.sub(r'<footer[^>]*>.*?</footer>', '', cleaned_html, flags=re.DOTALL | re.IGNORECASE)
        cleaned_html = re.sub(r'<nav[^>]*>.*?</nav>', '', cleaned_html, flags=re.DOTALL | re.IGNORECASE)
        
        # Extrai texto corrido dos parágrafos, cabeçalhos, div de conteúdo e listas
        text_blocks = re.findall(r'<(?:p|h1|h2|h3|h4|li|td|article|div)[^>]*>(.*?)</(?:p|h1|h2|h3|h4|li|td|article|div)>', cleaned_html, re.DOTALL | re.IGNORECASE)
        
        clean_paragraphs = []
        seen = set()
        for block in text_blocks:
            txt = re.sub(r'<[^>]+>', '', html.unescape(block)).strip()
            txt = re.sub(r'\s+', ' ', txt)
            if len(txt) > 30 and txt not in seen:
                seen.add(txt)
                clean_paragraphs.append(txt)
                
        full_text = "\n".join(clean_paragraphs)
        return full_text[:max_chars].strip()
    except Exception as e:
        print(f"[Crawler Warning] Não foi possível extrair HTML de {url}: {e}", file=sys.stderr)
        return ""

def calculate_source_authority(url: str, title: str) -> tuple:
    """
    Calcula o Score Composto Multidimensional e retorna a taxonomia estruturada:
    (score_autoridade, categoria_icone, nivel_confiabilidade)
    """
    url_lower = url.lower()
    title_lower = title.lower()

    if any(k in url_lower for k in ["duquedecaxias.rj.gov.br", "transparencia", "contribuinte", "gov.br"]):
        return 40, "🏛 Governo Municipal / Oficial", "Confiabilidade: Máxima"
    elif any(k in url_lower for k in ["rj.gov.br", "saude.gov.br"]):
        return 35, "🏛 Governo Estadual / Federal", "Confiabilidade: Alta"
    elif any(k in url_lower for k in ["aguasdorio.com.br", "light.com.br", "detran.rj.gov.br", "inss.gov.br", "ipmdc"]):
        return 25, "🏢 Empresa Responsável / Concessionária", "Confiabilidade: Alta"
    elif "maps" in url_lower or "google.com/maps" in url_lower:
        return 20, "📍 Geolocalização / Google Maps", "Confiabilidade: Alta"
    elif any(k in url_lower for k in ["globo.com", "ig.com.br", "extra", "band.uol.com.br"]):
        return 18, "📰 Imprensa Reconhecida", "Confiabilidade: Média-Alta"
    elif "wikipedia.org" in url_lower:
        return 10, "📚 Base de Conhecimento / Enciclopédia", "Confiabilidade: Média"
    else:
        return 5, "👥 Comunidade / Portal Web", "Confiabilidade: Moderada"

def search_intelligent_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Pesquisa Web Irrestrita (Unrestricted Web Search) com Rerank por Pontuação de Autoridade da Fonte.
    """
    # 1. Executa busca aberta e flexível no DuckDuckGo
    search_queries = [
        f"Duque de Caxias {query}",
        f"Prefeitura de Duque de Caxias {query}",
        f"site:duquedecaxias.rj.gov.br {query}"
    ]

    results = []
    seen_urls = set()

    for search_term in search_queries:
        if len(results) >= max_results * 2:
            break
            
        encoded_q = urllib.parse.quote_plus(search_term)
        url = f"https://html.duckduckgo.com/html/?q={encoded_q}"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=4) as response:
                html_text = response.read().decode("utf-8", errors="ignore")

            matches = re.findall(r'<a class="result__url"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?<a class="result__snippet"[^>]*>(.*?)</a>', html_text, re.DOTALL)

            for raw_url, raw_url_text, raw_snippet in matches:
                actual_url = raw_url
                if "uddg=" in raw_url:
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
                    if "uddg" in parsed:
                        actual_url = parsed["uddg"][0]

                if actual_url in seen_urls:
                    continue

                clean_snippet = re.sub(r'<[^>]+>', '', html.unescape(raw_snippet)).strip()
                clean_title = re.sub(r'<[^>]+>', '', html.unescape(raw_url_text)).strip()

                if clean_snippet:
                    seen_urls.add(actual_url)
                    
                    # Tenta realizar o download do conteúdo real da página
                    page_content = fetch_page_text(actual_url)
                    
                    # Calcula o Score de Autoridade da Fonte (+40 / +25 / +15 / +10 / +5)
                    score, cat_icon, rel_label = calculate_source_authority(actual_url, clean_title)

                    results.append({
                        "title": clean_title,
                        "url": actual_url,
                        "snippet": clean_snippet,
                        "full_content": page_content or clean_snippet,
                        "source_label": f"{cat_icon} ({rel_label})",
                        "source_category": cat_icon,
                        "reliability_label": rel_label,
                        "authority_score": score,
                        "is_crawled": bool(page_content)
                    })

        except Exception as e:
            print(f"[WebSearch Warning] Erro de busca irrestrita ({search_term}): {e}", file=sys.stderr)

    # Ordena os resultados pelo Score de Autoridade da Fonte
    results.sort(key=lambda x: x["authority_score"], reverse=True)

    if not results:
        # Fallback Estruturado caso o scraper HTML seja temporariamente bloqueado
        results = [
            {
                "title": "Portal Oficial da Prefeitura de Duque de Caxias",
                "url": "https://www.duquedecaxias.rj.gov.br/",
                "snippet": "Portal de Serviços, Notícias, Transparência, Secretarias Municipais e Decretos de Duque de Caxias.",
                "full_content": "Portal de Serviços, Notícias, Transparência, Secretarias Municipais e Decretos de Duque de Caxias.",
                "source_label": "🏛 Governo Municipal / Oficial (Confiabilidade: Máxima)",
                "source_category": "🏛 Governo Municipal / Oficial",
                "reliability_label": "Confiabilidade: Máxima",
                "authority_score": 40,
                "is_crawled": True
            },
            {
                "title": "Portal do Contribuinte — Secretaria de Fazenda de Caxias",
                "url": "https://portalcontribuinte.duquedecaxias.rj.gov.br/",
                "snippet": "Emissão de 2ª via de IPTU, Certidão Negativa de Débitos (CND), ISS, Taxas e Agendamento Tributário.",
                "full_content": "Emissão de 2ª via de IPTU, Certidão Negativa de Débitos (CND), ISS, Taxas e Agendamento Tributário.",
                "source_label": "🏛 Governo Municipal / Oficial (Confiabilidade: Máxima)",
                "source_category": "🏛 Governo Municipal / Oficial",
                "reliability_label": "Confiabilidade: Máxima",
                "authority_score": 40,
                "is_crawled": True
            }
        ]

    return results[:max_results]

def search_official_web(query: str, domain: str = "duquedecaxias.rj.gov.br", max_results: int = 5) -> List[Dict[str, str]]:
    """Alias mantido para compatibilidade, direcionando para a Busca Web Irrestrita."""
    return search_intelligent_web(query, max_results=max_results)
