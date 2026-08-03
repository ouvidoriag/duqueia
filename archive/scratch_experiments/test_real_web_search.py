import urllib.request
import urllib.parse
import re
import html
import sys

def test_ddg(query):
    encoded_q = urllib.parse.quote_plus(query)
    # Test Lite endpoint vs HTML endpoint vs Google
    url_lite = f"https://lite.duckduckgo.com/lite/"
    data = urllib.parse.urlencode({'q': query}).encode('utf-8')
    
    req = urllib.request.Request(
        url_lite,
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            html_text = response.read().decode("utf-8", errors="ignore")
            print(f"Response length: {len(html_text)}")
            print("Snippet sample:")
            print(html_text[:500])
            
            # Find links in lite.duckduckgo.com
            # Lite format: <a class='result-snippet' ...> or <td class="result-snippet"> or <a href="...">
            links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*class=["\']result-link["\'][^>]*>(.*?)</a>', html_text, re.DOTALL)
            if not links:
                links = re.findall(r'href="(https?://[^"]+)"', html_text)
            print(f"Found {len(links)} links:")
            for l in links[:5]:
                print(" ->", l)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_ddg("Hospital Infantil Parada Angelica Duque de Caxias")
