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

# CST ICMS (Regime Normal - NF-e/NFC-e)
TABELA_CST_ICMS = {
    '00': 'Tributada integralmente',
    '10': 'Tributada e com cobrança do ICMS por substituição tributária',
    '20': 'Com redução da base de cálculo',
    '30': 'Isenta ou não tributada e com cobrança do ICMS por substituição tributária',
    '40': 'Isenta',
    '41': 'Não tributada',
    '50': 'Suspensão',
    '51': 'Diferimento',
    '60': 'ICMS cobrado anteriormente por substituição tributária',
    '70': 'Com redução de base de cálculo e cobrança do ICMS por substituição tributária',
    '90': 'Outras',
}

# CSOSN ICMS (Simples Nacional)
TABELA_CSOSN_ICMS = {
    '101': 'Tributada pelo Simples Nacional com permissão de crédito',
    '102': 'Tributada pelo Simples Nacional sem permissão de crédito',
    '103': 'Isenção do ICMS no Simples Nacional para faixa de receita bruta',
    '201': 'Tributada pelo Simples Nacional com permissão de crédito e com cobrança do ICMS por substituição tributária',
    '202': 'Tributada pelo Simples Nacional sem permissão de crédito e com cobrança do ICMS por substituição tributária',
    '203': 'Isenção do ICMS no Simples Nacional para faixa de receita bruta e com cobrança do ICMS por substituição tributária',
    '300': 'Imune',
    '400': 'Não tributada pelo Simples Nacional',
    '500': 'ICMS cobrado anteriormente por substituição tributária (substituído) ou por antecipação',
    '900': 'Outros (a critério da UF)',
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

def get_info_adicionais(nota: Dict[str, Any], item: Dict[str, Any], item_index: int = 0) -> Dict[str, Any]:
    """Consolida informações adicionais da nota (contribuinte/fisco) e do item."""
    info_contrib = nota.get('INF_CPL') or nota.get('INF_COMPLEMENTARES')
    info_fisco = nota.get('INF_FISCO')
    info_item = item.get('INFO_ADICIONAL')

    partes = []
    if info_contrib:
        partes.append(f"[CONTRIBUINTE]: {info_contrib}")
    if info_fisco:
        partes.append(f"[FISCO]: {info_fisco}")
    if info_item:
        item_num = item.get('NUMERO') or item_index + 1
        partes.append(f"[ITEM {item_num}]: {info_item}")

    return {'info_adicionais': ' | '.join(partes) if partes else ''}

def get_outros_impostos(item: Dict[str, Any]) -> Dict[str, Any]:
    """Identifica presença de impostos não convencionais e registra o nome da tag."""
    # Lista padrão de impostos conhecidos (tags _BLOCO que devem existir)
    impostos_padrao = {'ICMS_BLOCO', 'IPI_BLOCO', 'PIS_BLOCO', 'COFINS_BLOCO', 'ISSQN_BLOCO', 'ICMS_UFDEST_BLOCO'}
    
    # Coletar todos os campos _BLOCO presentes no item
    impostos_presentes = set()
    for key in item.keys():
        if key.endswith('_BLOCO'):
            impostos_presentes.add(key)
    
    # Identificar impostos não padrão
    outros_impostos = impostos_presentes - impostos_padrao
    
    # Verificar campo OUTRO_IMPOSTO (se vier preenchido do processador)
    outro_imposto_campo = item.get('OUTRO_IMPOSTO')
    
    if outros_impostos or outro_imposto_campo:
        # Extrair nomes das tags (remover _BLOCO)
        nomes_impostos = [imp.replace('_BLOCO', '') for imp in sorted(outros_impostos)]
        
        if nomes_impostos and outro_imposto_campo:
            descricao = ', '.join(nomes_impostos) + f', {outro_imposto_campo}'
        elif nomes_impostos:
            descricao = ', '.join(nomes_impostos)
        else:
            descricao = outro_imposto_campo
    else:
        descricao = 'NAO'
    
    return {
        'outros_impostos': descricao,
    }

def get_issqn_info(item: Dict[str, Any]) -> Dict[str, Any]:
    """Identifica presença de ISSQN no item (serviço) retornando SIM/NAO."""
    issqn_bloco = item.get('ISSQN_BLOCO')
    tem_issqn_flag = item.get('TEM_ISSQN')

    if issqn_bloco or tem_issqn_flag:
        tem_issqn = 'SIM'
    else:
        tem_issqn = 'NAO'

    return {
        'tem_issqn': tem_issqn,
    }

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

def _get_desc_cst_icms(cst):
    """Retorna a descrição do CST ICMS (2 dígitos) ou CSOSN (3 dígitos)."""
    if not cst:
        return 'N/A'
    
    cst_str = str(cst)
    
    # Se tem 3 dígitos, é CSOSN (Simples Nacional)
    if len(cst_str) == 3:
        return TABELA_CSOSN_ICMS.get(cst_str, f'CSOSN {cst_str}')
    # Se tem 2 dígitos, é CST (Regime Normal)
    else:
        return TABELA_CST_ICMS.get(cst_str, f'CST {cst_str}')

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

def get_tipi_aplicavel(item: Dict[str, Any]) -> Dict[str, Any]:
    """Identifica se o produto está sujeito à TIPI (Tabela de Incidência do IPI)."""
    ipi_bloco = item.get('IPI_BLOCO')
    ipi_cst = item.get('IPI_CST', '')
    
    # Se não tem IPI_BLOCO, não está sujeito à TIPI
    if not ipi_bloco:
        tem_tipi = 'NAO'
    # Se CST está em códigos de isento/suspenso, não é tributável
    elif str(ipi_cst) in ['52', '53', '54', '55']:
        tem_tipi = 'NAO'
    # Se tem IPI_BLOCO e CST não é isento, está sujeito
    else:
        tem_tipi = 'SIM'
    
    return {'tipi': tem_tipi}

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

def identificar_difal(nota: Dict[str, Any], item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identifica a incidência do DIFAL (Diferencial de Alíquota)
    com base nas regras:
    1. Presença do bloco ICMSUFDest (regra 19a)
    2. OU Se cumprir 3 requisitos (regra 19b):
        a) Destinatário = consumidor final (indFinal = 1)
        b) Operação interestadual (UF diferente)
        c) Destinatário não contribuinte do ICMS (indIEDest = 9)

    Args:
        dados_nota_json (dict): Dicionário contendo os dados gerais da NF-e
        e o bloco 'ITEMS'.

    Returns:
        bool: True se o DIFAL incide, False caso contrário.
    """
    
    # --- REGRA 19a: Presença do bloco ICMSUFDest ---
    
    # 1.1 Verifica nos totais (indica que houve cálculo na nota)
    # Procuramos por chaves que indicam a presença do cálculo de DIFAL no total.
    if nota.get("DIFAL_CONS_FINAL") == "1" and nota.get("DIFAL_DEST_UF") != nota.get("DIFAL_EMIT_UF"):
         return True
    
    # 1.2 Verifica por item (procurando o bloco em cada item)
    # Verifica se o bloco de campos de DIFAL do item está preenchido
    if item.get("ICMS_UFDEST_VBCUFDEST") or item.get("TEM_DIFAL") == "1":
        return True

    # --- REGRA 19b: Cumprimento dos 3 requisitos ---
    
    # 2.1 Verifica Destinatário = Consumidor Final
    is_consumidor_final = nota.get("CONSUMIDOR_FINAL") == "1"
    
    # 2.2 Verifica Operação Interestadual (UF diferentes)
    uf_emitente = nota.get("EMIT_UF")
    uf_destinatario = nota.get("DEST_UF")
    is_interestadual = uf_emitente is not None and uf_destinatario is not None and uf_emitente != uf_destinatario
    
    # 2.3 Verifica Destinatário Não Contribuinte (indIEDest = 9)
    # A tag indIEDest no XML (linha 61) tem o valor '9' para não-contribuinte.
    # No JSON você está usando "DEST_IND_IE_DEST".
    is_nao_contribuinte = nota.get("DEST_IND_IE_DEST") == "9"
    
    # 2.4 Retorna TRUE se as 3 condições forem atendidas
    if is_consumidor_final and is_interestadual and is_nao_contribuinte:
        return True
    
    # --- Se nenhuma das regras for atendida ---
    return False

# ==============================================================================
# FUNÇÃO PRINCIPAL: EXPANDIR ITENS E GERAR RELATÓRIO
# ==============================================================================

def montar_dataframe_notas(notas: List[Dict[str, Any]]) -> pd.DataFrame:
    """Monta DataFrame com ID, Numero Nota e JSON completo da nota."""
    dados = []
    
    index = 0
    for idx, nota in enumerate(notas, 1):
        items = nota.get('ITEMS', [])
        
        for item_idx, item in enumerate(items):
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
                "Transporte": get_transporte_info(nota).get('tem_transporte', ''),
            }
            info_produto = {
                'NCM': item.get('NCM', ''),
                'Material': item.get('XPROD', ''),
                'CFOP': get_cfop_info(item).get('cfop', ''),
                "Natureza": nota.get('NATUREZA_OPERACAO', ''),
                "ICMS": item.get('ICMS_BLOCO', '0.00'),
                "CST ICMS": item.get('ICMS_CST') or item.get('ICMS_CSOSN', ''),
                "DESC CST ICMS": _get_desc_cst_icms(item.get('ICMS_CST') or item.get('ICMS_CSOSN', '')),
                "IPI_CST": get_ipi_status(item).get('ipi_status', ''),
                "TIPI": get_tipi_aplicavel(item).get('tipi', 'NAO'),
                "CONFINS": get_cofins_status(item).get('tem_cofins', ''),
                "Sujeito a ISS?": get_issqn_info(item).get('tem_issqn', ''),
                "Outros Impostos": get_outros_impostos(item).get('outros_impostos', ''),
                "Infos Adicionais": get_info_adicionais(nota, item, item_idx).get('info_adicionais', ''),
                "DIFAL": identificar_difal(nota, item),
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
