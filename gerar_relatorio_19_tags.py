
import os
import pandas as pd
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

def organizar_operacao(xml_path: str) -> str:
    """
    Identifica se a nota é de Entrada ou Saída com base na tag <tpNF>:
    0 = Saída (Remetente)
    1 = Entrada (Destinatário)
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = '{http://www.portalfiscal.inf.br/nfe}'
        # busca o nó infNFe (com e sem namespace)
        infnfe = root.find(f'.//{ns}infNFe')
        if infnfe is None:
            infnfe = root.find('.//infNFe')
        tpNF = None
        if infnfe is not None:
            # Priorizar o caminho correto: infNFe/ide/tpNF (com namespace)
            tpNF = infnfe.find(f'{ns}ide/{ns}tpNF')
            # fallback sem namespace explicitado
            if tpNF is None:
                tpNF = infnfe.find('ide/tpNF')
            # último recurso: buscar qualquer tpNF dentro de infNFe
            if tpNF is None:
                tpNF = infnfe.find(f'{ns}tpNF')
            if tpNF is None:
                tpNF = infnfe.find('tpNF')
        if tpNF is not None and tpNF.text:
            valor = tpNF.text.strip()
            if valor == '0':
                return 'Saída'
            elif valor == '1':
                return 'Entrada'
    except Exception:
        pass
    return ''

def identificar_consumidor_final(xml_path: str) -> str:
    """
    Identifica se a nota é para Consumidor Final.

    Regras (retorna 'Sim' quando uma das condições for verdadeira):
    - Modelo = 65 (NFC-e)
    - indFinal = 1
    - indIEDest = 9
    - Para NF-e (mod 55): tag <IE> do destinatário ausente ou com valor 'ISENTO'
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = '{http://www.portalfiscal.inf.br/nfe}'
        infnfe = root.find(f'.//{ns}infNFe')
        if infnfe is None:
            infnfe = root.find('.//infNFe')
        if infnfe is None:
            return 'Não'

        # modelo (mod)
        mod = infnfe.find(f'{ns}ide/{ns}mod') or infnfe.find('ide/mod') or infnfe.find(f'{ns}mod') or infnfe.find('mod')
        if mod is not None and mod.text and mod.text.strip() == '65':
            return 'Sim'

        # indFinal
        indFinal = infnfe.find(f'{ns}ide/{ns}indFinal') or infnfe.find('ide/indFinal') or infnfe.find(f'{ns}indFinal') or infnfe.find('indFinal')
        if indFinal is not None and indFinal.text and indFinal.text.strip() == '1':
            return 'Sim'

        # indIEDest
        indIEDest = infnfe.find(f'{ns}dest/{ns}indIEDest') or infnfe.find('dest/indIEDest') or infnfe.find(f'{ns}indIEDest') or infnfe.find('indIEDest')
        if indIEDest is not None and indIEDest.text and indIEDest.text.strip() == '9':
            return 'Sim'

        # Para NF-e (mod 55): verificar IE do destinatário ausente ou 'ISENTO'
        # buscar mod (já feito acima) para saber se é 55; se mod não disponível, ainda verificamos IE
        ie_node = infnfe.find(f'{ns}dest/{ns}IE') or infnfe.find('dest/IE') or infnfe.find(f'{ns}IE') or infnfe.find('IE')
        ie_text = ie_node.text.strip() if ie_node is not None and ie_node.text else ''
        # Se IE ausente (string vazia) ou contém 'ISENTO' -> consumidor final (quando aplicável)
        if not ie_text or ie_text.upper() == 'ISENTO':
            # se mod é None ou mod == '55' consideramos NF-e
            if mod is None or (mod is not None and mod.text and mod.text.strip() == '55'):
                return 'Sim'

    except Exception:
        pass
    return 'Não'

def identificar_natureza_operacao(cfop: str) -> str:
    """
    Identifica a natureza da operação com base no CFOP do item.

    Regras:
    - Ler o CFOP de 4 dígitos.
    - Analisar o primeiro dígito:
      * 1,2,3 → Entrada
      * 5,6,7 → Saída
      * caso contrário → Outros

    Retorna uma string no formato '<Natureza> (CFOP <cfop>)'.
    """
    if not cfop:
        return ''
    # Normaliza: remove espaços e pontos, pega apenas os dígitos iniciais
    code = ''.join(ch for ch in cfop if ch.isdigit())
    if not code:
        return ''
    first = code[0]
    if first in ('1', '2', '3'):
        natureza = 'Entrada'
    elif first in ('5', '6', '7'):
        natureza = 'Saída'
    else:
        natureza = 'Outros'
    return f"{natureza} (CFOP {cfop})"

