"""
provider_health.py — DUQUE IA
==============================
Verifica a integridade e disponibilidade dos provedores LLM (Gemini, Groq, OpenAI).
Executado na inicialização para garantir visibilidade do estado do sistema.
"""

import sys
import time

class ProviderHealthChecker:
    
    @staticmethod
    def check_all() -> dict:
        """
        Verifica a integridade de todos os provedores LLM configurados.
        Retorna um dicionário com o status de cada um.
        """
        print("[HealthCheck] Iniciando verificação de provedores LLM...", file=sys.stderr)
        results = {}
        
        # 1. Checa Gemini
        try:
            from utils.gemini_client import GeminiClient
            t0 = time.time()
            gemini = GeminiClient()
            if not gemini.api_keys:
                results["gemini"] = {"status": "offline", "reason": "Nenhuma chave configurada"}
            else:
                try:
                    # Teste leve: geração de 1 token
                    resp = gemini.generate_response("Diga 'OK'", max_output_tokens=5)
                    lat = (time.time() - t0) * 1000
                    results["gemini"] = {"status": "ok", "latency_ms": round(lat), "model": gemini.generation_model_name}
                except Exception as e:
                    results["gemini"] = {"status": "error", "error": str(e)}
        except Exception as e:
            results["gemini"] = {"status": "error", "error": str(e)}
            
        # 2. Checa Groq
        try:
            from utils.groq_client import GroqClient
            t0 = time.time()
            groq = GroqClient()
            if not groq.api_keys:
                results["groq"] = {"status": "offline", "reason": "Nenhuma chave configurada"}
            else:
                try:
                    resp = groq.generate_response("Diga 'OK'", prefer_quality=False)
                    lat = (time.time() - t0) * 1000
                    results["groq"] = {"status": "ok", "latency_ms": round(lat), "model": "llama-3.1-8b-instant"}
                except Exception as e:
                    results["groq"] = {"status": "error", "error": str(e)}
        except Exception as e:
            results["groq"] = {"status": "error", "error": str(e)}
            
        # 3. Checa OpenAI
        import os
        from openai import OpenAI
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if not openai_key or openai_key == "YOUR_API_KEY_HERE":
            results["openai"] = {"status": "skip", "reason": "Chave não configurada ou placeholder"}
        else:
            try:
                client = OpenAI(api_key=openai_key)
                t0 = time.time()
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Diga 'OK'"}],
                    max_tokens=5
                )
                lat = (time.time() - t0) * 1000
                results["openai"] = {"status": "ok", "latency_ms": round(lat), "model": "gpt-4o-mini"}
            except Exception as e:
                results["openai"] = {"status": "error", "error": str(e)}

        # Imprime relatório no console
        for prov, info in results.items():
            status = info.get("status")
            if status == "ok":
                print(f"  [✔] {prov.upper().ljust(8)} | OK ({info.get('latency_ms')}ms) - {info.get('model')}", file=sys.stderr)
            elif status == "skip" or status == "offline":
                print(f"  [-] {prov.upper().ljust(8)} | IGNORADO ({info.get('reason')})", file=sys.stderr)
            else:
                print(f"  [✖] {prov.upper().ljust(8)} | ERRO: {info.get('error')[:80]}...", file=sys.stderr)
                
        return results
