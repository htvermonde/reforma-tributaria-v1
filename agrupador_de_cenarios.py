import pandas as pd
import os
import json
from toon_python import encode

def criar_estrutura_hierarquica(df_agrupado):
    """
    Converte DataFrame agrupado em estrutura hierárquica para formato TOON.
    Agrupa por emitente e organiza cenários de forma aninhada.
    """
    estrutura = {}
    
    for _, row in df_agrupado.iterrows():
        cnpj_emit = str(row.get('CNPJ/CPF Emissor', 'DESCONHECIDO'))
        
        # Inicializa estrutura do emitente se não existir
        if cnpj_emit not in estrutura:
            estrutura[cnpj_emit] = {
                'cnpj_emissor': cnpj_emit,
                'razao_social_emissor': str(row.get('Razão Social Emissor', '')),
                'uf_emissor': str(row.get('UF Emissor', '')),
                'cenarios': []
            }
        
        # Adiciona cenário ao emitente
        cenario = {
            'tipo': str(row.get('Tipo', '')),
            'destinatario': {
                'cnpj': str(row.get('CNPJ/CPF Destinatário', '')),
                'razao_social': str(row.get('Razão Social Destinatário', '')),
                'uf': str(row.get('UF Destinatário', ''))
            },
            'fiscal': {
                'operacao': str(row.get('Operação', '')),
                'consumidor_final': str(row.get('Consumidor Final', '')),
                'ncm': str(row.get('NCM', '')),
                'cfop': str(row.get('CFOP', '')),
                'natureza': str(row.get('Natureza', '')),
                'transporte': str(row.get('Transporte', ''))
            },
            'impostos': {
                'icms': str(row.get('ICMS', '')),
                'icms_cst': str(row.get('ICMS CST', '')),
                'ipi_cst': str(row.get('IPI_CST', '')),
                'confins': str(row.get('CONFINS', '')),
                'outros': str(row.get('Outros Impostos', '')),
                'sujeito_iss': str(row.get('Sujeito a ISS?', '')),
                'difal': str(row.get('DIFAL', ''))
            },
            'infos_adicionais': str(row.get('Infos Adicionais', '')),
            'nfs_agrupadas': str(row.get('nfs_agrupadas', ''))
        }
        
        estrutura[cnpj_emit]['cenarios'].append(cenario)
    
    # Converte dict de emitentes para lista
    resultado = {
        'total_emitentes': len(estrutura),
        'emitentes': list(estrutura.values())
    }
    
    return resultado

