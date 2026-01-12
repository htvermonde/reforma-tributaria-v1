# from office365.sharepoint.client_context import ClientContext

# # --- Configurações ---
# # Credenciais do Azure App (Substituindo usuário/senha para evitar erro de MFA/SAML)
# client_id = ""
# client_secret = ""

# # URL do Site Específico (Recomendado conectar diretamente ao site do acervo)
# site_url = "https://stefaninilatam.sharepoint.com/sites/Governana545Stefanini"

# # Caminho da pasta que deseja listar
# folder_url = "/sites/Governana545Stefanini/Documentos Compartilhados/Gestão/SC/99. Gestão IA/01. ACELERADORES/LLM Indexer/Reforma Tributaria - Potencial/compra"

# def listar_arquivos_sharepoint(site_url, client_id, client_secret, folder_url):
#     print(f"Conectando ao site: {site_url}")
#     try:
#         # Autenticação via Client ID e Secret (App-Only)
#         ctx = ClientContext(site_url).with_client_credentials(client_id, client_secret)
        
#         # Acessar a pasta
#         print(f"Acessando pasta: {folder_url}")
#         target_folder = ctx.web.get_folder_by_server_relative_url(folder_url)
#         files = target_folder.files
#         ctx.load(files)
#         ctx.execute_query()
        
#         print("-" * 50)
#         print(f"Arquivos encontrados ({len(files)}):")
#         lista_arquivos = []
#         for file in files:
#             print(f" - {file.name} ({file.length} bytes)")
#             lista_arquivos.append(file.name)
#         print("-" * 50)
            
#         return lista_arquivos

#     except Exception as e:
#         print("\n!! ERRO !!")
#         print(f"Detalhes: {e}")
#         # Dica para debug se falhar
#         if "401" in str(e) or "403" in str(e):
#              print("Verifique se o Client ID e Secret têm permissão neste site.")
#         return None

# if __name__ == "__main__":
#     listar_arquivos_sharepoint(site_url, client_id, client_secret, folder_url)


from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.client_credential import ClientCredential
import os
CLIENT_ID = ""
CLIENT_SECRET = ""
SITE_URL = "https://stefaninilatam.sharepoint.com/sites/Governana545Stefanini"
credentials = ClientCredential(CLIENT_ID, CLIENT_SECRET)
ctx = ClientContext(SITE_URL).with_credentials(credentials)
# Simple verification
web = ctx.web.get().execute_query()
print("Connected to SharePoint Site:", web.properties["Title"])