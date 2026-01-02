import json
import os
from lxml import etree

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================

PASTA_XMLS = 'reading_notes/envision'
ARQUIVO_MAPEAMENTO = 'mapping_config.json'
ARQUIVO_SAIDA = 'output/resposta_notas_envision.json'

# ==============================================================================
# FUNÇÕES
# ==============================================================================

def remover_namespace(elemento):
    """Remove namespace de um elemento e seus filhos"""
    for elem in elemento.iter():
        if isinstance(elem.tag, str) and '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]
    return elemento


def extrair_namespace_raiz(tree):
    """Extrai o namespace da raiz do XML antes de remover namespaces"""
    raiz_original = tree.getroot()
    if isinstance(raiz_original.tag, str) and '}' in raiz_original.tag:
        namespace = raiz_original.tag.split('}')[0][1:]
        return namespace
    return None


def extrair_tipo_documento(raiz, namespace):
    """
    Determina o tipo de documento: mercadoria, serviço ou CT-e
    
    Regras:
    1. Se namespace != http://www.portalfiscal.inf.br/nfe → serviço (NFSe)
    2. Se mod = 55 ou 65 → mercadoria
    3. Se mod = 57 → CT-e (serviço de transporte)
    4. Se tem NCM → mercadoria
    5. Se tem ISSQN e não tem NCM → serviço
    """
    # Regra 1: Verifica namespace
    if namespace and namespace != 'http://www.portalfiscal.inf.br/nfe':
        return 'serviço'
    
    # Extrai modelo
    modelo = extrair_valor(raiz, 'infNFe/ide/mod')
    
    # Regra 2: Modelos 55 e 65
    if modelo in ['55', '65']:
        return 'mercadoria'
    
    # Regra 3: Modelo 57
    if modelo == '57':
        return 'CT-e'
    
    # Regra 4: Verifica presença de NCM
    tem_ncm = raiz.xpath('//infNFe/det/prod/NCM')
    if tem_ncm:
        return 'mercadoria'
    
    # Regra 5: Verifica presença de ISSQN (sem NCM)
    tem_issqn = raiz.xpath('//infNFe/det/imposto/ISSQN')
    if tem_issqn:
        return 'serviço'
    
    return None


def extrair_valor(raiz, xpath, retornar_elemento=False):
    """Extrai valor de um XPath, tentando múltiplas alternativas separadas por ' ou '"""
    if not xpath:
        return None
    
    # Tenta cada XPath alternativo
    for caminho in xpath.split(' ou '):
        caminho = caminho.strip()
        
        # Ignora descrições textuais
        if ' ' in caminho and '/' not in caminho:
            continue
        
        # Normaliza xpath
        if not caminho.startswith('/'):
            caminho = '//' + caminho
        
        try:
            elementos = raiz.xpath(caminho)
            if elementos:
                # Se for atributo ou texto
                if isinstance(elementos[0], str):
                    return elementos[0]
                # Se for elemento
                elif hasattr(elementos[0], 'tag'):
                    # Se pedir elemento completo (para campos BLOCO)
                    if retornar_elemento:
                        if len(elementos) > 1:
                            return elementos  # Retorna lista de elementos
                        return elementos[0]  # Retorna elemento único
                    
                    # Senão retorna texto
                    if elementos[0].text:
                        valores = [e.text.strip() for e in elementos if e.text]
                        return valores if len(valores) > 1 else (valores[0] if valores else None)
        except:
            continue
    
    return None


def elemento_para_dict(elemento):
    """Converte elemento XML em dicionário - retorna apenas o nome da tag do primeiro filho"""
    if elemento is None:
        return None
    
    # Se for lista de elementos
    if isinstance(elemento, list):
        return [elemento_para_dict(e) for e in elemento]
    
    # Retorna o nome da tag do primeiro filho (ex: ICMS61, ICMS00, etc)
    if len(elemento) > 0:
        return elemento[0].tag
    
    return None


def processar_xml(caminho_xml, mapeamento):
    """Processa um XML e extrai dados conforme mapeamento"""
    tree = etree.parse(caminho_xml)
    
    # Extrai namespace antes de remover
    namespace = extrair_namespace_raiz(tree)
    
    # Remove namespaces para facilitar XPath
    raiz = remover_namespace(tree.getroot())
    
    # Extrai tipo de documento (passa namespace para análise)
    tipo_documento = extrair_tipo_documento(raiz, namespace)
    
    dados_nota = {}
    campos_item = {}
    
    # Extrai cada campo do mapeamento
    for campo, config in mapeamento.items():
        # Campos especiais tratados separadamente
        if campo == 'NAMESPACE_RAIZ':
            dados_nota[campo] = namespace
            continue
        elif campo == 'TIPO_DOCUMENTO':
            dados_nota[campo] = tipo_documento
            continue
        
        xpath = config.get('caminho_xml', '')
        
        # Verifica se é campo BLOCO (precisa retornar estrutura completa)
        eh_bloco = campo.endswith('_BLOCO')
        valor = extrair_valor(raiz, xpath, retornar_elemento=eh_bloco)
        
        # Converte elemento XML em dict se for bloco
        if eh_bloco and valor is not None:
            valor = elemento_para_dict(valor)
        
        # Separa campos de item dos campos de nota
        if campo.startswith('ITEM_'):
            campos_item[campo] = valor
        else:
            dados_nota[campo] = valor
    
    # Organiza itens em lista
    if campos_item:
        # Descobre quantos itens
        num_itens = 1
        for valor in campos_item.values():
            if isinstance(valor, list):
                num_itens = max(num_itens, len(valor))
        
        # Monta lista de itens
        itens = []
        for i in range(num_itens):
            item = {}
            for nome_campo, valor in campos_item.items():
                nome_limpo = nome_campo[5:]  # Remove 'ITEM_'
                
                if isinstance(valor, list):
                    item[nome_limpo] = valor[i] if i < len(valor) else None
                else:
                    item[nome_limpo] = valor
            
            itens.append(item)
        
        dados_nota['ITEMS'] = itens
    
    return dados_nota


def processar_pasta():
    """Processa todos XMLs da pasta e gera JSON final"""
    # Carrega mapeamento
    with open(ARQUIVO_MAPEAMENTO, 'r', encoding='utf-8') as f:
        mapeamento = json.load(f)
    
    # Lista XMLs
    arquivos = [f for f in os.listdir(PASTA_XMLS) if f.endswith('.xml')]
    print(f"Processando {len(arquivos)} XMLs")
    
    # Processa cada XML
    notas = []
    for i, arquivo in enumerate(arquivos, 1):
        caminho = os.path.join(PASTA_XMLS, arquivo)
        print(f"[{i}/{len(arquivos)}] {arquivo}")
        
        try:
            dados = processar_xml(caminho, mapeamento)
            dados['xml_filename'] = arquivo
            notas.append(dados)
        except Exception as e:
            print(f"  Erro: {e}")
    
    # Salva resultado
    os.makedirs('output', exist_ok=True)
    with open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
        json.dump(notas, f, indent=4, ensure_ascii=False)
    
    print(f"\nConcluído: {len(notas)} notas salvas em {ARQUIVO_SAIDA}")


# ==============================================================================
# EXECUÇÃO
# ==============================================================================

if __name__ == '__main__':
    processar_pasta()
