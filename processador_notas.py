import json
import os
from lxml import etree
from typing import Dict, Any, List

# ==============================================================================
# Funções de Leitura e Parsing
# ==============================================================================

def load_mapping_structure(mapping_path: str) -> Dict[str, Dict[str, str]]:
    """
    Carrega a estrutura de mapeamento a partir de um arquivo JSON.

    Args:
        mapping_path: O caminho para o arquivo JSON de mapeamento.

    Returns:
        Um dicionário contendo a estrutura de mapeamento.
    
    Raises:
        FileNotFoundError: Se o arquivo de mapeamento não for encontrado.
        json.JSONDecodeError: Se o conteúdo do arquivo JSON for inválido.
    """
    print(f"Lendo estrutura de mapeamento em: {mapping_path}")
    if not os.path.exists(mapping_path):
        raise FileNotFoundError(f"Arquivo de mapeamento não encontrado: {mapping_path}")
    
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping_structure = json.load(f)
    return mapping_structure

def load_xml_document(xml_path: str) -> etree.Element:
    """
    Carrega e faz o parsing de um documento XML.
    Remove namespaces para facilitar o uso dos XPaths definidos no mapeamento.
    """
    # print(f"Lendo documento XML em: {xml_path}")
    if not os.path.exists(xml_path):
        raise FileNotFoundError(f"Arquivo XML não encontrado: {xml_path}")
        
    tree = etree.parse(xml_path)
    # Remove namespaces para simplificar XPaths
    for elem in tree.iter():
        if isinstance(elem.tag, str) and '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]
    return tree.getroot()

# ==============================================================================
# Função Principal de Mapeamento
# ==============================================================================

def process_xml_mapping(xml_path: str, mapping_path: str) -> Dict[str, Any]:
    """
    Processa o XML com base nas regras do arquivo de mapeamento.
    Suporta: 'ou', 'presença de', wildcards (*) e listas.
    """
    try:
        # 1. Carregar a estrutura de mapeamento
        # Assumindo que a estrutura de mapeamento é carregada uma vez fora do loop para otimização
        mapping_structure = load_mapping_structure(mapping_path)
        
        # 2. Carregar o documento XML (sem namespaces)
        xml_root = load_xml_document(xml_path)
        
        extracted_data = {}
        
        # 3. Aplicar o mapeamento
        # print(f"\nIniciando mapeamento da Nota Fiscal: {os.path.basename(xml_path)}")
        
        for key, config in mapping_structure.items():
            raw_xpath = config.get("caminho_xml")
            target_field = config.get("target_field", key)
            is_optional = config.get("opcional", False)
            
            if not raw_xpath:
                continue
            
            # Trata múltiplos caminhos (separador " ou ")
            possible_xpaths = [p.strip() for p in raw_xpath.split(' ou ')]
            value = None
            
            for xpath in possible_xpaths:
                check_presence = False
                # Trata regra de "presença de"
                if xpath.lower().startswith("presença de "):
                    xpath = xpath[12:].strip()
                    check_presence = True
                
                # Ignora textos descritivos que não são XPaths
                if " " in xpath and "/" not in xpath and not check_presence:
                    continue

                # Garante busca em qualquer nível se não for caminho absoluto
                final_xpath = xpath if xpath.startswith("/") else "//" + xpath
                
                try:
                    elements = xml_root.xpath(final_xpath)
                except Exception:
                    continue # Pula XPaths inválidos
                
                if check_presence:
                    if elements:
                        value = True
                        break
                    elif value is None:
                        value = False
                
                elif elements:
                    # Caso especial: Wildcard (*) para pegar o nome da tag (ex: Tipo de ICMS)
                    if xpath.endswith("*"):
                        vals = [e.tag for e in elements if isinstance(e.tag, str)]
                    else:
                        # Extrai texto dos elementos
                        vals = []
                        for e in elements:
                            if hasattr(e, 'text') and e.text:
                                vals.append(e.text.strip())
                            elif isinstance(e, (str, int, float, bool)):
                                vals.append(e)
                    
                    if vals:
                        # Se for lista única, retorna o valor, senão a lista
                        value = vals[0] if len(vals) == 1 else vals
                        break
            
            # Se o campo é opcional e não foi encontrado, atribui None silenciosamente
            # Se não é opcional e value é None, isso pode indicar um problema (mas não quebramos aqui)
            extracted_data[target_field] = value

        # print(f"Mapeamento concluído para {os.path.basename(xml_path)}.")
        return extracted_data

    except Exception as e:
        print(f"\nERRO durante o processamento do arquivo {xml_path}: {e}")
        import traceback
        traceback.print_exc()
        return {}

