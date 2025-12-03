import json
import pandas as pd

# Caminho do arquivo JSON de entrada e Excel de saída
ARQUIVO_JSON = 'output/resposta_notas.json'
ARQUIVO_EXCEL = 'output/relatorio_customizado.xlsx'

# Defina aqui as colunas desejadas na ordem do exemplo da imagem
COLUNAS = [
    'FILIAL', 'CNPJ', 'Cliente/Recep/Produto', 'Numero', 'Serie', 'Modelo', 'Data Emissao',
    'ESTADUAL', 'MUNICIPAL', 'CENARIO', 'NATOP', 'CFOP', 'DESC CFOP', 'CONSUMIDOR FINAL',
    'GEST FISC', 'DESC GEST FISC', 'ICMS', 'ICMS Outras UF', 'ICMS Diferido', 'ICMS Outras UF',
    'Fundo Pobreza', 'Mensagem da NF', 'Mensagem referente ao ICMS', 'IPI', 'CST IPI',
    'ENQ IPI', 'VALOR IPI', 'TIP IPI', 'UNID IPI', 'GEST IPI', 'DESC GEST IPI', 'PIS',
    'CST PIS', 'SERIE CST PIS', 'COFINS', 'CST COFINS', 'SERIE CST COFINS', 'SERVICOS ISS',
    'LC 116', 'LOGO SERVICO FINANCEIRO', 'MSS', 'ISS RETIDO', 'PIS', 'COFINS', 'CSLL',
    'IRRF', 'INSS', 'RETENCAO PIS E INSS', 'Compensação', 'BASE', 'RET', 'RETEN', 'RETEN1'
]

def carregar_dados_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def expandir_itens(dados):
    linhas = []
    for nota in dados:
        item_numero = nota.get('ITEM_NUMERO')
        if isinstance(item_numero, list):
            for i in range(len(item_numero)):
                linha = {}
                # Exemplo de preenchimento, ajuste conforme o mapeamento real
                linha['CNPJ'] = nota.get('EMIT_CNPJ')
                linha['Cliente/Recep/Produto'] = nota.get('ITEM_XPROD', [None]*len(item_numero))[i]
                linha['Numero'] = nota.get('NUMERO_NF')
                linha['Serie'] = nota.get('SERIE')
                linha['Modelo'] = nota.get('MODELO')
                linha['Data Emissao'] = nota.get('DATA_EMISSAO')
                linha['CFOP'] = nota.get('ITEM_CFOP', [None]*len(item_numero))[i]
                # ...adicione os demais campos conforme necessário...
                linhas.append(linha)
        else:
            linha = {}
            linha['CNPJ'] = nota.get('EMIT_CNPJ')
            linha['Cliente/Recep/Produto'] = nota.get('ITEM_XPROD')
            linha['Numero'] = nota.get('NUMERO_NF')
            linha['Serie'] = nota.get('SERIE')
            linha['Modelo'] = nota.get('MODELO')
            linha['Data Emissao'] = nota.get('DATA_EMISSAO')
            linha['CFOP'] = nota.get('ITEM_CFOP')
            # ...adicione os demais campos conforme necessário...
            linhas.append(linha)
    return linhas

def main():
    dados = carregar_dados_json(ARQUIVO_JSON)
    linhas = expandir_itens(dados)
    df = pd.DataFrame(linhas)
    # Garante todas as colunas do layout, mesmo que vazias
    for col in COLUNAS:
        if col not in df.columns:
            df[col] = ''
    df = df[COLUNAS]
    df.to_excel(ARQUIVO_EXCEL, index=False)
    print(f'Relatório gerado em: {ARQUIVO_EXCEL}')

if __name__ == '__main__':
    main()
