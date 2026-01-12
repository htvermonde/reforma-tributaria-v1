import os
import requests

class LlmIndexEngine:
    def __init__(self, doc_hash: str, api_key: str):
        """
        Inicializa a engine do LlmIndexer.
        
        Args:
            doc_hash (str): Hash do documento/índice.
            api_key (str): Chave de API para autenticação (Header: ApiKey).
        """
        self.doc_hash = doc_hash
        self.api_key = api_key
        self.base_url = "https://llmindexer-api.saiapplications.com"
        self.headers = {
            "ApiKey": self.api_key
        }

    def list_files(self):
        """
        Lista os arquivos associados ao hash do documento.
        
        Endpoint esperado: GET /api/index/{hash}/files
        """
        url = f"{self.base_url}/api/index/{self.doc_hash}/files"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def upload_file(self, file_path: str):
        """
        Faz upload de um arquivo para o índice.
        
        Endpoint: POST /api/index/{hash}/files/upload
        Body: Files (multipart/form-data)
        """
        url = f"{self.base_url}/api/index/{self.doc_hash}/files/upload"
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
        filename = os.path.basename(file_path)
        
        # 'Files' é a chave especificada no prompt para o corpo da requisição
        with open(file_path, 'rb') as f:
            files = {
                'Files': (filename, f)
            }
            response = requests.post(url, headers=self.headers, files=files)
        
        response.raise_for_status()
        return response.json()

    def get_file_info(self, file_id: str):
        """
        Obtém informações detalhadas de um arquivo específico.
        
        Endpoint esperado: GET /api/index/{hash}/files/{file_id}
        """
        url = f"{self.base_url}/api/index/{self.doc_hash}/files/{file_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_rag_details(self, question: str):
        """
        Obtém detalhes do RAG (Retrieve Augmented Generation) com base em uma pergunta.
        
        Endpoint esperado: POST /api/index/{hash}/search (Suposição padrão REST)
        """
        # Assumindo endpoint de busca/query
        url = f"{self.base_url}/api/index/{self.doc_hash}/search"
        
        payload = {
            "question": question
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

if __name__ == "__main__":
    # COLOQUE SUAS CREDENCIAIS AQUI PARA TESTAR
    # Exemplo de hash que estava no prompt: H4b5963a3bdc8485cbe92fcaf493999c3
    DOC_HASH = "H4b5963a3bdc8485cbe92fcaf493999c3" 
    API_KEY = "AvkBvNfUn8GzQzeAMRNLbXapL7RC_4DZzeBRqhBjA-c=" 
    
    engine = LlmIndexEngine(doc_hash=DOC_HASH, api_key=API_KEY)
    
    print(f"Iniciando testes para DocHash: {DOC_HASH}...\n")

    # 1. Teste de Listagem
    # print("--- 1. Listar Arquivos ---")

    # files = engine.list_files()
    # print(f"Sucesso! Arquivos encontrados: {files}")
    
    # Tenta pegar um ID real para usar nos proximos testes
    # Ajuste a chave 'id' ou 'fileId' conforme o retorno real da API list_files
    # file_id_teste = None
    # if isinstance(files, list) and len(files) > 0:
    #         # Supondo que o retorno seja lista de dicts
    #     file_id_teste = files[0].get('id') 
    # elif isinstance(files, dict) and 'files' in files:
    #     file_list = files['files']
    #     if file_list:
    #         file_id_teste = file_list[0].get('id')


    # # 2. Teste de Upload
    # print("\n--- 2. Upload de Arquivo ---")
    # dummy_path = "output/relatorio_agrupado_moet.txt"
    # with open(dummy_path, "w", encoding="utf-8") as f:
    #     f.write("Conteúdo de teste para a engine RAG.")
        
    # upload_resp = engine.upload_file(dummy_path)
    # print(f"Sucesso! Upload realizado: {upload_resp}")

    # # if os.path.exists(dummy_path):
    # #     os.remove(dummy_path)


