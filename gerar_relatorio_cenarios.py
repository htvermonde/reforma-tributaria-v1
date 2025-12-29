import pandas as pd
import os
import json
from toon_python import encode

def criar_estrutura_hierarquica(df_agrupado):
    """
    Converte DataFrame agrupado em estrutura hierárquica para formato TOON.
    """
    estrutura = {}
    
    for _, row in df_agrupado.iterrows():
        # Garantir que o CNPJ seja string e sem espaços
        cnpj_emit = str(row.get('CNPJ/CPF Emissor', 'DESCONHECIDO')).strip()
        
        if cnpj_emit not in estrutura:
            estrutura[cnpj_emit] = {
                'cnpj_emissor': cnpj_emit,
                'razao_social_emissor': str(row.get('Razão Social Emissor', '')),
                'uf_emissor': str(row.get('UF Emissor', '')),
                'cenarios': []
            }
        
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
                'natureza': str(row.get('NATOP', '')), # Corrigido para NATOP conforme lista de colunas
                'transporte': str(row.get('Transporte', ''))
            },
            'impostos': {
                'icms_cst': str(row.get('CST ICMS', '')),
                'ipi_cst': str(row.get('CST IPI', '')),
                'pis_cst': str(row.get('CST PIS', '')),
                'cofins_cst': str(row.get('CST COFINS', '')),
                'outros': str(row.get('Outros Impostos', '')),
                'sujeito_iss': str(row.get('Sujeito a ISS?', '')),
                'difal': str(row.get('DIFAL', ''))
            },
            'nfs_agrupadas': str(row.get('nfs_agrupadas', ''))
        }
        
        estrutura[cnpj_emit]['cenarios'].append(cenario)
    
    return {
        'total_emitentes': len(estrutura),
        'emitentes': list(estrutura.values())
    }

def agrupar_cenarios_nfs(caminho_entrada, caminho_saida):
    # 1. Carregar o DataFrame
    if caminho_entrada.endswith('.xlsx'):
        df = pd.read_excel(caminho_entrada)
    else:
        df = pd.read_csv(caminho_entrada)

    if df.empty:
        print("ERRO: O arquivo de entrada está vazio.")
        return

    # Limpeza básica: remover espaços extras nos nomes das colunas
    df.columns = df.columns.str.strip()

    # 2. Colunas de agrupamento
    colunas_agrupamento = [
        'Cenario', 'Tipo', 
        'CNPJ/CPF Emissor', 'Razão Social Emissor', 
        'CNPJ/CPF Destinatário', 'Razão Social Destinatário', 
        'UF Emissor', 'UF Destinatário', 'Operação', 'Consumidor Final', 
        'Transporte', 'NCM', 'Classificação/Produto', 'NATOP',
        'CFOP', 'DESC CFOP', 'CST ICMS', 'DESC CST ICMS', "%ICMS Normal", "ICMS VBC",
        'CST IPI', 'ENQUADRAMENTO IPI', '%IPI', 'TIPI',
        'CST PIS', 'DESC CST PIS', '%PIS',
        'CST COFINS', 'DESC CST COFINS', '%CONFINS',
        'Sujeito a ISS?', 'DIFAL', 
        'Outros Impostos'
    ]

    # Filtrar apenas as colunas que existem no arquivo
    colunas_existentes = [col for col in colunas_agrupamento if col in df.columns]
    
    # --- TRATAMENTO CRÍTICO PARA NÃO RETORNAR VAZIO ---
    # Convertemos tudo para string e tratamos nulos antes de agrupar
    df_process = df.copy()
    for col in colunas_existentes:
        df_process[col] = df_process[col].fillna('').astype(str).str.strip()

    # 3. Agrupar
    df_agrupado = df_process.groupby(colunas_existentes, as_index=False, dropna=False).agg(
        qtd_agrupamentos=('Numero Nota', 'count'),
        nfs_agrupadas=('Numero Nota', lambda x: ', '.join(x.astype(str).unique()))
    )

    # 4. Salvar Excel/CSV de conferência
    df_agrupado.to_excel(caminho_saida, index=False)
    
    # 5. Gerar JSON e TOON
    data_hierarquica = criar_estrutura_hierarquica(df_agrupado)
    
    caminho_base = caminho_saida.rsplit('.', 1)[0]
    
    try:
        # Salvar JSON
        with open(f"{caminho_base}.json", 'w', encoding='utf-8') as f:
            json.dump(data_hierarquica, f, ensure_ascii=False, indent=2)
        
        # Gerar e salvar TOON
        toon_data = encode(data_hierarquica)
        with open(f"{caminho_base}.toon", 'w', encoding='utf-8') as f:
            f.write(toon_data)
        
        print(f"✅ Sucesso! Original: {len(df)} linhas | Agrupado: {len(df_agrupado)} cenários.")
        
    except Exception as e:
        print(f"❌ Erro na geração dos arquivos: {e}")

# --- Execução ---
if __name__ == "__main__":
    entrada = 'output/relatorio_customizado.xlsx'
    saida = 'output/relatorio_agrupado.xlsx'
    
    if os.path.exists(entrada):
        agrupar_cenarios_nfs(entrada, saida)
    else:
        print(f"Arquivo não encontrado: {entrada}")