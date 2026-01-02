import json
import os
from lxml import etree

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================

PASTA_XMLS = "reading_notes/envision"
ARQUIVO_MAPEAMENTO = "mapping_config.json"
ARQUIVO_SAIDA = "output/resposta_notas_envision.json"

# ==============================================================================
# FUNÇÕES (copiadas do processador_notas_v2.py)
# ==============================================================================


def remover_namespace(elemento):
    """Remove namespace de um elemento e seus filhos"""
    for elem in elemento.iter():
        if isinstance(elem.tag, str) and "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]
    return elemento


def extrair_namespace_raiz(tree):
    """Extrai o namespace da raiz do XML antes de remover namespaces"""
    raiz_original = tree.getroot()
    if isinstance(raiz_original.tag, str) and "}" in raiz_original.tag:
        namespace = raiz_original.tag.split("}")[0][1:]
        return namespace
    return None


def extrair_tipo_documento(raiz, namespace):
    """
    Determina o tipo de documento: mercadoria, serviço ou CT-e
    """
    if namespace and namespace != "http://www.portalfiscal.inf.br/nfe":
        return "serviço"

    modelo = extrair_valor(raiz, "infNFe/ide/mod")
    if modelo in ["55", "65"]:
        return "mercadoria"
    elif modelo == "57":
        return "CT-e"

    tem_ncm = bool(raiz.xpath(".//NCM"))
    tem_issqn = bool(raiz.xpath(".//ISSQN"))

    if tem_ncm:
        return "mercadoria"
    elif tem_issqn:
        return "serviço"

    return "mercadoria"


def extrair_valor(raiz, caminho):
    """Extrai valor de um caminho XPath"""
    if " ou " in caminho:
        caminhos = [c.strip() for c in caminho.split(" ou ")]
    else:
        caminhos = [caminho]

    for cam in caminhos:
        if cam.lower().startswith("presença de "):
            cam = cam[12:].strip()
            elementos = raiz.xpath(f"//{cam}")
            if elementos:
                return True
            continue

        if "/" not in cam:
            continue

        if cam.endswith("*"):
            elementos = raiz.xpath(cam[:-1])
            if elementos:
                return elementos[0].tag
        else:
            elementos = raiz.xpath(f"//{cam}")
            if elementos and hasattr(elementos[0], "text"):
                return elementos[0].text

    return None


def processar_xml(caminho_xml, mapeamento):
    """Processa um XML e retorna o JSON da nota com seus itens"""
    tree = etree.parse(caminho_xml)
    namespace = extrair_namespace_raiz(tree)
    raiz = remover_namespace(tree.getroot())

    # Extrai dados da nota (nível raiz)
    nota = {}
    for chave, config in mapeamento.items():
        if not chave.startswith("ITEM_"):
            caminho = config.get("caminho_xml", "")
            valor = extrair_valor(raiz, caminho)
            nota[chave] = valor

    # Adiciona tipo de documento
    nota["TIPO_DOCUMENTO"] = extrair_tipo_documento(raiz, namespace)
    nota["NAMESPACE_RAIZ"] = namespace

    # Processa itens (det)
    itens = []
    dets = raiz.xpath(".//det")

    for det in dets:
        item = {}

        # Extrai dados do item
        for chave, config in mapeamento.items():
            if chave.startswith("ITEM_"):
                caminho = config.get("caminho_xml", "")
                # Remove o prefixo do caminho de nota
                caminho_item = caminho.replace("infNFe/det/", "")

                valor = extrair_valor(det, caminho_item)
                # Remove prefixo ITEM_ da chave
                chave_final = chave.replace("ITEM_", "")
                item[chave_final] = valor

        # Adiciona número do item
        item["NUMERO"] = det.get("nItem")

        itens.append(item)

    nota["ITEMS"] = itens

    return nota


def processar_pasta():
    """Processa todos XMLs da pasta e gera JSON final"""
    # Carrega mapeamento
    with open(ARQUIVO_MAPEAMENTO, "r", encoding="utf-8") as f:
        mapeamento = json.load(f)

    # Lista XMLs
    arquivos = [f for f in os.listdir(PASTA_XMLS) if f.lower().endswith(".xml")]
    print(f"\n{'='*80}")
    print(f"PROCESSANDO PASTA ENVISION COM TAGS IBS/CBS/IS")
    print(f"{'='*80}")
    print(f"Processando {len(arquivos)} XMLs da pasta: {PASTA_XMLS}\n")

    # Processa cada XML
    notas = []
    for i, arquivo in enumerate(arquivos, 1):
        caminho = os.path.join(PASTA_XMLS, arquivo)
        print(f"[{i}/{len(arquivos)}] {arquivo}")

        try:
            dados = processar_xml(caminho, mapeamento)
            dados["xml_filename"] = arquivo
            notas.append(dados)
        except Exception as e:
            print(f"  ❌ Erro: {e}")

    # Salva resultado
    os.makedirs("output", exist_ok=True)
    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(notas, f, indent=4, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"✅ Concluído: {len(notas)} notas salvas em {ARQUIVO_SAIDA}")
    print(f"{'='*80}")


# ==============================================================================
# EXECUÇÃO
# ==============================================================================

if __name__ == "__main__":
    processar_pasta()
