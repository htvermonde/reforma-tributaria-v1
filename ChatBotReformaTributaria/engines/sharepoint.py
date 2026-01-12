import msal
import requests

# Configurações do App (obtidas no Portal Azure)
CLIENT_ID = 'seu-client-id'
CLIENT_SECRET = 'seu-client-secret'
TENANT_ID = 'seu-tenant-id'
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

# Configurações do SharePoint
SITE_ID = "seu-site-id-do-sharepoint"
FOLDER_PATH = "General/NomeDaPasta" # Caminho dentro da biblioteca

# 1. Obter Token de Acesso
app = msal.ConfidentialClientApplication(CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET)
token_response = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

if "access_token" in token_response:
    headers = {'Authorization': f"Bearer {token_response['access_token']}"}
    
    # 2. Listar itens da pasta
    # endpoint: /sites/{site-id}/drive/root:/{path}:/children
    url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drive/root:/{FOLDER_PATH}:/children"
    
    response = requests.get(url, headers=headers)
    items = response.json()
    
    for item in items.get('value', []):
        print(f"Nome: {item['name']} | ID: {item['id']}")
else:
    print("Erro ao obter token:", token_response.get("error_description"))