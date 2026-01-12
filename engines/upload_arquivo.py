from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.client_context import ClientContext
import os

# Configurações extraídas da sua URL
site_url = "https://stefaninilatam.sharepoint.com"
username = "hvermonde@stefanini.com"
password = "H@llen232324"

# Caminho exato da pasta de destino
target_folder_url = "/sites/Governana545Stefanini/Documentos Compartilhados/Gestão/SC/99. Gestão IA/01. ACELERADORES/LLM Indexer/Reforma Tributaria - Potencial/compra"

# Arquivo que você quer subir
local_path = "base/relatorio_customizado_compra.txt"

def get_context():
    """Cria e retorna o contexto autenticado do SharePoint."""
    return ClientContext(site_url).with_credentials(UserCredential(username, password))

def upload_arquivo():
    try:
        # Autenticação
        ctx = get_context()
        
        # Lendo o arquivo local
        if not os.path.exists(local_path):
            print(f"Erro: O arquivo {local_path} não foi encontrado na pasta do script.")
            return

        with open(local_path, 'rb') as content_file:
            file_content = content_file.read()

        # Obtendo a pasta e realizando o upload
        target_folder = ctx.web.get_folder_by_server_relative_url(target_folder_url)
        target_folder.upload_file(os.path.basename(local_path), file_content).execute_query()
        
        print("Upload concluído com sucesso!")
        
    except Exception as e:
        print(f"Ocorreu um erro no upload: {e}")

def listar_arquivos():
    """Lista os arquivos presentes na pasta de destino."""
    try:
        # Autenticação
        ctx = get_context()
        
        # Obtendo a pasta
        target_folder = ctx.web.get_folder_by_server_relative_url(target_folder_url)
        files = target_folder.files
        ctx.load(files)
        ctx.execute_query()
        
        print(f"\n--- Arquivos em '{target_folder_url}' ---")
        path_list = []
        for file in files:
            print(f"Nome: {file.name} | Tamanho: {file.length} bytes")
            path_list.append(file.serverRelativeUrl)
        return path_list
            
    except Exception as e:
        print(f"Ocorreu um erro ao listar arquivos: {e}")
        return []

if __name__ == "__main__":
    # upload_arquivo()
    listar_arquivos()