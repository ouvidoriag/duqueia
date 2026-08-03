import urllib.request
import urllib.parse
import re
import html
import sys

def test_ddg_html_get(query):
    print(f"\n--- Testing DDG HTML GET for: '{query}' ---")
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded_q}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
            "Referer": "https://html.duckduckgo.com/"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            text = resp.read().decode('utf-8', errors='ignore')
            print("Length:", len(text))
            # Extract links and titles from html.duckduckgo.com
            # Pattern in DDG HTML: <a class="result__a" href="...">Title</a>
            # or <a class="result__url" href="...">...</a>
            results = re.findall(r'<a class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', text, re.DOTALL)
            print(f"Found {len(results)} result__a links!")
            for u, t in results[:5]:
                clean_t = re.sub(r'<[^>]+>', '', html.unescape(t)).strip()
                # Parse uddg URL
                actual_url = u
                if "uddg=" in u:
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
                    if "uddg" in parsed:
                        actual_url = parsed["uddg"][0]
                print(f" -> [{clean_t}] ({actual_url})")

            # Extract snippets
            snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', text, re.DOTALL)
            print(f"Found {len(snippets)} snippets!")
            for s in snippets[:3]:
                clean_s = re.sub(r'<[^>]+>', '', html.unescape(s)).strip()
                print("   Snippet:", clean_s[:100])
    except Exception as e:
        print("Error:", e)

def test_bing_html_get(query):
    print(f"\n--- Testing Bing HTML GET for: '{query}' ---")
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://www.bing.com/search?q={encoded_q}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            text = resp.read().decode('utf-8', errors='ignore')
            print("Length:", len(text))
            # Bing search result links: <h2><a href="URL">TITLE</a></h2>
            b_results = re.findall(r'<h2><a href="(https?://[^"]+)"[^>]*>(.*?)</a></h2>', text, re.DOTALL)
            print(f"Found {len(b_results)} Bing links!")
            for u, t in b_results[:5]:
                clean_t = re.sub(r'<[^>]+>', '', html.unescape(t)).strip()
                print(f" -> [{clean_t}] ({u})")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_ddg_html_get("Hospital Infantil Parada Angelica Duque de Caxias")
    test_bing_html_get("Hospital Infantil Parada Angelica Duque de Caxias")
