import urllib.request
import urllib.parse
import re
import html

def debug_bing():
    query = "Hospital Infantil Parada Angelica Duque de Caxias"
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://www.bing.com/search?q={encoded_q}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8"
        }
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        text = resp.read().decode('utf-8', errors='ignore')
        
    print("Bing HTML slice around href:")
    hrefs = [m.start() for m in re.finditer(r'href="http', text)]
    print(f"Found {len(hrefs)} hrefs in Bing!")
    for idx in hrefs[:10]:
        print("--- SLICE ---")
        print(text[idx-20:idx+250])

if __name__ == "__main__":
    debug_bing()
