import urllib.request
import urllib.parse
import re
import html

def test_bing_organic():
    query = "Hospital Infantil Parada Angelica Duque de Caxias"
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://www.bing.com/search?q={encoded_q}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8"
        }
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        text = resp.read().decode('utf-8', errors='ignore')

    # Look for <li class="b_algo"> in Bing
    blocks = re.findall(r'<li class="b_algo">(.*?)</li>', text, re.DOTALL)
    print(f"Found {len(blocks)} b_algo blocks in Bing!")
    
    for idx, b in enumerate(blocks[:5]):
        # Extract title, url, snippet
        url_match = re.search(r'<h2><a href="([^"]+)"[^>]*>(.*?)</a></h2>', b, re.DOTALL)
        snippet_match = re.search(r'<p[^>]*>(.*?)</p>', b, re.DOTALL) or re.search(r'<div class="b_caption">(.*?)</div>', b, re.DOTALL)
        
        if url_match:
            u = url_match.group(1)
            t = re.sub(r'<[^>]+>', '', html.unescape(url_match.group(2))).strip()
            s = re.sub(r'<[^>]+>', '', html.unescape(snippet_match.group(1))).strip() if snippet_match else ""
            print(f"\nResult #{idx+1}:")
            print(f"  Title: {t}")
            print(f"  URL:   {u}")
            print(f"  Snippet: {s[:150]}")

if __name__ == "__main__":
    test_bing_organic()
