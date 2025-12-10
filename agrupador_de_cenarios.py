import pandas as pd
import os

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
        #'CNPJ/CPF Destinatário', 'Razão Social Destinatário', 
        'UF Emissor', 'UF Destinatário', 'Operação', 'Consumidor Final', 
        'NCM', 'CFOP', 'Natureza', 'ICMS', 'ICMS CST', 'IPI_CST', 
        'CONFINS', 
        # 'Transporte', 'Infos Adicionais', 'Imposto', 'ISSQN', 'DIFAL'
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
        nfs_agrupadas=('Numero Nota', lambda x: ', '.join(x.astype(str).unique()))
    ).reset_index()

    # 4. Salvar o DataFrame agrupado
    print(f"Salvando o resultado agrupado em: {caminho_saida}")
    
    # Detecta extensão e salva apropriadamente
    if caminho_saida.endswith('.xlsx'):
        df_agrupado.to_excel(caminho_saida, index=False)
    elif caminho_saida.endswith('.csv'):
        df_agrupado.to_csv(caminho_saida, index=False)
    else:
        print(f"AVISO: Extensão não reconhecida, salvando como CSV")
        df_agrupado.to_csv(caminho_saida, index=False)
    
    print("Processo concluído com sucesso!")
    print(f"Linhas no DataFrame original: {len(df)}")
    print(f"Linhas no DataFrame agrupado: {len(df_agrupado)}")

# --- Uso ---
caminho_entrada_exemplo = 'output/relatorio_customizado_v3.xlsx'
caminho_saida_exemplo = 'output/relatorio_customizado_agrupado_v2.xlsx'

agrupar_cenarios_nfs(caminho_entrada_exemplo, caminho_saida_exemplo)
