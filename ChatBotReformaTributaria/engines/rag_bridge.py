import asyncio
import requests
import httpx

from core.config import settings

class RAGBridge:
    """Conecta com o RAG interno"""
    
    def __init__(self,):
        self.base_url = "https://libindexr.dev.saiapplications.com"
    
    def create_document(self, file_path, use_ocr=False):
        """
        Envia um arquivo para o endpoint de criação de documento.
        Args:
            file_path: caminho do arquivo a ser enviado
            use_ocr: booleano para OCR
            document_url: endpoint opcional, se não informado usa padrão
        Returns: dict com resposta
        """
        url = f"{self.base_url}/api/document/create"
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.split('/')[-1], f)
            }
            data = {'useOCR': str(use_ocr).lower()}
            response = requests.post(url, files=files, data=data)
        try:
            return response.json()
        except Exception:
            return {'status_code': response.status_code, 'text': response.text}

    def create_source(self, document_id, chunk_size=1000, using_ai_summary=False, model="TEXT-EMBEDDING-3-LARGE"):
        """
        Cria um source via API.
        Args:
            document_id: id do documento
            index_ids: lista de ids de índices
            chunk_size: tamanho do chunk
            using_ai_summary: bool
            model: nome do modelo
            source_url: endpoint opcional, se não informado usa padrão
        Returns: dict com resposta
        """
        url = f"{self.base_url}/api/source/create"
        headers = {"Content-Type": "application/json"}
        payload = {
            "id": "",
            "documentId": document_id,
            "indexIds": [],
            "chunkSize": chunk_size,
            "usingAISummary": using_ai_summary,
            "model": model
        }
        response = requests.post(url, json=payload, headers=headers)
        try:
            return response.json()
        except Exception:
            return {'status_code': response.status_code, 'text': response.text}

    def create_indexer(self, index_name, sources_ids):
        """
        Cria um indexer via API.
        Args:
            index_name: nome do índice
            sources_ids: lista de ids de sources
            indexer_url: endpoint opcional, se não informado usa padrão
        Returns: dict com resposta
        """
        url = f"{self.base_url}/api/index/create"
        headers = {"Content-Type": "application/json"}
        payload = {
            "indexName": index_name,
            "sourcesIds": sources_ids
        }
        response = requests.post(url, json=payload, headers=headers)
        try:
            return response.json()
        except Exception:
            return {'status_code': response.status_code, 'text': response.text}

    def query_indexer(self, pergunta: str, index_id) -> list:
        """
        Busca trechos no RAG
        
        Returns:
            Lista de trechos encontrados
        """
        url = f"{self.base_url}/api/index/search"
        payload = {
            "indexId": index_id,
            "quantity": 3,
            "thresholdSimilarity": 0.4,
            "useChunkChain": False,
            "maxChunkChainLink": 0,
            "searchQuery": pergunta
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            print("Response RAG")
            print(response.status_code)
            print(response.text)
            
            if response.status_code == 200:
                data = response.json()
                # Ajuste conforme formato real do seu RAG
                return data.get('results', data.get('chunks', []))
            else:
                print(f"Erro RAG: {response.status_code}")
                return []
        except Exception as e:
            print(f"Erro: {e}")
            return []

    async def call_rag_api(self, search_query: str, index_id: str, rag_quantity: int = 3, threshold_similarity = 0.4, use_chunk_chain=False) -> list:
        """
        Executa uma busca na API de RAG usando um indexId específico.

        Args:
            search_query: A string de busca para enviar à API.
            index_id: O ID do índice a ser consultado na API de RAG.

        Returns:
            Uma lista de strings, onde cada string é o 'rawContent' de um chunk relevante.
            Retorna uma lista vazia em caso de erro de status HTTP.
            Levanta httpx.ConnectError em caso de falha de conexão.
        """
        await asyncio.sleep(0.5)

        payload = {
            "indexId": index_id,
            "quantity": rag_quantity,
            "thresholdSimilarity": threshold_similarity,
            "useChunkChain": use_chunk_chain,
            "maxChunkChainLink": 0,
            "searchQuery": search_query,
        }
        
        # log_extra = {"rag_query": search_query, "rag_url": settings.RAG_API_URL, "index_id": index_id}

        try:
            async with httpx.AsyncClient(timeout=settings.RAG_REQUEST_TIMEOUT) as client:
                response = await client.post(settings.RAG_API_URL, json=payload)
                response.raise_for_status()
                
                data = response.json()
                raw_contents = []

                if "results" in data and isinstance(data["results"], list):
                    for result in data["results"]:
                        if "chunks" in result and isinstance(result["chunks"], list):
                            for chunk_info in result["chunks"]:
                                raw_content = chunk_info.get("chunk", {}).get("rawContent")
                                if raw_content:
                                    raw_contents.append(raw_content)
                
                return raw_contents

        except httpx.ConnectError as e:
            raise e
        except httpx.HTTPStatusError as e:
            return []
        except Exception as e:
            return []
