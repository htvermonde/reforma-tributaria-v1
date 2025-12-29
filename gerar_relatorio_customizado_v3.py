import json
import pandas as pd
from typing import Dict, Any, List

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================

ARQUIVO_JSON = 'output/resposta_notas.json'
ARQUIVO_EXCEL = 'output/relatorio_customizado.xlsx'
ARQUIVO_BASE_CFOP = 'base/base_cfop.xlsx'

# Carregar base CFOP
DF_BASE_CFOP = pd.read_excel(ARQUIVO_BASE_CFOP)

# ==============================================================================
# TABELAS DE DE-PARA
# ==============================================================================


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

def get_transporte_info(nota: Dict[str, Any]) -> Dict[str, Any]:
    """Identifica modalidade de transporte e retorna a descrição."""
    mod_frete = nota.get('TRANSP_MOD_FRETE')
    
    if mod_frete is None or mod_frete == '':
        tem_transporte = 'Não Informado'
    else:
        tem_transporte = TABELA_MOD_FRETE.get(str(mod_frete), f'Modalidade {mod_frete}')
    
    return {'tem_transporte': tem_transporte}

def _get_desc_cfop(cfop):
    """Retorna a descrição do CFOP."""
    if not cfop or cfop == '':
        return 'CFOP não informado'
    
    cfop_str = str(cfop).strip()
    # Compara convertendo ambos os lados para string e removendo espaços
    resultado = DF_BASE_CFOP[DF_BASE_CFOP['Codigo CFOP'].astype(str).str.strip() == cfop_str]
    if not resultado.empty:
        return resultado.iloc[0]['Descricao']
    return f'CFOP {cfop}'

