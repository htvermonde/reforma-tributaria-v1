import json
import pandas as pd
from typing import Dict, Any, List

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================

ARQUIVO_JSON = 'output/resposta_notas_v2.json'
ARQUIVO_EXCEL = 'output/relatorio_customizado_v3.xlsx'

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

# Modalidades de Frete
TABELA_MOD_FRETE = {
    '0': 'Por Conta do Emitente',
    '1': 'Por Conta do Destinatário',
    '2': 'Por Conta de Terceiro',
    '3': 'Por Conta de Terceiro (Comodato)',
    '4': 'Sem Movimento Físico',
    '9': 'Sem Frete',
}

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def get_tipo_operacao(nota: Dict[str, Any]) -> Dict[str, Any]:
    """Classifica como Entrada ou Saída."""
    tipo_nf = nota.get('TIPO_NF', '')
    return {'tipo_operacao': 'ENTRADA' if tipo_nf == '0' else 'SAIDA'}

def get_documento_destinatario(nota: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai CNPJ/CPF e Razão Social do Destinatário."""
    dest_cnpj = nota.get('DEST_CNPJ')
    dest_cpf = nota.get('DEST_CPF')
    return {
        'dest_documento': dest_cnpj if dest_cnpj else dest_cpf,
        'dest_tipo_pessoa': 'PJ' if dest_cnpj else 'PF',
        'dest_razao_social': nota.get('DEST_RAZAO_SOCIAL', ''),
    }

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

def _get_desc_cfop(cfop):
    """Retorna a descrição do CFOP."""
    return TABELA_CFOP.get(str(cfop), f'CFOP {cfop}')

def get_transporte_info(nota: Dict[str, Any]) -> Dict[str, Any]:
    """Identifica modalidade de transporte e retorna a descrição."""
    mod_frete = nota.get('TRANSP_MOD_FRETE')
    
    if mod_frete is None or mod_frete == '':
        tem_transporte = 'Não Informado'
    else:
        tem_transporte = TABELA_MOD_FRETE.get(str(mod_frete), f'Modalidade {mod_frete}')
    
    return {'tem_transporte': tem_transporte}

def get_cfop_info(item: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai CFOP e descrição."""
    cfop = item.get('CFOP', '')
    return {
        'cfop': cfop,
        'desc_cfop': _get_desc_cfop(cfop),
    }

def analisar_icms_itens(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identifica o tipo de ICMS e suas subdivisões para um item.
    Recebe o dict do item diretamente.
    """
    
    resultado_item = {
        "TIPO_ICMS": "Não Aplicável/Não Encontrado",
        "CST_CSOSN": "N/A",
        "REGIME": "",
        "QTD_BC_MONO": "",
        "ALIQUOTA_AD_REM": "",
        "VALOR_ICMS_RETIDO": "",
        "VBCST": "",
        "PICMSST": "",
        "VICMSST": "",
        "VBC": "",
        "PICMS": "",
        "VICMS": "",
        "ORIGEM_MERCADORIA": ""
    }

    # 1. Identifica o bloco de tributação do ICMS (Ex: ICMS00, ICMS60, ICMS61, ICMSSN102)
    bloco_icms = item.get("ICMS_BLOCO")
    cst_csosn = item.get("ICMS_CST") or item.get("ICMS_CSOSN")

    if bloco_icms:
        resultado_item["TIPO_ICMS"] = bloco_icms
        resultado_item["CST_CSOSN"] = cst_csosn if cst_csosn else "N/A"

        # 2. Interpretação das subdivisões com base no bloco/CST
        
        # Subdivisão para ICMS Monofásico (Combustíveis - Novo no XML)
        if bloco_icms == "ICMS61":
            resultado_item["REGIME"] = "Monofásico - ICMS Retido Anteriormente"
            resultado_item["QTD_BC_MONO"] = item.get("ICMS_QTD_BC_MONO_RET", "0.00")
            resultado_item["ALIQUOTA_AD_REM"] = item.get("ICMS_ALIQUOTA_MONO_RET", "0.00")
            resultado_item["VALOR_ICMS_RETIDO"] = item.get("ICMS_VALOR_MONO_RET", "0.00")

        # Subdivisão para ICMS ST (Substituição Tributária - Comum em outros casos)
        elif "ICMSST" in bloco_icms or cst_csosn in ["10", "60", "70", "500"]:
            resultado_item["REGIME"] = "Substituição Tributária (ST)"
            resultado_item["VBCST"] = item.get("ICMS_VBCST", "0.00")
            resultado_item["PICMSST"] = item.get("ICMS_PICMSST", "0.00")
            resultado_item["VICMSST"] = item.get("ICMS_VICMSST", "0.00")
        
        # Subdivisão para ICMS Normal (Tributado Integralmente)
        elif cst_csosn == "00":
            resultado_item["REGIME"] = "Tributado Integralmente"
            resultado_item["VBC"] = item.get("ICMS_VBC", "0.00")
            resultado_item["PICMS"] = item.get("ICMS_PICMS", "0.00")
            resultado_item["VICMS"] = item.get("ICMS_VICMS", "0.00")

        # Adicione outras condições (ICMS20, ICMSSN102, etc.) conforme a necessidade
        
        # Adiciona a Origem em todos os casos
        origem = item.get("ICMS_ORIGEM")
        if origem:
            origens = {"0": "Nacional", "1": "Estrangeira - Importação Direta", "2": "Estrangeira - Adquirida no Brasil"}
            resultado_item["ORIGEM_MERCADORIA"] = origens.get(origem, "Outra/Desconhecida")

    return resultado_item

def _get_desc_cst_ipi(cst):
    """Retorna a descrição do CST IPI."""
    return TABELA_CST_IPI.get(str(cst), f'CST {cst}')

def get_ipi_status(item: Dict[str, Any]) -> Dict[str, Any]:
    """Classifica IPI como tributado, isento ou sem aplicação."""
    cst_ipi = item.get('IPI_CST', '')
    
    if not cst_ipi or cst_ipi == '':
        status = 'SEM_IPI'
        descricao = 'Não se aplica'
    elif str(cst_ipi) in ['50', '51']:
        status = 'TRIBUTADO'
        descricao = _get_desc_cst_ipi(cst_ipi)
    elif str(cst_ipi) in ['52', '53', '54', '55', '99']:
        status = 'ISENTO'
        descricao = _get_desc_cst_ipi(cst_ipi)
    else:
        status = 'OUTROS'
        descricao = _get_desc_cst_ipi(cst_ipi)
    
    return {
        'ipi_status': status,
        'ipi_descricao': descricao,
        'cst_ipi': cst_ipi,
        'valor_ipi': item.get('IPI_VIPI', '0.00'),
    }

def _get_desc_cst_pis_cofins(cst):
    """Retorna a descrição do CST PIS/COFINS."""
    return TABELA_CST_PIS_COFINS.get(str(cst), f'CST {cst}')

def get_cofins_status(item: Dict[str, Any]) -> Dict[str, Any]:
    """ Classifica COFINS em 4 categorias."""
    cst_cofins = item.get('COFINS_CST', '')
    cofins_isento_list = ['07', '08', '09']
    cofins_tributado_list = ['01', '02', '03', '04', '05', '06']
    
    if not cst_cofins:
        tem_cofins = 'NAO'
        status = 'Não mapeado'
    elif str(cst_cofins) in cofins_isento_list:
        tem_cofins = 'NAO'
        status = _get_desc_cst_pis_cofins(cst_cofins) + ' (Isento/Suspenso)'
    elif str(cst_cofins) in cofins_tributado_list:
        tem_cofins = 'SIM'
        status = _get_desc_cst_pis_cofins(cst_cofins)
    else:
        tem_cofins = 'OUTRO'
        status = f'CST {cst_cofins} (não classificado)'
    
    cst_pis = item.get('PIS_CST', '')
    
    return {
        'tem_cofins': tem_cofins,
        'status_cofins': status,
        'cst_cofins': cst_cofins,
        'cst_pis': cst_pis,
        'desc_cst_pis': _get_desc_cst_pis_cofins(cst_pis),
    }



# ==============================================================================
# FUNÇÃO PRINCIPAL: EXPANDIR ITENS E GERAR RELATÓRIO
# ==============================================================================

def montar_dataframe_notas(notas: List[Dict[str, Any]]) -> pd.DataFrame:
    """Monta DataFrame com ID, Numero Nota e JSON completo da nota."""
    dados = []
    
    index = 0
    for idx, nota in enumerate(notas, 1):
        items = nota.get('ITEMS', [])
        
        for item in items:
            info_nota = {
                'ID': index,
                'Numero Nota': nota.get('NUMERO_NF', ''),
                'JSON da nota': json.dumps(nota, ensure_ascii=False, indent=2),
                "Tipo": nota.get('TIPO_DOCUMENTO', ''),
                "CNPJ/CPF Emissor": nota.get('EMIT_CNPJ') if nota.get('EMIT_CNPJ') else nota.get('EMIT_CPF', ''),
                "Razão Social Emissor": nota.get('EMIT_RAZAO_SOCIAL', ''),
                "CNPJ/CPF Destinatário": nota.get('DEST_CNPJ') if nota.get('DEST_CNPJ') else nota.get('DEST_CPF', ''),
                "Razão Social Destinatário": nota.get('DEST_RAZAO_SOCIAL', ''),
                "UF Emissor": nota.get('EMIT_UF', ''),
                "UF Destinatário": nota.get('DEST_UF', ''),
                "Operação": get_tipo_operacao(nota).get('tipo_operacao', ''),
                "Consumidor Final": get_consumidor_final(nota).get('consumidor_final', ''),
                "Tem Transporte": get_transporte_info(nota).get('tem_transporte', ''),
            }
            info_produto = {
                'NCM': item.get('NCM', ''),
                'CFOP': get_cfop_info(item).get('cfop', ''),
                "Natureza": nota.get('NATUREZA_OPERACAO', ''),
                "ICMS": item.get('ICMS_BLOCO', '0.00'),
                "ICMS CST": item.get('ICMS_CST', ''),
                "IPI_CST": get_ipi_status(item).get('ipi_status', ''),
                "CONFINS": get_cofins_status(item).get('tem_cofins', ''),
            }
            
            # Análise ICMS
            # info_icms = analisar_icms_itens(item)
            
            # resultado = {**info_nota, **info_produto, **info_icms}
            resultado = {**info_nota, **info_produto}
            dados.append(resultado)
            index += 1
    
    return pd.DataFrame(dados)


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
    
    # 2. Montar DataFrame
    print("\n2. Montando DataFrame...")
    df = montar_dataframe_notas(notas)
    print(f"   OK - {len(df)} linhas criadas")
    
    # 3. Salvar em Excel
    print(f"\n3. Salvando relatorio em: {ARQUIVO_EXCEL}")
    df.to_excel(ARQUIVO_EXCEL, index=False)
    print("   OK - Relatorio salvo com sucesso!")
    
    
    return df

if __name__ == '__main__':
    df = main()
