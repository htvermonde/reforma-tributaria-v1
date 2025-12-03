import json
import os
from lxml import etree
from typing import Dict, Any

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
    print(f"Lendo documento XML em: {xml_path}")
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
        mapping_structure = load_mapping_structure(mapping_path)
        
        # 2. Carregar o documento XML (sem namespaces)
        xml_root = load_xml_document(xml_path)
        
        extracted_data = {}
        
        # 3. Aplicar o mapeamento
        print("\nIniciando mapeamento da Nota Fiscal...")
        
        for key, config in mapping_structure.items():
            raw_xpath = config.get("caminho_xml")
            target_field = config.get("target_field", key)
            
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
            
            extracted_data[target_field] = value
            # print(f"  - Mapeado '{key}': {value}")

        print("\nMapeamento concluído com sucesso.")
        return extracted_data

    except Exception as e:
        print(f"\nERRO durante o processamento: {e}")
        import traceback
        traceback.print_exc()
        return {}


# ==============================================================================
# Execução do Script Principal
# ==============================================================================

if __name__ == '__main__':
    # DEFINE OS PATHS AQUI
    XML_FILE_PATH = 'reading_notes/potencial/31240380795727000656550010001509871474578521.xml'
    MAPPING_CONFIG_PATH = 'mapping_config.json'
    MAPPING_CONFIG_PATH = 'mapping_config_filtered.json'
    OUTPUT_DIR = 'output'
    
    # Cria a pasta de output se não existir
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Executa a função principal com os paths
    nf_mapping = process_xml_mapping(XML_FILE_PATH, MAPPING_CONFIG_PATH)
    nf_mapping_filtered = process_xml_mapping(XML_FILE_PATH, MAPPING_CONFIG_PATH)
    
    # Gera nome do arquivo de saída baseado no nome do XML
    xml_filename = os.path.basename(XML_FILE_PATH).replace('.xml', '')
    output_filename = f"{xml_filename}_mapeado.json"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Salva o resultado em arquivo JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(nf_mapping_filtered, f, indent=4, ensure_ascii=False)

    
    print("\n==================================")
    print("Resultado Final do Mapeamento:")
    print("==================================")
    print(json.dumps(nf_mapping_filtered, indent=4, ensure_ascii=False))
    print(f"\n Arquivo salvo em: {output_path}")