# ==============================================================================
# Nova Função para Processamento de Pasta
# ==============================================================================

def process_xml_folder(xml_folder_path: str, mapping_path: str, output_file_path: str) -> List[Dict[str, Any]]:
    """
    Percorre todos os arquivos XML em uma pasta, processa cada um e concatena os resultados.

    Args:
        xml_folder_path: O caminho para a pasta contendo os arquivos XML.
        mapping_path: O caminho para o arquivo JSON de mapeamento.
        output_file_path: O caminho para salvar o arquivo JSON de saída.

    Returns:
        Uma lista de dicionários com os dados extraídos de todos os XMLs.
    """
    print(f"\n🚀 Iniciando processamento da pasta: {xml_folder_path}")
    all_processed_data = []
    
    if not os.path.exists(xml_folder_path):
        print(f"❌ Pasta de XMLs não encontrada: {xml_folder_path}")
        return []

    # Lista todos os arquivos .xml na pasta
    xml_files = [f for f in os.listdir(xml_folder_path) if f.lower().endswith('.xml')]
    
    if not xml_files:
        print("⚠️ Nenhuma arquivo .xml encontrado na pasta.")
        return []
    
    print(f"Total de arquivos XML a processar: {len(xml_files)}")

    for i, filename in enumerate(xml_files):
        xml_path = os.path.join(xml_folder_path, filename)
        print(f"\n[{i+1}/{len(xml_files)}] Processando: {filename}")
        
        # Processa o XML individualmente
        result_json = process_xml_mapping(xml_path, mapping_path)
        
        if result_json:
            # Adiciona o nome do arquivo para rastreamento (opcional, mas útil)
            result_json['xml_filename'] = filename
            all_processed_data.append(result_json)

    # Salva o resultado concatenado
    print(f"\n💾 Salvando todos os {len(all_processed_data)} resultados concatenados em: {output_file_path}")
    with open(output_file_path, 'w', encoding='utf-8') as f:
        # Salva a lista de dicionários, o que é a maneira mais comum e correta de "concatenar" JSONs
        json.dump(all_processed_data, f, indent=4, ensure_ascii=False)
    
    print("✅ Processamento de pasta concluído.")
    return all_processed_data


# ==============================================================================
# Execução do Script Principal
# ==============================================================================

if __name__ == '__main__':
    # ==========================================================================
    # 📌 CONFIGURAÇÃO DE PATHS
    # É NECESSÁRIO CRIAR ESTAS PASTAS E ARQUIVOS PARA O SCRIPT FUNCIONAR:
    # 1. Uma pasta 'xml_notes' com seus arquivos .xml dentro.
    # 2. Um arquivo 'mapping_config.json' (ou similar) com a estrutura de mapeamento.
    # ==========================================================================
    XML_FOLDER_PATH = 'reading_notes/unificado'  # <<< MUDAR AQUI PARA O CAMINHO DA SUA PASTA DE XMLS
    MAPPING_CONFIG_PATH = 'mapping_config_filtered.json' 
    OUTPUT_DIR = 'output'
    OUTPUT_FILE_NAME = 'resposta_notas.json'
    OUTPUT_PATH = os.path.join(OUTPUT_DIR, OUTPUT_FILE_NAME)
    
    # Cria a pasta de output se não existir
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Executa a função principal para processamento da pasta
    try:
        process_xml_folder(XML_FOLDER_PATH, MAPPING_CONFIG_PATH, OUTPUT_PATH)
        
        print("\n==================================")
        print("   Processamento em Lote Concluído!")
        print("==================================")
        print(f"O resultado final está em: **{OUTPUT_PATH}**")
    
    except FileNotFoundError as e:
        print(f"\nERRO FATAL: {e}")
        print("\nVerifique se o caminho da pasta de XMLs e do arquivo de mapeamento estão corretos.")