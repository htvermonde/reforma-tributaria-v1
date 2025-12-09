
import os
import pandas as pd
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import re

# ==============================================================================
# 1. CONFIGURAÇÕES CONTROLADAS POR VARIÁVEIS
# ==============================================================================

# Caminho da pasta que contém os arquivos XML de entrada
XML_FOLDER_PATH = os.path.join(os.path.dirname(__file__), 'reading_notes', 'potencial')

# Nome do arquivo Excel de saída
OUTPUT_FILE_PATH = 'output/relatorio_fiscal.xlsx'

# ==============================================================================
# 2. CLASSE DE MAPEAMENTO E PROCESSAMENTO
# ==============================================================================

class NFeMapper:
    """
    Classe responsável por mapear dados de XMLs de NF-e para uma estrutura
    de dados (DataFrame do Pandas), conforme o layout do relatório fiscal.
    """
    
    def __init__(self):
        """
        Define o mapeamento das colunas do relatório para as tags XPath do XML.
        """
        self.nsmap = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        self.mapping: Dict[str, str] = {
            # 1. CAMPOS DE IDENTIFICAÇÃO E LOCALIZAÇÃO (CABECALHO)
            'CNPJ FILIAL': 'dest/CNPJ',
            'Classificação / Produto': 'cProd',
            'MunIni': 'emit/enderEmit/xMun',
            'Ufini': 'emit/enderEmit/UF',
            'MunFim': 'dest/enderDest/xMun',
            'Uffim': 'dest/enderDest/UF',

            # 2. CAMPOS OPERACIONAIS
            'ESTADUAL': 'emit/IE',
            'Municipal': 'emit/enderEmit/xMun',
            'NATOP': 'ide/natOp',
            'CFOP': 'CFOP',
            'DESC CFOP': 'xProd',
            'CONSUMIDOR FINAL': 'ide/indFinal',

            # 3. CAMPOS DE ICMS (POR ITEM)
            'CST ICMS': 'CST',
            'DESC CST ICMS': 'xProd',
            '%ICMS Normal': 'pICMS',
            'Base Normal': 'vBC',
            '% ICMS Outra UF': '',
            'Base ICMS Outra UF': '',

            # 4. CAMPOS DE DEDUÇÃO E INFORMAÇÕES ADICIONAIS (COMPLEXOS)
            'Frete Pauta': 'infCpl',
            'Dedução de ICMS': 'infCpl',
            'Isenção ICMS': 'infCpl',
            'Justificativa ICMS': 'infCpl',
            'Mensagem Legal do imposto': 'infCpl',
            'Obs': 'infNFe/infAdic/infCpl',
        }

    def _extract_icms_st_from_infcpl(self, infcpl_text: str, product_name: str) -> str:
        """
        Extrai BC e Valor do ICMS ST retido do texto de Informações Complementares.
        
        A lógica de extração é baseada nos nomes dos produtos (S500 e GASOLINA COMUM) 
        que estão referenciados no texto:
        S500 ICMS RETIDO OPER. ANT. P/ REF. BASE DE CALCULO DO ICMS ST R$ 21.592,00 - ICMS ST R$ R$ 3.238,80. 
        GASOLINA COMUM ICMS RETIDO OPER. ANT. P/ REF. BASE DE CALCULO DO ICMS ST R$ 30.117,00 - ICMS ST R$ R$ 5.421,06.
        """
        if not infcpl_text:
            return ''

        # Normaliza o texto para facilitar a busca (remove quebras de linha e espaços duplos)
        text = re.sub(r'\s+', ' ', infcpl_text.upper()).strip()
        
        # 1. Identifica o produto para buscar o trecho correto
        if 'DIESEL B S500' in product_name.upper():
            # Padrão para Diesel S500
            pattern = r'S500 ICMS RETIDO.*?BASE DE CALCULO DO ICMS ST R\$ ([\d\.,]+) - ICMS ST R\$ R\$ ([\d\.,]+)\.'
        elif 'GASOLINA COMUM' in product_name.upper():
            # Padrão para Gasolina Comum
            pattern = r'GASOLINA COMUM ICMS RETIDO.*?BASE DE CALCULO DO ICMS ST R\$ ([\d\.,]+) - ICMS ST R\$ R\$ ([\d\.,]+)\.'
        else:
            return 'Não encontrado no InfCpl'
            
        match = re.search(pattern, text)
        
        if match:
            bc_st = match.group(1).replace('.', '').replace(',', '.') # BC ST
            v_st = match.group(2).replace('.', '').replace(',', '.') # Valor ST
            
            # Retorna no formato: BC_ST: Valor (vST: Valor)
            return f'BCST R$ {bc_st}; VST R$ {v_st}'
        
        return 'Não encontrado no InfCpl'

    def extract_value(self, element: ET.Element, xpath: str) -> str:
        """Extrai valor usando XPath relativo/caminho, tratando tags simples e caminhos, com namespace."""
        if not xpath:
            return ''
        try:
            # Se for caminho (ex: emit/CNPJ), converte para XPath com namespace
            if '/' in xpath:
                path_parts = xpath.split('/')
                ns_xpath = './' + '/'.join(f'nfe:{p}' for p in path_parts)
                node = element.find(ns_xpath, self.nsmap)
                if node is not None and node.text:
                    return node.text
            else:
                # Tag simples (ex: cProd)
                node = element.find(f'nfe:{xpath}', self.nsmap)
                if node is not None and node.text:
                    return node.text
                # Busca por tag simples em subelementos
                for sub in element.iter():
                    if sub.tag.endswith(xpath) and sub.text:
                        return sub.text
            return ''
        except Exception:
            return ''

    def process_xml_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Processa um único arquivo XML, extraindo os dados de cada item (det)
        e os dados de cabeçalho, considerando o novo mapeamento XPath relativo.
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError:
            print(f"ERRO: Não foi possível analisar o XML: {file_path}")
            return []
        except FileNotFoundError:
            print(f"ERRO: Arquivo não encontrado: {file_path}")
            return []

        # Busca <infNFe> dentro de <NFe> usando namespace
        infnfe_node = root.find('.//{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe')
        if infnfe_node is None:
            infnfe_node = root.find('.//{http://www.portalfiscal.inf.br/nfe}infNFe')
        if infnfe_node is None:
            print(f"ERRO: Não encontrado <infNFe> em {file_path}")
            return []

        # 1. Extrai dados de cabeçalho
        header_data: Dict[str, str] = {}
        # Extrai todos os campos do mapping de forma dinâmica
        for col, xpath in self.mapping.items():
            # Sempre busca a partir do nó infNFe, exceto se o caminho começar com 'infNFe/' (que é redundante)
            rel_xpath = xpath.replace('infNFe/', '')
            val = self.extract_value(infnfe_node, rel_xpath)
            header_data[col] = val

        # Extrai infCpl para ser usado na função de extração complexa
        infcpl_full_text = self.extract_value(infnfe_node, 'infAdic/infCpl')
        header_data['infCpl'] = infcpl_full_text

        # 2. Processa cada item (<det>)
        items_list: List[Dict[str, Any]] = []
        for det in infnfe_node.findall('{http://www.portalfiscal.inf.br/nfe}det'):
            prod_node = det.find('{http://www.portalfiscal.inf.br/nfe}prod')
            imposto_node = det.find('{http://www.portalfiscal.inf.br/nfe}imposto')
            item_data: Dict[str, Any] = {'Arquivo XML': os.path.basename(file_path)}
            item_data.update(header_data) # Adiciona dados de cabeçalho

            # Extrai campos de item (que não são de cabeçalho)
            product_name = ''
            for col, xpath in self.mapping.items():
                if xpath in ('',) or xpath.startswith('infNFe/') or xpath.startswith('.'):
                    continue
                # Busca em prod_node
                if prod_node is not None and xpath in ['cProd', 'CFOP', 'xProd']:
                    val = self.extract_value(prod_node, xpath)
                    item_data[col] = val
                    if col == 'DESC CFOP':
                        product_name = val
                # Busca em imposto_node
                elif imposto_node is not None and xpath in ['CST', 'pICMS', 'vBC']:
                    # Pode estar em ICMS, PIS, COFINS
                    for imp_tag in ['ICMS', 'PIS', 'COFINS']:
                        imp_node = imposto_node.find(f'{{http://www.portalfiscal.inf.br/nfe}}{imp_tag}')
                        if imp_node is not None:
                            for sub in imp_node:
                                cst_val = sub.find(xpath)
                                if cst_val is not None and cst_val.text:
                                    item_data[col] = cst_val.text
                    # Busca direta para pICMS, vBC
                    val = self.extract_value(imposto_node, xpath)
                    if val:
                        item_data[col] = val
                # Busca em infCpl
                elif xpath == 'infCpl':
                    item_data[col] = infcpl_full_text

            items_list.append(item_data)

        return items_list

    def run_processor(self, xml_folder_path: str, output_file_path: str):
        """
        Função principal para percorrer a pasta de XMLs e gerar a planilha.
        (A lógica de execução permanece a mesma)
        """
        all_data: List[Dict[str, Any]] = []
        
        if not os.path.isdir(xml_folder_path):
            print(f"ERRO: O diretório de entrada não foi encontrado: {xml_folder_path}")
            return

        for filename in os.listdir(xml_folder_path):
            if filename.endswith('.xml') or filename.endswith('.XML'):
                file_path = os.path.join(xml_folder_path, filename)
                print(f"Processando arquivo: {filename}...")
                
                data = self.process_xml_file(file_path)
                all_data.extend(data)
                
        if not all_data:
            print("Nenhum dado processado. Verifique os arquivos XML na pasta de entrada.")
            return

        df = pd.DataFrame(all_data)
        
        # Reordena as colunas para seguir o layout do relatório
        required_columns = ['Arquivo XML'] + list(self.mapping.keys())
        df = df.reindex(columns=required_columns, fill_value='')

        try:
            df.to_excel(output_file_path, index=False)
            print("-" * 50)
            print(f"SUCESSO! Relatório salvo em: {os.path.abspath(output_file_path)}")
            print(f"Total de {len(all_data)} linhas (itens de NF-e) exportadas.")
        except Exception as e:
            print(f"ERRO ao salvar o arquivo Excel: {e}")

# ==============================================================================
# 3. EXECUÇÃO DO SCRIPT
# ==============================================================================

if __name__ == "__main__":
    os.makedirs(XML_FOLDER_PATH, exist_ok=True)
    mapper = NFeMapper()
    mapper.run_processor(XML_FOLDER_PATH, OUTPUT_FILE_PATH)