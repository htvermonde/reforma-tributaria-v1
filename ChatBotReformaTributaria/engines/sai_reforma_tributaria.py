from typing import List, Dict, Any
import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

class RTSAI:
    def __init__(self):
        self.api_key = os.getenv("SAI_API_KEY", "")
        self.is_initialized = False
        self.urls = "https://sai-library.saiapplications.com/api/templates/6930416fd96d536af1cf6e82/execute"

    def is_available(self) -> bool:
        return bool(os.getenv("SAI_API_KEY"))

    def initialize(self) -> bool:
        self.is_initialized = self.is_available()
        return self.is_initialized

    def get_first_infos(self, dados: Dict[str, Any]) -> List[Dict[str, Any]]:
        
        headers = {"X-Api-Key": self.api_key}
        data = {"inputs": {"dados": dados}}
        
        print("=== DEBUG ===")
        print(f"URL: {self.urls}")
        print(f"Enviando requisição...")
        
        # Aumenta timeout e adiciona retry
        max_retries = 3
        timeout = 300  # 5 minutos
        
        for tentativa in range(1, max_retries + 1):
            try:
                print(f"\nTentativa {tentativa}/{max_retries}...")
                response = requests.post(self.urls, json=data, headers=headers, timeout=timeout)
                
                print(f"\nStatus Code: {response.status_code}")
                print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                print(f"Tamanho da resposta: {len(response.content)} bytes")
                
                # Verificar se é JSON
                print("\n=== INSPECIONANDO RESPOSTA ===")
                try:
                    json_response = response.json()
                    print(f"Tipo da resposta: JSON")
                    print(f"Chaves disponíveis: {json_response.keys() if isinstance(json_response, dict) else 'não é dict'}")
                    print(f"Conteúdo JSON completo:")
                    print(json.dumps(json_response, indent=2, ensure_ascii=False))
                    text = str(json_response)
                except:
                    print(f"Tipo da resposta: Texto puro")
                    text = response.text
                    print(f"Conteúdo: {text}")
                
                if response.status_code != 200:
                    text = f"Erro {response.status_code}: {response.text}"
                
                result = {"text": text.strip() if text else ""}
                return [result]
                
            except requests.exceptions.ReadTimeout:
                print(f"\n⚠️  Timeout na tentativa {tentativa}")
                if tentativa == max_retries:
                    print(f"\n❌ Falha após {max_retries} tentativas")
                    return [{"text": f"Erro: Timeout após {max_retries} tentativas. A requisição demorou mais de {timeout} segundos."}]
                print("Tentando novamente...")
            except Exception as e:
                print(f"\n❌ Erro: {e}")
                return [{"text": f"Erro: {str(e)}"}]


# Exemplo de uso rápido
if __name__ == "__main__":
    import json
    
    rt = RTSAI()
    rt.initialize()
    
    with open("output/relatorio_customizado_agrupado_v2.json", 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    dados = str(dados)
    resultado = rt.get_first_infos(dados)
    
    # Salvar resposta completa em arquivo Markdown
    with open("output/resposta_completa.md", 'w', encoding='utf-8') as f:
        f.write(resultado[0]["text"])
    
    print("\n=== RESPOSTA COMPLETA ===")
    print(resultado[0]["text"])
    print(f"\n✓ Resposta salva em: output/resposta_completa.md")
