import requests
import os

def fazer_upload(caminho_arquivo_local):
    # 1. Identificação do seu ambiente via URL
    bucket_url = "https://reforma-tributaria-notas.s3.us-east-1.amazonaws.com"
    pasta_destino = "moet"
    
    # Pegamos o nome do arquivo (ex: 'nota.pdf') para compor a URL final
    nome_arquivo = os.path.basename(caminho_arquivo_local)
    
    # A URL completa que identifica seu ambiente e o destino do arquivo
    url_final = f"{bucket_url}/{pasta_destino}/{nome_arquivo}"
    
    print(f"Enviando para: {url_final}")

    try:
        # Abrimos o arquivo em modo binário ('rb')
        with open(caminho_arquivo_local, 'rb') as f:
            # O método PUT é o padrão que o S3 entende para uploads
            response = requests.put(url_final, data=f)
        
        # O S3 retorna 200 se o upload foi bem sucedido
        if response.status_code == 200:
            print("✅ Upload concluído com sucesso!")
        else:
            print(f"❌ Erro no upload. Status: {response.status_code}")
            print(f"Detalhes: {response.text}")
            
    except FileNotFoundError:
        print("Erro: O arquivo local não foi encontrado. Verifique o caminho.")

def fazer_upload_com_url_pronta(url_assinada, caminho_arquivo_local):
    """
    Faz o upload de um arquivo para o S3 usando uma Presigned URL fornecida.
    """
    try:
        # Abrimos o arquivo em modo binário ('rb')
        with open(caminho_arquivo_local, 'rb') as arquivo:
            # Para Presigned URLs do S3, enviamos o conteúdo diretamente no corpo (data)
            # O S3 espera um método PUT
            print(f"Iniciando upload de: {caminho_arquivo_local}...")
            
            response = requests.put(
                url_assinada, 
                data=arquivo,
                headers={'Content-Type': 'text/plain'} # Ajuste se for outro tipo de arquivo
            )

        # Verifica se o status code é 200 (OK)
        if response.status_code == 200:
            print("Sucesso! Arquivo enviado.")
        else:
            print(f"Erro no upload. Status: {response.status_code}")
            print(f"Detalhes: {response.text}")

    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_arquivo_local}' não foi encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

# --- VARIÁVEIS ---
minha_url = "https://reforma-tributaria-notas.s3.amazonaws.com/moet/teste-presign-linux.txt?AWSAccessKeyId=ASIA32BPI4BIWD3L44UP&Signature=KF2A7mr2vNn%2FLFQsCdXwNn4Pjpg%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEOb%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIF0Gdxq%2FW8euz9TVt%2Fd3s74T0%2FbDV5VViCteOsuWuoUKAiEAyoPNNoxW942XMgQoEld7btKn%2FDsl01P5%2B0pWwmAj4IEqhgQIr%2F%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FARACGgw4MTE4NDc5NjY4MDEiDAMECtZUOFWwsRydOCraA9cTTqDwWQ0x%2BMzESe7aCf2VhyIrakPWXa%2FIK5UneYxMneAATiW6WqDhFxO0tyxa%2FJKIeoeHdTfS1SWTEoUZp2x3ZHLoiNAkI16%2BfKGc4DbMOo3lknyB2js%2BcqC24ZJfEkMAaHKNMqovy4NjquQ71wMTtQl0hM3MDqGHU2q9VhvAqM3opc1iqMoPC9jMa8m9%2BHvzOWbRv6XErLvP%2F7dpWRAUBHHrwWGHf2RRp4TupEAdwEmJGHHZLIUXqtMSIJ4iqqJgG%2FyhfAy1pnEzZIMCaYoxTrv84I2boVx53hYbxX2UQqrWoW0urVSKWEmuGk0gyLMylYtYmSiHHZRAn2ChoWlUpkmuUZ35jZnBT6NuPjVaiIBAvEIqOTAYcQM2UCX%2Fg6PaIfFHFLJ9c7LP9D2JyxVxqbyQZ9HEXSaq36krVvDgi8uktWgSY8s5AjTmJZW56z7jsh7fimE1NlVht5yD5iBrrqYN8RhRwtFuC%2FYTIppTO9CRdt%2FVhqA%2F8ey9LW8VQbLCA9tP3Nnz74EewOeCiL0uDkK%2BcQ1quSbNkKkD219gTsp6o1sOpIE0cqOuSIQD0S1HmUwz2Ixof4DKcVz7I2WO2KSe4xgd5g1rL4Hk7P0RjSoDD7UHpizzszD12oXLBjqSAserW4xwno8Tw4on499ovViPHc3dG7PGqHI%2B2wfCrfdgvyENzgUQyfdw4EZ96IlMEcoJZ97nUsooz67%2FIma1qfElGLZL1KHdcr%2BcfwulF%2FQ7CUFWZYXb4Ps7Wy4PmDCbV5ll7nIFMidocuxioQawtI114pBtXDEPTXhDOqi6uZU8%2BYj%2Bm4stPQTM4PFc0O%2BPIVaeeO%2FMp8seZz2%2BKyaxNN%2FP6g5ZtQYpSp3pRfKS%2FDiU6fuVtd1BbO379vgG4ziM2kbNCOMlXwLhIlzZPzI5Nb9sATB80dKOPfJEuUg0kcx8QIXfQilckng4c8%2FvDPBf9dUQ9IPY8kVP1QkhSHBB1Ro1nG8U%2B%2FBqPn6z7rXbB5JxlC0%3D&Expires=1767998122"
arquivo_para_subir = "output/resposta_notas_moet.json" # Altere para o nome do seu arquivo

# Execução
# fazer_upload(arquivo_para_subir)
fazer_upload_com_url_pronta(minha_url, arquivo_para_subir)




