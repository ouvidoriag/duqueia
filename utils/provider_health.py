"""
provider_health.py — DUQUE IA
==============================
Verifica a integridade e disponibilidade das chaves do Google Gemini API.
Executado na inicialização para garantir visibilidade do estado do sistema.
"""

import sys
import time

class ProviderHealthChecker:
    
    @staticmethod
    def check_all() -> dict:
        """
        Verifica a integridade do provedor Gemini.
        Retorna um dicionário com o status do serviço.
        """
        print("[HealthCheck] Iniciando verificação de saúde da API Gemini...", file=sys.stderr)
        results = {}
        
        # Checa Gemini
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
                    results["gemini"] = {
                        "status": "ok",
                        "latency_ms": round(lat),
                        "model": gemini.generation_model_name,
                        "keys_count": len(gemini.api_keys)
                    }
                except Exception as e:
                    results["gemini"] = {"status": "error", "error": str(e)}
        except Exception as e:
            results["gemini"] = {"status": "error", "error": str(e)}

        # Imprime relatório no console
        for prov, info in results.items():
            status = info.get("status")
            if status == "ok":
                print(f"  [✔] {prov.upper().ljust(8)} | OK ({info.get('latency_ms')}ms) - Modelo: {info.get('model')} ({info.get('keys_count')} chaves ativas)", file=sys.stderr)
            elif status in ["skip", "offline"]:
                print(f"  [-] {prov.upper().ljust(8)} | DESCONECTADO ({info.get('reason')})", file=sys.stderr)
            else:
                print(f"  [✖] {prov.upper().ljust(8)} | ERRO: {info.get('error')[:80]}...", file=sys.stderr)
                
        return results

