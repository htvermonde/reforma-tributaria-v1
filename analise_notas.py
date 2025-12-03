import json
import os
from datetime import datetime
from typing import List, Dict, Any, Union, Tuple

# ==============================================================================
# Funções Auxiliares (Mantidas para Normalização e Estruturação)
# ==============================================================================

def normalize_date(date_str: str) -> str:
    """Normaliza o formato de data para YYYY-MM-DD."""
    if not date_str:
        return None
    date_part = date_str.split('T')[0]
    try:
        return datetime.strptime(date_part, '%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError:
        return None

def find_date_range(notes: List[Dict[str, Any]]) -> Dict[str, str]:
    """Encontra a data de início e fim no conjunto de notas."""
    dates = []
    for note in notes:
        norm_date = normalize_date(note.get("DATA_EMISSAO"))
        if norm_date:
            dates.append(norm_date)

    if not dates:
        return {"inicio": None, "fim": None}

    return {
        "inicio": min(dates),
        "fim": max(dates)
    }

def safe_get_list(data: Union[str, List, None]) -> List[str]:
    """Garante que o campo retornado seja uma lista de strings."""
    if data is None:
        return []
    if isinstance(data, list):
        return [str(item) if item is not None else "" for item in data]
    return [str(data)]

def safe_get_value(data: Union[str, List, None], index: int) -> str:
    """Retorna o valor no índice da lista, ou string vazia."""
    if isinstance(data, list) and index < len(data):
        return str(data[index]) if data[index] is not None else ""
    if index == 0 and isinstance(data, str) and data:
        return str(data)
    return ""

def transform_note_to_output(note: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforma a estrutura plana da nota processada em uma estrutura hierárquica.
    Focamos nos campos essenciais para a identificação do conjunto de dados.
    """
    transformed_note = {
        "cabecalho_fiscal": {
            "modelo": note.get("MODELO"),
            "tipo_nf": note.get("TIPO_NF"),
            "natureza_operacao": note.get("NATUREZA_OPERACAO"),
            # Campos essenciais para análise de conjunto (exemplos do seu formato)
            # "finalidade": note.get("FINALIDADE"), 
            # "destino_operacao": note.get("DESTINO_OPERACAO"), 
            # "consumidor_final": note.get("CONSUMIDOR_FINAL"), 
            "emit_uf": note.get("EMIT_UF"), 
            "dest_uf": note.get("DEST_UF"),
        },
        "itens_fiscais": []
    }

    # Descompacta os arrays de itens
    item_n_list = safe_get_list(note.get("ITEM_NUMERO"))
    
    for i in range(len(item_n_list)):
        item = {
            "n_item": safe_get_value(note.get("ITEM_NUMERO"), i),
            "ncm": safe_get_value(note.get("ITEM_NCM"), i),
            "cfop": safe_get_value(note.get("ITEM_CFOP"), i),
            
            # CSTs e Alíquotas são cruciais para identificar conjuntos fiscais diferentes
            "icms_cst": safe_get_value(note.get("ITEM_ICMS_CST"), i),
            # "aliq_icms": safe_get_value(note.get("ITEM_ICMS_PICMS"), i), 
            "pis_cst": safe_get_value(note.get("ITEM_PIS_CST"), i),
            "cofins_cst": safe_get_value(note.get("ITEM_COFINS_CST"), i),
            # "ipi_cst": safe_get_value(note.get("ITEM_IPI_CST"), i),
        }
        # Adiciona o item à lista
        transformed_note["itens_fiscais"].append(item)

    return transformed_note

# ==============================================================================
# Função Principal de Análise
# ==============================================================================

def analyze_tax_data_by_company(input_path: str, output_path: str):
    """
    Carrega, agrupa por CNPJ Emitente e identifica conjuntos de dados únicos, 
    salvando a saída no formato solicitado pelo usuário.
    """
    print(f"Lendo dados consolidados de: {input_path}")
    if not os.path.exists(input_path):
        print(f"❌ Erro: Arquivo de entrada não encontrado em {input_path}")
        return

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            all_notes: List[Dict[str, Any]] = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler ou decodificar o arquivo: {e}")
        return

    # 1. Agrupar notas por CNPJ Emitente
    notes_by_cnpj: Dict[str, List[Dict[str, Any]]] = {}
    for note in all_notes:
        cnpj = note.get("EMIT_CNPJ")
        if cnpj:
            if cnpj not in notes_by_cnpj:
                notes_by_cnpj[cnpj] = []
            notes_by_cnpj[cnpj].append(note)

    final_analysis: Dict[str, Any] = {}
    
    # 2. Processar cada grupo de notas (cada empresa)
    for cnpj, notes in notes_by_cnpj.items():
        print(f"\n⚙️ Processando CNPJ: {cnpj} com {len(notes)} notas...")
        
        # 2.1 Encontrar o período das notas
        period = find_date_range(notes)
        
        # 2.2 Agrupar e contar os conjuntos de dados únicos
        unique_sets_counts: Dict[Tuple, Dict[str, Any]] = {}

        for note in notes:
            # Transforma a nota na estrutura hierárquica padrão para análise
            t_note = transform_note_to_output(note)
            
            # --- Criação da Assinatura Única (Chave) ---
            # 1. Chave para o cabeçalho (imutável)
            cabecalho_tuple = tuple(sorted(t_note["cabecalho_fiscal"].items()))
            
            # 2. Chave para os itens fiscais (lista de tuplas imutáveis)
            itens_tuples = []
            for item in t_note["itens_fiscais"]:
                itens_tuples.append(tuple(sorted(item.items())))
            
            # A chave única é o cabeçalho + os itens
            unique_key = (cabecalho_tuple, tuple(itens_tuples))
            
            
            # --- Agregação e Contagem ---
            if unique_key not in unique_sets_counts:
                # Se for um novo conjunto, inicializa com a estrutura solicitada
                unique_sets_counts[unique_key] = {
                    "cabecalho_fiscal": t_note["cabecalho_fiscal"],
                    "itens_fiscais": t_note["itens_fiscais"],
                    "count": 1 # Primeiro caso encontrado
                }
            else:
                # Se for um conjunto já encontrado, incrementa o contador
                unique_sets_counts[unique_key]["count"] += 1

        
        # 3. Preparar a saída no formato solicitado (lista de conjuntos únicos)
        
        # Converte o dicionário de conjuntos únicos para uma lista de conjuntos
        final_notes_structure = list(unique_sets_counts.values())

        final_analysis[cnpj] = {
            "empresa_cnpj": cnpj,
            "periodo": period,
            "notas": final_notes_structure
        }
        
        print(f"   -> Conjuntos únicos de dados fiscais encontrados: {len(final_notes_structure)}")

    # 4. Salvar o resultado final
    print(f"\n💾 Salvando a análise final em: {output_path}")
    
    # Salva apenas os valores da análise (a lista de empresas)
    output_data_list = list(final_analysis.values())

    with open(output_path, 'w', encoding='utf-8') as f:
        # Salvamos uma lista de objetos (um para cada empresa), mantendo o formato hierárquico
        json.dump(output_data_list, f, indent=4, ensure_ascii=False)
    
    print("✅ Análise concluída com sucesso! (Saída formatada por CNPJ)")


# ==============================================================================
# Execução do Script Principal
# ==============================================================================

if __name__ == '__main__':
    # DEFINE OS PATHS AQUI
    INPUT_FILE_PATH = 'output/notas_processadas_unificado.json' # Arquivo de entrada do script anterior
    OUTPUT_FILE_PATH = 'output/analise_por_empresa_unificado.json'
    
    # Garante que a pasta 'output' existe
    if not os.path.exists(os.path.dirname(OUTPUT_FILE_PATH)):
        os.makedirs(os.path.dirname(OUTPUT_FILE_PATH))

    # Executa a função principal de análise
    analyze_tax_data_by_company(INPUT_FILE_PATH, OUTPUT_FILE_PATH)