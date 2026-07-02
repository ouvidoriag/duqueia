import os
import re

ROOT = r"c:\Users\501379.PMDC\Desktop\PRODUCAO"

key_patterns = [
    re.compile(r"AIzaSy[A-Za-z0-9_\-]{33}"),
    re.compile(r"AQ\.[A-Za-z0-9_\-]{40,}")
]

print("Procurando chaves de API do Gemini no projeto...")
found_keys = set()

for dirpath, dirnames, filenames in os.walk(ROOT):
    # Ignora pastas de controle de versão ou caches
    if any(p in dirpath for p in [".git", "__pycache__", "node_modules", ".gemini"]):
        continue
    for filename in filenames:
        filepath = os.path.join(dirpath, filename)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for pattern in key_patterns:
                    matches = pattern.findall(content)
                    for match in matches:
                        found_keys.add(match)
        except Exception:
            pass

print(f"\nTotal de chaves únicas encontradas no projeto: {len(found_keys)}")
for key in found_keys:
    masked = key[:8] + "..." + key[-8:] if len(key) > 16 else key
    print(f"- Chave: {key} (Mascara: {masked})")
