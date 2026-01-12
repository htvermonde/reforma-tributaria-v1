import boto3
import requests
import os
from botocore.config import Config

# --- CONFIGURAÇÕES AWS (Substitua pelos seus dados) ---
ACCESS_KEY = 'SUA_ACCESS_KEY'
SECRET_KEY = 'SUA_SECRET_KEY'
BUCKET_NAME = 'reforma-tributaria-notas'
REGION = 'us-east-1' 

def processar_upload_completo(caminho_arquivo_local):
    """
    1. Gera a Presigned URL dinamicamente baseada no nome do arquivo.
    2. Realiza o upload imediato via requisição HTTP PUT.
    """
    
    # Valida se o arquivo local existe
    if not os.path.exists(caminho_arquivo_local):
        print(f"❌ Arquivo não encontrado: {caminho_arquivo_local}")
        return

    # Extrai apenas o nome do arquivo (ex: 'documento.pdf') para salvar no S3
    nome_arquivo_s3 = f"moet/{os.path.basename(caminho_arquivo_local)}"

    # Inicializa o cliente S3 com suporte a assinatura V4
    s3_client = boto3.client(
        's3',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name=REGION,
        config=Config(signature_version='s3v4')
    )

    try:
        # PASSO 1: Gerar a URL Pré-assinada
        print(f"\n--- Processando: {os.path.basename(caminho_arquivo_local)} ---")
        url_presign = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': nome_arquivo_s3,
                'ContentType': 'application/octet-stream'
            },
            ExpiresIn=3600
        )
        print(f"✅ URL Gerada com sucesso.")

        # PASSO 2: Enviar o arquivo para a URL gerada
        with open(caminho_arquivo_local, 'rb') as corpo_arquivo:
            print(f"Iniciando transferência para o S3...")
            response = requests.put(
                url_presign, 
                data=corpo_arquivo,
                headers={'Content-Type': 'application/octet-stream'}
            )

        # Verificação do status do upload
        if response.status_code == 200:
            print(f"🚀 Sucesso! Arquivo disponível em: {nome_arquivo_s3}")
        else:
            print(f"🔴 Falha no upload: Status {response.status_code}")
            print(f"Mensagem da AWS: {response.text}")

    except Exception as e:
        print(f"❗ Erro crítico no processo: {e}")

# --- EXECUÇÃO ---

# Você pode passar uma lista de arquivos que deseja subir
arquivos_para_enviar = [
    "output/resposta_notas_moet.json",
    "output/resposta_notas_moet.json",
    "output/resposta_notas_moet.json"
]

for item in arquivos_para_enviar:
    # Este comando executa a geração da URL + o Upload
    processar_upload_completo(item)