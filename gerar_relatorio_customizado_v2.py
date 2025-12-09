import json
import pandas as pd
from typing import Dict, Any, List

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================

ARQUIVO_JSON = 'output/resposta_notas.json'
ARQUIVO_EXCEL = 'output/relatorio_customizado_v11.xlsx'

# ==============================================================================
# TABELAS DE DE-PARA
# ==============================================================================

# CFOP - Código Fiscal de Operações e Prestações
TABELA_CFOP = {
    # Entradas
    '1101': 'Compra para industrialização',
    '1102': 'Compra para comercialização',
    '1411': 'Devolução de venda de produção do estabelecimento',
    '1661': 'Devolução de venda de combustível',
    '1949': 'Outra entrada de mercadoria ou prestação de serviço não especificada',
    
    # Saídas
    '5101': 'Venda de produção do estabelecimento',
    '5102': 'Venda de mercadoria adquirida ou recebida de terceiros',
    '5405': 'Venda de mercadoria adquirida ou recebida de terceiros em operação com mercadoria sujeita ao regime de substituição tributária, na condição de contribuinte substituído',
    '5411': 'Devolução de compra para industrialização',
    '5949': 'Outra saída de mercadoria ou prestação de serviço não especificada',
    '6101': 'Venda de produção do estabelecimento',
    '6102': 'Venda de mercadoria adquirida ou recebida de terceiros',
}

# CST IPI
TABELA_CST_IPI = {
    '00': 'Entrada com recuperação de crédito',
    '01': 'Entrada tributada com alíquota zero',
    '02': 'Entrada isenta',
    '03': 'Entrada não-tributada',
    '04': 'Entrada imune',
    '05': 'Entrada com suspensão',
    '49': 'Outras entradas',
    '50': 'Saída tributada',
    '51': 'Saída tributada com alíquota zero',
    '52': 'Saída isenta',
    '53': 'Saída não-tributada',
    '54': 'Saída imune',
    '55': 'Saída com suspensão',
    '99': 'Outras saídas',
}

# CST PIS/COFINS
TABELA_CST_PIS_COFINS = {
    '01': 'Operação Tributável com Alíquota Básica',
    '02': 'Operação Tributável com Alíquota Diferenciada',
    '03': 'Operação Tributável com Alíquota por Unidade de Medida de Produto',
    '04': 'Operação Tributável Monofásica - Revenda a Alíquota Zero',
    '05': 'Operação Tributável por Substituição Tributária',
    '06': 'Operação Tributável a Alíquota Zero',
    '07': 'Operação Isenta da Contribuição',
    '08': 'Operação sem Incidência da Contribuição',
    '09': 'Operação com Suspensão da Contribuição',
    '49': 'Outras Operações de Saída',
    '50': 'Operação com Direito a Crédito - Vinculada Exclusivamente a Receita Tributada no Mercado Interno',
    '99': 'Outras Operações',
}

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def safe_get(data, index, default=''):
    """Retorna o valor no índice da lista, ou default se não existir."""
    if data is None:
        return default
    if isinstance(data, list):
        return data[index] if index < len(data) else default
    if index == 0:
        return data if data is not None else default
    return default

def get_desc_cfop(cfop):
    """Retorna a descrição do CFOP."""
    return TABELA_CFOP.get(str(cfop), f'CFOP {cfop}')

def get_desc_cst_ipi(cst):
    """Retorna a descrição do CST IPI."""
    return TABELA_CST_IPI.get(str(cst), f'CST {cst}')

def get_desc_cst_pis_cofins(cst):
    """Retorna a descrição do CST PIS/COFINS."""
    return TABELA_CST_PIS_COFINS.get(str(cst), f'CST {cst}')


def get_consumidor_final(nota: Dict[str, Any]) -> Dict[str, Any]:
  
    ind_final = nota.get('IND_FINAL', '')
    modelo = str(nota.get('MODELO', '')).strip()
    
    # Nível 1: IND_FINAL
    if str(ind_final) == '1':
        return {
            'consumidor_final': 'SIM',
            'desc_consumidor_final': 'Consumidor Final (IND_FINAL=1)'
        }
    
    # Nível 2: Modelo 65
    if modelo == '65':
        return {
            'consumidor_final': 'SIM',
            'desc_consumidor_final': 'NFC-e (Modelo 65)'
        }
    
    # Padrão: B2B
    return {
        'consumidor_final': 'NAO',
        'desc_consumidor_final': 'Operação B2B (Modelo 55 ou 57, IND_FINAL=0)'
    }


