import json
import os
from lxml import etree

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================

# ==============================================================================
# FUNÇÕES
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

    Regras:
    1. Se namespace != http://www.portalfiscal.inf.br/nfe → serviço (NFSe)
    2. Se mod = 55 ou 65 → mercadoria
    3. Se mod = 57 → CT-e (serviço de transporte)
    4. Se tem NCM → mercadoria
    5. Se tem ISSQN e não tem NCM → serviço
    """
    # Regra 1: Verifica namespace
    if namespace and namespace != "http://www.portalfiscal.inf.br/nfe":
        return "serviço"

    # Extrai modelo
    modelo = extrair_valor(raiz, "infNFe/ide/mod")

    # Regra 2: Modelos 55 e 65
    if modelo in ["55", "65"]:
        return "mercadoria"

    # Regra 3: Modelo 57
    if modelo == "57":
        return "CT-e"

    # Regra 4: Verifica presença de NCM
    tem_ncm = raiz.xpath("//infNFe/det/prod/NCM")
    if tem_ncm:
        return "mercadoria"

    # Regra 5: Verifica presença de ISSQN (sem NCM)
    tem_issqn = raiz.xpath("//infNFe/det/imposto/ISSQN")
    if tem_issqn:
        return "serviço"

    return None


def extrair_valor(raiz, xpath, retornar_elemento=False):
    """Extrai valor de um XPath, tentando múltiplas alternativas separadas por ' ou '"""
    if not xpath:
        return None

    # Tenta cada XPath alternativo
    for caminho in xpath.split(" ou "):
        caminho = caminho.strip()

        # Ignora descrições textuais
        if " " in caminho and "/" not in caminho:
            continue

        # Normaliza xpath
        if not caminho.startswith("/"):
            caminho = "//" + caminho

        try:
            elementos = raiz.xpath(caminho)
            if elementos:
                # Se for atributo ou texto
                if isinstance(elementos[0], str):
                    return elementos[0]
                # Se for elemento
                elif hasattr(elementos[0], "tag"):
                    # Se pedir elemento completo (para campos BLOCO)
                    if retornar_elemento:
                        if len(elementos) > 1:
                            return elementos  # Retorna lista de elementos
                        return elementos[0]  # Retorna elemento único

                    # Senão retorna texto
                    if elementos[0].text:
                        valores = [e.text.strip() for e in elementos if e.text]
                        return (
                            valores
                            if len(valores) > 1
                            else (valores[0] if valores else None)
                        )
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


def extrair_todos_impostos(raiz):
    """Extrai todos os impostos presentes no item"""
    # Busca todos os itens da nota
    itens = raiz.xpath("//infNFe/det")

    if not itens:
        return None

    # Para cada item, verifica os impostos
    resultados_por_item = []
    for item in itens:
        impostos = item.xpath("imposto/*")
        impostos_do_item = []

        for imposto in impostos:
            tag = imposto.tag
            impostos_do_item.append(tag)

        # Adiciona resultado do item (None se não houver impostos)
        resultados_por_item.append(
            ", ".join(impostos_do_item) if impostos_do_item else None
        )

    # Retorna lista se múltiplos itens, ou valor único se apenas um item
    return (
        resultados_por_item
        if len(resultados_por_item) > 1
        else (resultados_por_item[0] if resultados_por_item else None)
    )


def extrair_outros_impostos(raiz):
    """Extrai impostos não convencionais do item (diferentes de ICMS, IPI, PIS, COFINS, ISSQN)"""
    impostos_padrao = {"ICMS", "IPI", "PIS", "COFINS", "ISSQN"}
    # impostos_padrao = {}

    # Busca todos os itens da nota
    itens = raiz.xpath("//infNFe/det")

    if not itens:
        return None

    # Para cada item, verifica os impostos
    resultados_por_item = []
    for item in itens:
        impostos = item.xpath("imposto/*")
        outros_do_item = []

        for imposto in impostos:
            tag = imposto.tag
            if tag not in impostos_padrao:
                outros_do_item.append(tag)

        # Adiciona resultado do item (None se não houver outros impostos)
        resultados_por_item.append(
            ", ".join(outros_do_item) if outros_do_item else None
        )

    # Retorna lista se múltiplos itens, ou valor único se apenas um item
    return (
        resultados_por_item
        if len(resultados_por_item) > 1
        else (resultados_por_item[0] if resultados_por_item else None)
    )


def verificar_difal(raiz, debug=False):
    """
    Verifica se incide DIFAL (Diferencial de Alíquota) por item.

    REGRA 1: Se existe tag ICMSUFDest no item → incide DIFAL
    REGRA 2: Se cumprir os 3 requisitos simultaneamente:
        - Destinatário = consumidor final (indFinal = 1)
        - Operação interestadual (UF emitente != UF destinatário)
        - Destinatário não contribuinte do ICMS (indIEDest = 9)

    Retorna lista de '1' (incide) ou '0' (não incide) para cada item
    """
    print(f"  [DIFAL DEBUG] Função chamada, debug={debug}")

    # Busca todos os itens da nota
    itens = raiz.xpath("//infNFe/det")

    if not itens:
        print(f"  [DIFAL DEBUG] Nenhum item encontrado!")
        return None

    print(f"  [DIFAL DEBUG] {len(itens)} itens encontrados")

    # Extrai dados do nível da nota para REGRA 2
    ind_final = extrair_valor(raiz, "infNFe/ide/indFinal")
    uf_emitente = extrair_valor(raiz, "infNFe/emit/enderEmit/UF")
    uf_destinatario = extrair_valor(raiz, "infNFe/dest/enderDest/UF")
    ind_ie_dest = extrair_valor(raiz, "infNFe/dest/indIEDest")

    print(
        f"  [DIFAL] indFinal={ind_final}, UF_Emit={uf_emitente}, UF_Dest={uf_destinatario}, indIEDest={ind_ie_dest}"
    )

    # Verifica REGRA 2 (aplica-se a todos os itens da nota)
    cond1 = ind_final == "1"
    cond2 = uf_emitente is not None
    cond3 = uf_destinatario is not None
    cond4 = uf_emitente != uf_destinatario
    cond5 = ind_ie_dest == "9"

    print(
        f"  [DIFAL] Condições: indFinal=='1':{cond1}, UF_emit!=None:{cond2}, UF_dest!=None:{cond3}, UFs_diferentes:{cond4}, indIEDest=='9':{cond5}"
    )

    regra2_atendida = cond1 and cond2 and cond3 and cond4 and cond5

    if debug:
        print(f"  [DIFAL] REGRA 2 atendida: {regra2_atendida}")

    # Para cada item, verifica REGRA 1 ou REGRA 2
    resultados_por_item = []
    for idx, item in enumerate(itens, 1):
        # REGRA 1: Verifica se existe ICMSUFDest no item
        # Testa todos os caminhos possíveis
        tem_icms_ufdest = bool(
            item.xpath("imposto/ICMSUFDest")
            or item.xpath(".//ICMSUFDest")
            or item.xpath("imposto/ICMS/ICMSUFDest")
            or item.xpath("imposto/ICMS/*/ICMSUFDest")
        )

        if debug and tem_icms_ufdest:
            print(f"  [DIFAL] Item {idx}: Encontrou ICMSUFDest")

        if tem_icms_ufdest or regra2_atendida:
            resultados_por_item.append("1")  # Incide DIFAL
        else:
            resultados_por_item.append("0")  # Não incide DIFAL

    if debug:
        print(f"  [DIFAL] Resultado: {resultados_por_item}")

    # Retorna lista se múltiplos itens, ou valor único se apenas um item
    return (
        resultados_por_item
        if len(resultados_por_item) > 1
        else (resultados_por_item[0] if resultados_por_item else None)
    )


def processar_xml(caminho_xml, mapeamento, debug_difal=True):
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
        if campo == "NAMESPACE_RAIZ":
            dados_nota[campo] = namespace
            continue
        elif campo == "TIPO_DOCUMENTO":
            dados_nota[campo] = tipo_documento
            continue
        elif campo == "ITEM_OUTROS_IMPOSTOS":
            # Função especial para extrair outros impostos
            valor = extrair_outros_impostos(raiz)
            campos_item[campo] = valor
            continue
        elif campo == "ITEM_TODOS_IMPOSTOS":
            # Função especial para extrair todos impostos
            valor = extrair_todos_impostos(raiz)
            campos_item[campo] = valor
            continue
        elif campo == "ITEM_TEM_DIFAL":
            # Função especial para verificar DIFAL por item
            valor = verificar_difal(raiz, debug=debug_difal)
            campos_item[campo] = valor
            continue

        xpath = config.get("caminho_xml", "")

        # Verifica se é campo BLOCO (precisa retornar estrutura completa)
        eh_bloco = campo.endswith("_BLOCO")
        valor = extrair_valor(raiz, xpath, retornar_elemento=eh_bloco)

        # Converte elemento XML em dict se for bloco
        if eh_bloco and valor is not None:
            valor = elemento_para_dict(valor)

        # Separa campos de item dos campos de nota
        if campo.startswith("ITEM_"):
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

        dados_nota["ITEMS"] = itens

    return dados_nota


def processar_pasta(pasta_xmls, arquivo_mapeamento, arquivo_saida):
    """Processa todos XMLs da pasta e gera JSON final"""
    # Carrega mapeamento
    with open(arquivo_mapeamento, "r", encoding="utf-8") as f:
        mapeamento = json.load(f)

    # Lista XMLs
    arquivos = [f for f in os.listdir(pasta_xmls) if f.endswith(".xml")]
    print(f"Processando {len(arquivos)} XMLs")

    # Processa cada XML
    notas = []
    for i, arquivo in enumerate(arquivos, 1):
        caminho = os.path.join(pasta_xmls, arquivo)
        print(f"[{i}/{len(arquivos)}] {arquivo}")

        try:
            # Ativa debug apenas na primeira nota
            debug_difal = i == 1
            dados = processar_xml(caminho, mapeamento, debug_difal=debug_difal)
            dados["xml_filename"] = arquivo
            notas.append(dados)
        except Exception as e:
            print(f"  Erro: {e}")

    # Salva resultado
    os.makedirs("output", exist_ok=True)
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        json.dump(notas, f, indent=4, ensure_ascii=False)

    print(f"\nConcluído: {len(notas)} notas salvas em {arquivo_saida}")
