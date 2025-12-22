from core.query_enhancement import QueryEnhancer
from rag_tools import RAGBridge
import logging
import base64
import json
import re
from dotenv import load_dotenv
import os
import asyncio
load_dotenv()

# Configuração simples de logging local (sem dependência externa)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("CodeZProcessor")



class BaseProcessor:
    def __init__(self):
        self.rag = RAGBridge()

    def fix_base64_padding(self, b64_string):
        return b64_string + '=' * (-len(b64_string) % 4)

    def handle_abap_code_base64(self, abap_code_base64):
        """
        Decodes ABAP code from base64, saves as .md (UTF-8 text) and .bin (binary), returns paths and decoded string.
        """
        abap_code_base64 = self.fix_base64_padding(abap_code_base64)
        temp_md_path = "./temp_abap_code.md"
        abap_code_bytes = base64.b64decode(abap_code_base64)
        
        try:
            abap_code_str = abap_code_bytes.decode("utf-8")
            print("Arquivo decodificado como UTF-8")
        except UnicodeDecodeError:
            abap_code_str = abap_code_bytes.decode("latin-1")
            print("Arquivo decodificado como Latin-1 (fallback)")
        
        with open(temp_md_path, "w", encoding="utf-8") as f:
            f.write(abap_code_str)
    
        return {
            "temp_md_path": temp_md_path,
        }

    def delete_temp_files(self, file_paths):
        """
        Remove arquivos temporários passados na lista file_paths.
        """
        for path in file_paths:
            try:
                os.remove(path)
                print(f"Arquivo temporário removido: {path}")
            except Exception as e:
                print(f"Erro ao remover {path}: {e}")

    def unify_abap_codes(self, abap_codes_list):
        """
        Recebe uma lista de códigos base64, salva cada um como arquivo temporário, unifica em um único arquivo e retorna o base64 do arquivo unificado.
        """
        temp_files = []
        for idx, abap_code_base64 in enumerate(abap_codes_list):
            abap_code_base64 = self.fix_base64_padding(abap_code_base64)
            abap_code_bytes = base64.b64decode(abap_code_base64)
            temp_path = f"./temp_abap_code_unify_{idx}.txt"
            with open(temp_path, "wb") as f:
                f.write(abap_code_bytes)
            temp_files.append(temp_path)

        unified_path = "./temp_abap_code_unified.txt"
        with open(unified_path, "wb") as unified_file:
            for temp_path in temp_files:
                with open(temp_path, "rb") as f:
                    unified_file.write(f.read())

        with open(unified_path, "rb") as f:
            unified_bytes = f.read()
        unified_base64 = base64.b64encode(unified_bytes).decode("utf-8")
        print(f"Arquivo unificado salvo: {unified_path}")

        # Remove arquivos temporários
        self.delete_temp_files(temp_files + [unified_path])

        return unified_base64

    def process_rag_code_z(self, temp_md_path):
        """
        Cria documento, source e indexer no RAG e retorna apenas o index_id.
        """
        logger.info("[SESSION] Criando documento no RAG.")
        doc_resp = self.rag.create_document(file_path=temp_md_path, use_ocr=False)
        document_id = doc_resp.get('id')
        logger.info(f"[SESSION] Documento criado no RAG: {doc_resp}")

        logger.info("[SESSION] Criando source no RAG.")
        source_resp = self.rag.create_source(document_id=document_id)
        source_id = source_resp.get('id')
        logger.info(f"[SESSION] Source criado no RAG: {source_resp}")

        logger.info("[SESSION] Criando indexer no RAG.")
        indexer_resp = self.rag.create_indexer(index_name="Codigo Z teste", sources_ids=[source_id])
        index_id = indexer_resp.get('id')
        logger.info(f"[SESSION] Indexer criado no RAG: {indexer_resp}")
        
        return index_id

    async def process(self, session, request, http_session):
        # 5. Buscar no RAG para cada pergunta melhorada
        logger.info(f"[SESSION] Buscando no RAG para pergunta: {pergunta}")
        trechos = await self.rag.call_rag_api(search_query=pergunta, index_id=index_id)
        resultados.append({
            "index_id_code_z": index_id,
            "pergunta_melhorada": pergunta,
            "resultados_rag": trechos
        })


        # Retorne a lista de resultados ao final do processamento
        logger.info("[SESSION] Finalizando processamento e retornando resultados.")
        return resultados


def load_request(path: str):
    """Carrega request de forma TOLERANTE (comentários, quebras de linha dentro de strings).
    Se falhar em JSON padrão, faz parsing linha a linha simples. É apenas para teste."""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Remove comentários /* */ e // inteiros
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.S)
    content = re.sub(r'//.*', '', content)
    # Normaliza quebras de linha dentro de valores (simplificação para teste)
    compact = ' '.join(line.strip() for line in content.splitlines())
    try:
        data = json.loads(compact)
    except json.JSONDecodeError:
        # Parser super simples linha a linha (chave: valor)
        data = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('{') or line.startswith('}'):
                continue
            if ':' not in line:
                continue
            k, v = line.split(':', 1)
            k = k.strip().strip('"\'')
            v = v.strip().rstrip(',').strip()
            # remove aspas se houver
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            data[k] = v

    class RequestWrapper:
        def __init__(self, d):
            for k, v in d.items():
                setattr(self, k, v)
            if not hasattr(self, 'abap_codes'):
                setattr(self, 'abap_codes', d.get('abap_codes', ''))

    return RequestWrapper(data)




if __name__ == "__main__":
    processor = BaseProcessor()
    request = load_request("CodeZProcessor/request.json")
    session = None
    http_session = None
    # Run the async process method using asyncio
    resultado = asyncio.run(processor.process(session, request, http_session))
    print("RESULTADO FINAL:")
    # print(resultado)
    # Salva o resultado em um arquivo JSON para análise
    with open("resultado_final.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print("Resultado salvo em resultado_final.json")