def get_info_adicionais(nota: Dict[str, Any], item_index: int = 0) -> Dict[str, Any]:
    """
    Extrai informações adicionais da nota e do item.
    """
    # Campos de nível de nota
    info_contrib = nota.get('INFO_ADICIONAL_CONTRIB')
    info_fisco = nota.get('INFO_ADICIONAL_FISCO')
    
    # Campo de nível de item
    item_info = safe_get(nota.get('ITEM_INFO_ADICIONAL'), item_index, '')
    
    # Montar mensagem consolidada
    mensagem_partes = []
    
    if info_contrib:
        mensagem_partes.append(f"[CONTRIB]: {info_contrib}")
    
    if info_fisco:
        mensagem_partes.append(f"[FISCO]: {info_fisco}")
    
    if item_info:
        mensagem_partes.append(f"[ITEM {safe_get(nota.get('ITEM_NUMERO'), item_index, '')}]: {item_info}")
    
    # Se alguma informação existe, concatenar; senão, vazio
    mensagem_final = ' | '.join(mensagem_partes) if mensagem_partes else ''
    
    return {
        'info_adicionais': mensagem_final
    }


def get_documento_emissor(nota: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai CNPJ/CPF e Razão Social do Emissor."""
    emit_cnpj = nota.get('EMIT_CNPJ')
    emit_cpf = nota.get('EMIT_CPF')
    return {
        'emit_documento': emit_cnpj if emit_cnpj else emit_cpf,
        'emit_tipo_pessoa': 'PJ' if emit_cnpj else 'PF',
        'emit_cnpj': emit_cnpj,
        'emit_razao_social': nota.get('EMIT_RAZAO_SOCIAL', ''),
    }

def get_documento_destinatario(nota: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai CNPJ/CPF e Razão Social do Destinatário."""
    dest_cnpj = nota.get('DEST_CNPJ')
    dest_cpf = nota.get('DEST_CPF')
    return {
        'dest_documento': dest_cnpj if dest_cnpj else dest_cpf,
        'dest_tipo_pessoa': 'PJ' if dest_cnpj else 'PF',
        'dest_razao_social': nota.get('DEST_RAZAO_SOCIAL', ''),
    }

def get_uf_emissor(nota: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai UF do Emissor."""
    return {'emit_uf': nota.get('EMIT_UF', '')}

def get_uf_destinatario(nota: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai UF do Destinatário."""
    return {'dest_uf': nota.get('DEST_UF', '')}

def get_tipo_operacao(nota: Dict[str, Any]) -> Dict[str, Any]:
    """Classifica como Entrada ou Saída."""
    tipo_nf = nota.get('TIPO_NF', '')
    return {'tipo_operacao': 'ENTRADA' if tipo_nf == '0' else 'SAIDA'}

def get_ncm(nota: Dict[str, Any], item_index: int) -> Dict[str, Any]:
    """Extrai NCM do item."""
    return {'ncm': safe_get(nota.get('ITEM_NCM'), item_index, '')}

def get_cfop_info(nota: Dict[str, Any], item_index: int) -> Dict[str, Any]:
    """Extrai CFOP e descrição."""
    cfop = safe_get(nota.get('ITEM_CFOP'), item_index, '')
    return {
        'cfop': cfop,
        'desc_cfop': get_desc_cfop(cfop),
    }

def get_natureza_operacao(nota: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai Natureza de Operação."""
    return {'natureza_operacao': nota.get('NATUREZA_OPERACAO', '')}

def get_ipi_status(nota: Dict[str, Any], item_index: int) -> Dict[str, Any]:
    """Classifica IPI como tributado, isento ou sem aplicação."""
    cst_ipi = safe_get(nota.get('ITEM_IPI_CST'), item_index, '')
    
    if not cst_ipi or cst_ipi == '':
        status = 'SEM_IPI'
        descricao = 'Não se aplica'
    elif str(cst_ipi) in ['50', '51']:
        status = 'TRIBUTADO'
        descricao = get_desc_cst_ipi(cst_ipi)
    elif str(cst_ipi) in ['52', '53', '54', '55', '99']:
        status = 'ISENTO'
        descricao = get_desc_cst_ipi(cst_ipi)
    else:
        status = 'OUTROS'
        descricao = get_desc_cst_ipi(cst_ipi)
    
    return {
        'ipi_status': status,
        'ipi_descricao': descricao,
        'cst_ipi': cst_ipi,
        'valor_ipi': safe_get(nota.get('ITEM_IPI_VIPI'), item_index, '0.00'),
    }

def get_cofins_status(nota: Dict[str, Any], item_index: int) -> Dict[str, Any]:
    """ Classifica COFINS em 4 categorias."""
    cst_cofins = safe_get(nota.get('ITEM_COFINS_CST'), item_index, '')
    cofins_isento_list = ['07', '08', '09']
    cofins_tributado_list = ['01', '02', '03', '04', '05', '06']
    
    if not cst_cofins:
        tem_cofins = 'NAO'
        status = 'Não mapeado'
    elif str(cst_cofins) in cofins_isento_list:
        tem_cofins = 'NAO'
        status = get_desc_cst_pis_cofins(cst_cofins) + ' (Isento/Suspenso)'
    elif str(cst_cofins) in cofins_tributado_list:
        tem_cofins = 'SIM'
        status = get_desc_cst_pis_cofins(cst_cofins)
    else:
        tem_cofins = 'OUTRO'
        status = f'CST {cst_cofins} (não classificado)'
    
    cst_pis = safe_get(nota.get('ITEM_PIS_CST'), item_index, '')
    
    return {
        'tem_cofins': tem_cofins,
        'status_cofins': status,
        'cst_cofins': cst_cofins,
        'cst_pis': cst_pis,
        'desc_cst_pis': get_desc_cst_pis_cofins(cst_pis),
    }

def aplicar_regras_negocio(nota: Dict[str, Any], item_index: int) -> Dict[str, Any]:
    """
    Aplica as regras de negócio chamando funções especializadas.
    Mantém consistência arquitetural com funções separadas por regra.
    """
    resultado = {}
    
    resultado.update(get_documento_emissor(nota))          
    resultado.update(get_documento_destinatario(nota))      
    resultado.update(get_uf_emissor(nota))                  
    resultado.update(get_uf_destinatario(nota))             
    resultado.update(get_tipo_operacao(nota))               
    resultado.update(get_consumidor_final(nota))            
    resultado.update(get_ncm(nota, item_index))             
    resultado.update(get_cfop_info(nota, item_index))       
    resultado.update(get_natureza_operacao(nota))           
    resultado.update(get_ipi_status(nota, item_index))      
    resultado.update(get_cofins_status(nota, item_index))   
    resultado.update(get_info_adicionais(nota, item_index)) 
    
    return resultado

# ==============================================================================
# FUNÇÃO PRINCIPAL: EXPANDIR ITENS E GERAR RELATÓRIO
# ==============================================================================

def get_json_completo_nfe(nota: Dict[str, Any]) -> str:
    """
    Retorna o JSON completo da NFe formatado para exibição.
    """
    return json.dumps(nota, ensure_ascii=False, indent=2)

def expandir_notas_para_linhas(notas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Expande cada nota em múltiplas linhas (uma por item).
    """
    linhas = []
    
    for nota in notas:
        # Descobrir quantos itens tem na nota
        item_numero = nota.get('ITEM_NUMERO')
        
        if item_numero is None:
            continue
            
        num_itens = len(item_numero) if isinstance(item_numero, list) else 1
        
        # Criar uma linha para cada item
        for i in range(num_itens):
            linha = {
                # Dados básicos da nota
                'arquivo_xml': nota.get('xml_filename', ''),
                'json_completo_nfe': get_json_completo_nfe(nota),
                'modelo': nota.get('MODELO', ''),
                'serie': nota.get('SERIE', ''),
                'numero_nf': nota.get('NUMERO_NF', ''),
                'data_emissao': nota.get('DATA_EMISSAO', ''),
                'valor_total_nf': nota.get('TOTAL_VNF', ''),
                'emit_razao_social': nota.get('EMIT_RAZAO_SOCIAL', ''),
                'emit_municipio': nota.get('EMIT_MUN', ''),
                'dest_municipio': nota.get('DEST_MUN', ''),
                
                # Dados do item
                'item_numero': safe_get(item_numero, i, ''),
                'item_codigo': safe_get(nota.get('ITEM_CPROD'), i, ''),
                'item_descricao': safe_get(nota.get('ITEM_XPROD'), i, ''),
                'item_unidade': safe_get(nota.get('ITEM_UNIDADE'), i, ''),
                'item_quantidade': safe_get(nota.get('ITEM_QTDE'), i, ''),
                'item_valor': safe_get(nota.get('ITEM_VPROD'), i, ''),
                
                'total_pis': nota.get('TOTAL_VPIS', ''),
                'total_cofins': nota.get('TOTAL_VCOFINS', ''),
            }
            
            # Aplicar as regras de negócio
            regras = aplicar_regras_negocio(nota, i)
            linha.update(regras)
            
            linhas.append(linha)
    
    return linhas

# ==============================================================================
# MAPEAMENTO PARA FORMATO DO RELATÓRIO FISCAL
# ==============================================================================

def mapear_para_formato_relatorio(linhas: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Mapeia os dados processados para o formato do relatorio_fiscal.xlsx
    """
    dados_mapeados = []
    
    for linha in linhas:
        registro = {
            # Colunas do relatório fiscal
            'Arquivo XML': linha['arquivo_xml'],
            'JSON': linha['json_completo_nfe'],
            'CNPJ/CPF Emissor': linha.get('emit_documento', ''),  
            'Razao Social Emissor': linha['emit_razao_social'],
            'CNPJ/CPF Destinatario': linha.get('dest_documento', ''),  
            'Razao Social Destinatario': linha['dest_razao_social'],
            'Classificacao / Produto': linha['item_descricao'],
            'NCM': linha.get('ncm', ''), 
            'MUN Emissor': linha['emit_municipio'],
            'UF Emissor': linha['emit_uf'],
            'MUN Destinatario': linha['dest_municipio'],
            'UF Destinatario': linha['dest_uf'],
            'ESTADUAL': linha['tipo_operacao'],
            'NATOP': linha['natureza_operacao'],
            'CFOP': linha['cfop'],
            'DESC CFOP': linha['desc_cfop'],
            'CONSUMIDOR FINAL': linha.get('consumidor_final', ''), 
            'COFINS': linha.get('tem_cofins', 'NAO'),  
            'Informacoes Adicionais': linha.get('info_adicionais', ''),  
        }
        
        dados_mapeados.append(registro)
    
    return pd.DataFrame(dados_mapeados)

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("="*80)
    print("GERADOR DE RELATÓRIO CUSTOMIZADO V2")
    print("="*80)
    
    # 1. Carregar dados
    print(f"\n1. Carregando dados de: {ARQUIVO_JSON}")
    with open(ARQUIVO_JSON, 'r', encoding='utf-8') as f:
        notas = json.load(f)
    print(f"   OK - {len(notas)} notas carregadas")
    
    # 2. Expandir notas para linhas (uma linha por item)
    print("\n2. Expandindo itens e aplicando regras de negocio...")
    linhas = expandir_notas_para_linhas(notas)
    print(f"   OK - {len(linhas)} linhas geradas")
    
    # 3. Mapear para formato do relatório fiscal
    print("\n3. Mapeando para formato do relatorio fiscal...")
    df = mapear_para_formato_relatorio(linhas)
    print(f"   OK - DataFrame criado com {len(df)} linhas e {len(df.columns)} colunas")
    
    # 4. Salvar em Excel
    print(f"\n4. Salvando relatorio em: {ARQUIVO_EXCEL}")
    df.to_excel(ARQUIVO_EXCEL, index=False)
    print("   OK - Relatorio salvo com sucesso!")
    
    
    return df

if __name__ == '__main__':
    df = main()
