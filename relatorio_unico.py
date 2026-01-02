import json
import pandas as pd
from typing import Dict, Any, List


# ================= IBS/CBS/IS - LÓGICA CONSOLIDADA =====================
def get_ibs_info(item: Dict[str, Any]) -> Dict[str, Any]:
    """Identifica presença de IBS (Imposto sobre Bens e Serviços) no item."""
    ibscbs_bloco = item.get("IBSCBS_BLOCO")
    ibs_bloco = item.get("IBS_BLOCO")
    ibs_vibs = (
        item.get("IBSCBS_VIBS")
        or item.get("IBS_VIBS")
        or item.get("IBS_VALOR")
        or item.get("VIBS")
    )
    ibs_cst = item.get("IBSCBS_CST") or item.get("IBS_CST")
    ibs_aliq = (
        item.get("IBSCBS_PIBSUF")
        or item.get("IBS_PIBSUF")
        or item.get("IBS_ALIQ")
        or item.get("IBS_PALIQ")
        or item.get("PIBSUF")
    )
    tem_ibs_flag = item.get("TEM_IBS")
    if ibscbs_bloco or ibs_bloco or ibs_vibs or tem_ibs_flag:
        valor = float(ibs_vibs) if ibs_vibs else 0.0
        partes = [f"SIM - R$ {valor:.2f}"]
        if ibs_cst:
            partes.append(f"CST: {ibs_cst}")
        if ibs_aliq:
            try:
                aliq_float = float(ibs_aliq)
                partes.append(f"Alíq: {aliq_float}%")
            except:
                partes.append(f"Alíq: {ibs_aliq}")
        info_consolidada = " (".join(partes)
        if "(" in info_consolidada:
            info_consolidada += ")"
    else:
        info_consolidada = "NAO"
    return {"IBS": info_consolidada}


def get_cbs_info(item: Dict[str, Any]) -> Dict[str, Any]:
    """Identifica presença de CBS (Contribuição sobre Bens e Serviços) no item."""
    ibscbs_bloco = item.get("IBSCBS_BLOCO")
    cbs_bloco = item.get("CBS_BLOCO")
    cbs_vcbs = (
        item.get("IBSCBS_VCBS")
        or item.get("CBS_VCBS")
        or item.get("CBS_VALOR")
        or item.get("VCBS")
    )
    cbs_cst = item.get("IBSCBS_CST") or item.get("CBS_CST")
    cbs_aliq = (
        item.get("IBSCBS_PCBS")
        or item.get("CBS_PCBS")
        or item.get("CBS_ALIQ")
        or item.get("CBS_PALIQ")
        or item.get("PCBS")
    )
    tem_cbs_flag = item.get("TEM_CBS")
    if ibscbs_bloco or cbs_bloco or cbs_vcbs or tem_cbs_flag:
        valor = float(cbs_vcbs) if cbs_vcbs else 0.0
        partes = [f"SIM - R$ {valor:.2f}"]
        if cbs_cst:
            partes.append(f"CST: {cbs_cst}")
        if cbs_aliq:
            try:
                aliq_float = float(cbs_aliq)
                partes.append(f"Alíq: {aliq_float}%")
            except:
                partes.append(f"Alíq: {cbs_aliq}")
        info_consolidada = " (".join(partes)
        if "(" in info_consolidada:
            info_consolidada += ")"
    else:
        info_consolidada = "NAO"
    return {"CBS": info_consolidada}


def get_is_info(item: Dict[str, Any]) -> Dict[str, Any]:
    """Identifica presença de IS (Imposto Seletivo) no item."""
    is_bloco = item.get("IS_BLOCO")
    is_vis = item.get("IS_VIS") or item.get("IS_VALOR") or item.get("VIS")
    is_cst = item.get("IS_CST")
    is_aliq = (
        item.get("IS_PIS")
        or item.get("IS_ALIQ")
        or item.get("IS_PALIQ")
        or item.get("PIS")
    )
    tem_is_flag = item.get("TEM_IS")
    if is_bloco or is_vis or tem_is_flag:
        valor = float(is_vis) if is_vis else 0.0
        partes = [f"SIM - R$ {valor:.2f}"]
        if is_cst:
            partes.append(f"CST: {is_cst}")
        if is_aliq:
            try:
                aliq_float = float(is_aliq)
                partes.append(f"Alíq: {aliq_float}%")
            except:
                partes.append(f"Alíq: {is_aliq}")
        info_consolidada = " (".join(partes)
        if "(" in info_consolidada:
            info_consolidada += ")"
    else:
        info_consolidada = "NAO"
    return {"IS": info_consolidada}


# Função principal de exemplo (deve ser adaptada para o seu fluxo)
def montar_dataframe_notas(notas: List[Dict[str, Any]]) -> pd.DataFrame:
    dados = []
    index = 0
    for idx, nota in enumerate(notas, 1):
        items = nota.get("ITEMS", [])
        for item_idx, item in enumerate(items):
            info_nota = {
                "ID": index,
                "Numero Nota": nota.get("NUMERO_NF", ""),
                "JSON da nota": json.dumps(nota, ensure_ascii=False, indent=2),
                "Tipo": nota.get("TIPO_DOCUMENTO", ""),
                "CNPJ/CPF Emissor": (
                    nota.get("EMIT_CNPJ")
                    if nota.get("EMIT_CNPJ")
                    else nota.get("EMIT_CPF", "")
                ),
                "Razão Social Emissor": nota.get("EMIT_RAZAO_SOCIAL", ""),
                "CNPJ/CPF Destinatário": (
                    nota.get("DEST_CNPJ")
                    if nota.get("DEST_CNPJ")
                    else nota.get("DEST_CPF", "")
                ),
                "Razão Social Destinatário": nota.get("DEST_RAZAO_SOCIAL", ""),
                "UF Emissor": nota.get("EMIT_UF", ""),
                "UF Destinatário": nota.get("DEST_UF", ""),
            }
            info_produto = {
                "NCM": item.get("NCM", ""),
                "CFOP": item.get("CFOP", ""),
            }
            ibs_info = get_ibs_info(item)
            cbs_info = get_cbs_info(item)
            is_info = get_is_info(item)
            resultado = {**info_nota, **info_produto, **ibs_info, **cbs_info, **is_info}
            dados.append(resultado)
            index += 1
    return pd.DataFrame(dados)


# Exemplo de uso (deve ser adaptado para o seu fluxo real)
if __name__ == "__main__":
    with open("output/resposta_notas.json", "r", encoding="utf-8") as f:
        notas = json.load(f)
    df = montar_dataframe_notas(notas)
    df.to_excel("output/relatorio_customizado.xlsx", index=False)
    print("Relatório gerado com IBS, CBS e IS!")