def identificar_tipo(xml_path: str) -> str:
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = root.tag.split('}')[0].strip('{') if '}' in root.tag else ''
        # 1. Se a raiz for NFe e o namespace padrão, pode ser mercadoria
        if root.tag.endswith('NFe') and ns == 'http://www.portalfiscal.inf.br/nfe':
            mod = root.find('.//{http://www.portalfiscal.inf.br/nfe}ide/{http://www.portalfiscal.inf.br/nfe}mod')
            if mod is not None:
                if mod.text == '57':
                    return 'Serviço (CTe)'
                if mod.text in ['55', '65']:
                    return 'Mercadoria'
            ncm = root.find('.//{http://www.portalfiscal.inf.br/nfe}NCM')
            if ncm is not None and ncm.text:
                return 'Mercadoria'
            issqn = root.find('.//{http://www.portalfiscal.inf.br/nfe}ISSQN')
            if issqn is not None and ncm is None:
                return 'Serviço'
            return 'Mercadoria'
        else:
            return 'Serviço'
    except Exception:
        return 'Indefinido'

def extrair_dados(xml_path: str) -> List[Dict[str, Any]]:
    """Extrai dados do XML e retorna uma lista de linhas, uma por item (det).

    Cada linha contém os campos de nível de nota repetidos e os campos do item
    (`NCM`, `CFOP`)."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = '{http://www.portalfiscal.inf.br/nfe}'
        infnfe = root.find(f'.//{ns}infNFe')
        if infnfe is None:
            infnfe = root.find('.//infNFe')

        def get_text(path):
            node = infnfe.find(path) if infnfe is not None else None
            return node.text.strip() if node is not None and node.text else ''

        # Campos de nível de nota
        base = {
            'Tipo': identificar_tipo(xml_path),
            'CNPJ Emissor': get_text(f'{ns}emit/{ns}CNPJ'),
            'Razão Social Emissor': get_text(f'{ns}emit/{ns}xNome'),
            'CNPJ Destinatario': get_text(f'{ns}dest/{ns}CNPJ'),
            'Razão Social Destinatario': get_text(f'{ns}dest/{ns}xNome'),
            'UF do Emissor': get_text(f'{ns}emit/{ns}enderEmit/{ns}UF'),
            'UF do Destinatario': get_text(f'{ns}dest/{ns}enderDest/{ns}UF'),
            'Operação': organizar_operacao(xml_path),
            'Consumidor Final': identificar_consumidor_final(xml_path)
        }

        # Encontrar itens (det)
        dets = []
        if infnfe is not None:
            dets = infnfe.findall(f'{ns}det') or infnfe.findall('det')

        linhas: List[Dict[str, Any]] = []
        if not dets:
            # Nenhum item encontrado: retorna uma linha com NCM/CFOP vazios
            row = dict(base)
            row.update({'NCM': '', 'CFOP': ''})
            linhas.append(row)
            return linhas

        for det in dets:
            prod = det.find(f'{ns}prod') or det.find('prod')
            ncm_node = prod.find(f'{ns}NCM') if prod is not None else None
            if ncm_node is None and prod is not None:
                ncm_node = prod.find('NCM')
            cfop_node = prod.find(f'{ns}CFOP') if prod is not None else None
            if cfop_node is None and prod is not None:
                cfop_node = prod.find('CFOP')
            ncm = ncm_node.text.strip() if ncm_node is not None and ncm_node.text else ''
            cfop = cfop_node.text.strip() if cfop_node is not None and cfop_node.text else ''

            row = dict(base)
            # calcular natureza por item (com base no CFOP do item)
            natureza = identificar_natureza_operacao(cfop)
            row.update({'Natureza da Operação': natureza, 'NCM': ncm, 'CFOP': cfop})
            linhas.append(row)

        return linhas
    except Exception:
        return []

def gerar_relatorio_xml(pasta_xml: str, output_path: str):
    linhas: List[Dict[str, Any]] = []
    for nome_arquivo in os.listdir(pasta_xml):
        if nome_arquivo.lower().endswith('.xml'):
            caminho_xml = os.path.join(pasta_xml, nome_arquivo)
            dados = extrair_dados(caminho_xml)
            # extrair_dados agora retorna uma lista de linhas (uma por item). Suporta
            # também dicts por compatibilidade, então tratamos ambos os casos.
            if isinstance(dados, list):
                linhas.extend(dados)
            elif isinstance(dados, dict):
                linhas.append(dados)
    df = pd.DataFrame(linhas, columns=[
        'Tipo', 'CNPJ Emissor', 'Razão Social Emissor', 'CNPJ Destinatario',
        'Razão Social Destinatario', 'UF do Emissor', 'UF do Destinatario', 'Natureza da Operação', 'NCM', 'CFOP', 'Operação', 'Consumidor Final'
    ])
    df.to_excel(output_path, index=False)
    print(f'Relatório gerado em: {output_path}')

if __name__ == '__main__':
    pasta_xml = 'reading_notes/unificado'  # Altere conforme necessário
    output_path = 'output/relatorio_notas.xlsx'  # Altere conforme necessário
    gerar_relatorio_xml(pasta_xml, output_path)
