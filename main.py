from processador_notas_v2 import processar_pasta
from gerar_relatorio_customizado_v3 import gerar_relatorio_customizado

if __name__ == "__main__":
    # elee/ params para processador_notas_v2
    PASTA_XMLS = "reading_notes/unificado"
    ARQUIVO_MAPEAMENTO = "mapping_config.json"
    ARQUIVO_SAIDA = "output/resposta_notas.json"

    processar_pasta(PASTA_XMLS, ARQUIVO_MAPEAMENTO, ARQUIVO_SAIDA)

    # elee/ params para processador_customizado_v3
    ARQUIVO_JSON = "output/resposta_notas.json"
    ARQUIVO_EXCEL = "output/relatorio_customizado.xlsx"
    ARQUIVO_BASE_CFOP = "base/base_cfop.xlsx"

    gerar_relatorio_customizado(ARQUIVO_JSON, ARQUIVO_EXCEL, ARQUIVO_BASE_CFOP)
