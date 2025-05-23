import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings
from pyspark.sql.functions import pandas_udf
from pyspark.sql.types import ArrayType, DoubleType

from .ai_utils import AiUtils


###################################
# CLASS AiEmbedding
# Author: Airton Lira Junior
# Date: 2025-05-23
################################### 

class AiEmbedding:

    @staticmethod
    def process_embeddings(list_text: list, model_name="sentence-transformers/all-MiniLM-L6-v2") -> list:
        try:
            # Inicializa o cliente
            deploy_client = HuggingFaceEmbeddings(model_name=model_name, model_kwargs={"device": "cpu"})
            if not deploy_client:
                return AiUtils.handler_error("Erro _embed_query: deploy_client não inicializado.")
            embeddings = []
            for text in list_text:
                embeddings.append(deploy_client.embed_query(text))
            return embeddings
        except Exception as api_error:
            return AiUtils.handler_error(f"Erro ao chamar endpoint da API de embedding {model_name}: {api_error}")

    @staticmethod
    def process_embedding(text: str):
        if not text:
            return AiUtils.handler_error("Erro _embed_query: text not informed.")
        processed_embeddings = AiEmbedding.process_embeddings([text])
        return processed_embeddings[0]

    @staticmethod
    @pandas_udf(ArrayType(DoubleType()))
    def process_embeddings_udf(texts: pd.Series) -> pd.Series:
        print(f"DEBUG UDF: Processando um lote de {len(texts)} textos no executor.")
        try:
            # Lista para armazenar embeddings
            all_embeddings = []
            batch_size = 100
            # Processa em lotes de 100 registros
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size].tolist()
                print(f"DEBUG UDF: Processando lote {i // batch_size + 1} com {len(batch_texts)} textos")
                processed_embeddings = AiEmbedding.process_embeddings(batch_texts)
                all_embeddings.extend(processed_embeddings)
                print(f"DEBUG UDF: Embeddings recebidos para lote {i // batch_size + 1}")

            # Garante que todos os embeddings sejam listas de floats com o mesmo comprimento
            result_series = pd.Series([emb if emb else [0.0] for emb in all_embeddings], index=texts.index)

            # Garante que cada elemento é uma lista de floats
            for i, item in enumerate(result_series):
                if not isinstance(item, list):
                    print(f"Erro: Item {i} não é uma lista: {type(item)}. Substituindo por valor default.")
                    result_series[i] = [0.0]

            return result_series
        except Exception as api_error:
            return AiUtils.handler_error(f"Erro UDF: Erro ao chamar endpoint da API de embedding: {api_error}")