def agrupar_cenarios_nfs(caminho_entrada, caminho_saida):
    """
    Recebe um DataFrame de Notas Fiscais, agrupa os cenários e consolida
    os números das notas fiscais agrupadas.

    Args:
        caminho_entrada (str): Caminho para o arquivo CSV de entrada.
        caminho_saida (str): Caminho para salvar o arquivo CSV de saída agrupado.
    """
    try:
        # 1. Carregar o DataFrame
        print(f"Carregando dados de: {caminho_entrada}")
        # Detecta extensão e carrega apropriadamente
        if caminho_entrada.endswith('.xlsx'):
            df = pd.read_excel(caminho_entrada)
        elif caminho_entrada.endswith('.csv'):
            df = pd.read_csv(caminho_entrada)
        else:
            print(f"ERRO: Formato de arquivo não suportado. Use .xlsx ou .csv")
            return
        
    except FileNotFoundError:
        print(f"ERRO: Arquivo não encontrado no caminho: {caminho_entrada}")
        return
    except Exception as e:
        print(f"Ocorreu um erro ao carregar o arquivo: {e}")
        return

    # 2. Definir as colunas de agrupamento (cenário)
    colunas_agrupamento = [
        'Tipo', 'CNPJ/CPF Emissor', 'Razão Social Emissor', 
        'CNPJ/CPF Destinatário', 'Razão Social Destinatário', 
        'UF Emissor', 'UF Destinatário', 
        'Operação', 'Consumidor Final', 'Transporte',
        'NCM', 'Classificação/Produto', 'CFOP', 'DESC CFOP',
        'CST ICMS', 'DESC CST ICMS', 
        'CST IPI', 'ENQUADRAMENTO IPI', '%IPI', 'TIPI',
        'CONFINS', 'DESC CST COFINS','Sujeito a ISS?',
        'Outros Impostos', 'DIFAL'
        # 'Infos Adicionais'
    ]
    # Adicionar outras colunas relevantes conforme necessário 
    # 'Transporte', 'Infos Adicionais', 'Imposto', 'ISSQN', 'DIFAL'

    # Verificar se todas as colunas de agrupamento existem no DataFrame
    colunas_ausentes = [col for col in colunas_agrupamento if col not in df.columns]
    if colunas_ausentes:
        print(f"ERRO: As seguintes colunas de agrupamento não foram encontradas no DataFrame: {colunas_ausentes}")
        return

    # 3. Agrupar e agregar
    print("Agrupando cenários...")
    
    # A coluna 'Numero Nota' é a que será consolidada.
    # Usamos o .apply(list) para criar uma lista com todos os números de nota.
    # O .agg(lambda x: ', '.join(x.astype(str).unique())) é uma alternativa
    # mais robusta para concatenar os números de notas únicos em uma string separada por vírgula.
    
    df_agrupado = df.groupby(colunas_agrupamento).agg(
        qtd_agrupamentos=('Numero Nota', 'count'),
        nfs_agrupadas=('Numero Nota', lambda x: ', '.join([str(val) for val in x]))
    ).reset_index()

    # 4. Salvar o DataFrame agrupado em múltiplos formatos
    print(f"Salvando o resultado agrupado em: {caminho_saida}")
    
    # Detecta extensão e salva apropriadamente
    if caminho_saida.endswith('.xlsx'):
        df_agrupado.to_excel(caminho_saida, index=False)
    elif caminho_saida.endswith('.csv'):
        df_agrupado.to_csv(caminho_saida, index=False)
    else:
        print(f"AVISO: Extensão não reconhecida, salvando como CSV")
        df_agrupado.to_csv(caminho_saida, index=False)
    
    # 5. Converter DataFrame para estrutura hierárquica e salvar em JSON e TOON
    print("Convertendo para formatos JSON e TOON...")
    
    # Converte DataFrame para estrutura hierárquica
    data_hierarquica = criar_estrutura_hierarquica(df_agrupado)
    
    # Gera caminhos para JSON e TOON (substitui extensão)
    caminho_base = caminho_saida.rsplit('.', 1)[0]
    caminho_json = f"{caminho_base}.json"
    caminho_toon = f"{caminho_base}.toon"
    
    try:
        # 1. Salva JSON primeiro
        with open(caminho_json, 'w', encoding='utf-8') as f:
            json.dump(data_hierarquica, f, ensure_ascii=False, indent=2)
        print(f"   ✅ JSON salvo em: {caminho_json}")
        
        # 2. Lê o JSON salvo e converte para TOON (garante consistência)
        with open(caminho_json, 'r', encoding='utf-8') as f:
            data_from_json = json.load(f)
        
        toon_data = encode(data_from_json)
        
        with open(caminho_toon, 'w', encoding='utf-8') as f:
            f.write(toon_data)
        
        # Calcula economia de espaço
        json_size = os.path.getsize(caminho_json)
        toon_size = os.path.getsize(caminho_toon)
        economy_percent = ((json_size - toon_size) / json_size) * 100
        
        print(f"   ✅ TOON salvo em: {caminho_toon}")
        print(f"   📊 Tamanho JSON: {json_size:,} bytes")
        print(f"   📊 Tamanho TOON: {toon_size:,} bytes")
        print(f"   💾 Economia: {economy_percent:.1f}%")
        
    except Exception as e:
        print(f"   ⚠️  Erro ao salvar JSON/TOON: {e}")
    
    print("\nProcesso concluído com sucesso!")
    print(f"Linhas no DataFrame original: {len(df)}")
    print(f"Linhas no DataFrame agrupado: {len(df_agrupado)}")

# --- Uso ---
caminho_entrada_exemplo = 'output/relatorio_customizado.xlsx'
caminho_saida_exemplo = 'output/relatorio_agrupado.xlsx'

agrupar_cenarios_nfs(caminho_entrada_exemplo, caminho_saida_exemplo)