def get_cfop_info(item: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai CFOP e descrição."""
    cfop = item.get('CFOP', '')
    return {
        'cfop': cfop,
        'desc_cfop': _get_desc_cfop(cfop),
    }

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
    
    return {
        'ipi_cst':ipi_cst,
        'tipi': tem_tipi
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
        'cst_cofins': cst_cofins,
        'tem_cofins': tem_cofins,
        'status_cofins': status,
        'cst_pis': cst_pis,
        'desc_cst_pis': _get_desc_cst_pis_cofins(cst_pis),
    }

def get_issqn_info(item: Dict[str, Any]) -> Dict[str, Any]:
    """Identifica presença de ISSQN no item (serviço) retornando SIM/NAO."""
    issqn_bloco = item.get('ISSQN_BLOCO')
    tem_issqn_flag = item.get('TEM_ISSQN')

    if issqn_bloco is not None or tem_issqn_flag is not None:
        tem_issqn = 'SIM'
    else:
        tem_issqn = 'NAO'

    return {
        'tem_issqn': tem_issqn,
    }

def identificar_difal(nota: Dict[str, Any], item: Dict[str, Any]) -> Dict[str, Any]:
    # 1. Inicializa a variável para evitar erro de escopo
    tem_difal = False
    motivo = "Sem incidência"

    # Extração de dados com valores padrão para evitar None
    ind_final = str(nota.get("CONSUMIDOR_FINAL", "0"))
    ind_ie_dest = str(nota.get("DEST_IND_IE_DEST", ""))
    uf_emit = nota.get("DIFAL_EMIT_UF")
    uf_dest = nota.get("DIFAL_DEST_UF")
    cfop = str(item.get("CFOP", ""))
    
    is_interestadual = uf_emit and uf_dest and uf_emit != uf_dest
    is_saida = cfop.startswith("6") # Operações interestaduais de saída

    # --- REGRA 1: Presença Explícita do Bloco (EC 87/2015) ---
    if item.get("DIFAL_UFDEST_BLOCO") or item.get("TEM_DIFAL") == "1":
        tem_difal = True
        motivo = "Bloco ICMSUFDest presente no item"

    # --- REGRA 2: Requisitos para Não Contribuinte ---
    elif is_interestadual and is_saida and ind_final == "1" and ind_ie_dest == "9":
        tem_difal = True
        motivo = "Operação Interestadual, Consumidor Final Não Contribuinte"

    # --- REGRA 3: Requisitos para Contribuinte (Uso/Consumo/Ativo) ---
    # Nota: O DIFAL aqui pode estar no campo vICMSST
    elif is_interestadual and is_saida and ind_final == "1" and ind_ie_dest == "1":
        tem_difal = True
        motivo = "DIFAL Contribuinte (Uso/Consumo ou Ativo Imobilizado)"

    return {
        "tem_difal": tem_difal,
        "motivo": motivo,
        "debug": {
            "interestadual": is_interestadual,
            "consumidor_final": ind_final,
            "ind_ie_dest": ind_ie_dest,
            "cfop": cfop
        }
    }

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


def gerar_cenario(nota: Dict[str, Any], item: Dict[str, Any]) -> str:
    """Gera uma descrição resumida do cenário da operação para visão geral rápida."""
    partes = []
    
    # 1. Tipo de documento
    tipo_doc = nota.get('TIPO_DOCUMENTO', 'N/A')
    if tipo_doc:
        partes.append(tipo_doc.upper())
    
    # 2. Tipo de operação
    tipo_op = get_tipo_operacao(nota).get('tipo_operacao', 'N/A')
    partes.append(tipo_op)
    
    # 3. Consumidor final ou B2B
    # cons_final = get_consumidor_final(nota).get('consumidor_final', 'NAO')
    # partes.append('CONS.FINAL' if cons_final == 'SIM' else 'B2B')
    
    # 4. Transporte
    transporte = get_transporte_info(nota).get('tem_transporte', '')
    if transporte and transporte != 'Não Informado':
        # Abrevia o tipo de transporte
        if 'Emitente' in transporte:
            partes.append('FRETE-EMIT')
        elif 'Destinatário' in transporte:
            partes.append('FRETE-DEST')
        elif 'Terceiro' in transporte:
            partes.append('FRETE-3º')
        elif 'Sem Frete' in transporte:
            partes.append('SEM-FRETE')
    
    # 5. NATOP (resumida)
    natop = nota.get('NATUREZA_OPERACAO', '')
    if natop:
        # Pega as primeiras 20 caracteres da NATOP
        natop_resumida = natop[:25] + '...' if len(natop) > 25 else natop
        partes.append(natop_resumida)
    
    # 6. CFOP
    # cfop = item.get('CFOP', '')
    # if cfop:
    #     partes.append(f"CFOP-{cfop}")
    
    # 7. Todos os impostos
    todos_impostos = item.get('TODOS_IMPOSTOS', '')
    if todos_impostos:
        partes.append(f"[{todos_impostos}]")
    
    # 8. Regime tributário ICMS
    cst_icms = item.get('ICMS_CST') or item.get('ICMS_CSOSN', '')
    if cst_icms:
        if str(cst_icms) in ['10', '60', '70']:
            partes.append('ICMS-ST')
        elif str(cst_icms) == '61':
            partes.append('ICMS-MONO')
        elif str(cst_icms) in ['40', '41', '50']:
            partes.append('ICMS-ISENTO')
        elif len(str(cst_icms)) == 3:  # CSOSN
            partes.append('SIMPLES')
        else:
            partes.append('ICMS-NORMAL')
    
    # 9. IPI
    # ipi_status = get_ipi_status(item).get('ipi_status', '')
    # if ipi_status == 'TRIBUTADO':
    #     partes.append('COM-IPI')
    
    # # 10. DIFAL
    # tem_difal = identificar_difal(nota, item).get('tem_difal', False)
    # if tem_difal:
    #     partes.append('COM-DIFAL')
    
    # # 11. ISS
    # tem_iss = get_issqn_info(item).get('tem_issqn', 'NAO')
    # if tem_iss == 'SIM':
    #     partes.append('COM-ISS')
    
    return ' | '.join(partes)


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
                "Cenario": gerar_cenario(nota, item),
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
                'Classificação/Produto': item.get('XPROD', ''),
                "NATOP": nota.get('NATUREZA_OPERACAO', ''),               
                'CFOP': get_cfop_info(item).get('cfop', ''),
                'DESC CFOP': get_cfop_info(item).get('desc_cfop', ''),

                "CST ICMS": item.get('ICMS_CST') or item.get('ICMS_CSOSN', ''),
                "DESC CST ICMS": _get_desc_cst_icms(item.get('ICMS_CST') or item.get('ICMS_CSOSN', '')),
                "%ICMS Normal": item.get('ICMS_PICMS', '0'),
                "ICMS VBC": item.get('ICMS_VBC', '0'),
                
                "CST IPI": get_ipi_status(item).get('cst_ipi', ''),
                "ENQUADRAMENTO IPI": get_ipi_status(item).get('ipi_status', ''),
                "%IPI": get_ipi_status(item).get('valor_ipi', ''),
                "TIPI": get_tipi_aplicavel(item).get('tipi', 'NAO'),

                "CST PIS": item.get('PIS_CST', ''),
                "DESC CST PIS": _get_desc_cst_pis_cofins(item.get('PIS_CST', '')),
                "%PIS": item.get('PIS_PPIS', ''),
                
                "CST COFINS": get_cofins_status(item).get('cst_cofins', ''),
                "DESC CST COFINS": get_cofins_status(item).get('tem_cofins', ''),
                "%CONFINS": item.get('COFINS_PCOFINS', ''),
                
                "Sujeito a ISS?": get_issqn_info(item).get('tem_issqn', ''),
                
                "DIFAL": identificar_difal(nota, item).get('tem_difal', False),
                "DIFAL motivo": identificar_difal(nota, item).get('motivo', ''),
                "DIFAL interestadual": identificar_difal(nota, item).get('debug', {}).get('interestadual', False),
                "DIFAL consumidor final": identificar_difal(nota, item).get('debug', {}).get('consumidor_final', ''),
                "DIFAL ind_ie_dest": identificar_difal(nota, item).get('debug', {}).get('ind_ie_dest', ''),
                "DIFAL cfop": identificar_difal(nota, item).get('debug', {}).get('cfop', ''),
                
                "Outros Impostos": item.get('OUTROS_IMPOSTOS', ''),
                "Todos Impostos": item.get('TODOS_IMPOSTOS', ''),
                "Infos Adicionais": get_info_adicionais(nota, item, item_idx).get('info_adicionais', ''),
                
            }
            
            # Análise ICMS
            # info_icms = analisar_icms_itens(item)S
            
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
