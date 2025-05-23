import datetime

from databricks.vector_search.client import VectorSearchClient

from .ai_utils import AiUtils


# ###################################
# CLASS AiVectorSearch
# Author: Airton Lira Junior
# Date: 2025-05-23
###################################
class AiVectorSearch():
    def __init__(self, vector_search_endpoint_name:str, source_table_name:str, embedding_dimension=384, primary_key="id", embedding_column="embedding", columns=["content"]):
        """
        Inicializa o vector search.
        """
        self.vector_search_endpoint_name = vector_search_endpoint_name # Seu endpoint
        self.index_table_name = source_table_name + "_index" # Seu índice
        self.source_table_name = source_table_name# Não usado diretamente no predict
        self.embedding_dimension = embedding_dimension
        
        self.primary_key = primary_key
        self.embedding_column = embedding_column
        self.columns = columns

        self._init_vector_search()

    def _init_vector_search(self):
        try:
            self.vsc = VectorSearchClient(disable_notice=True)
            print("VectorSearchClient e MlflowDeploymentClient inicializados no __init__.")
            self.vsc.get_endpoint(name=self.vector_search_endpoint_name)
            print(f"Endpoint VS '{self.vector_search_endpoint_name}' acessível.")
        except Exception as e:
            if "RESOURCE_DOES_NOT_EXIST" in str(e) or "not found" in str(e).lower():
                print(f"Endpoint '{self.vector_search_endpoint_name}' não encontrado. Criando...")
                # Cria o endpoint
                self.vsc.create_endpoint_and_wait(
                    name=self.vector_search_endpoint_name,
                    endpoint_type="STANDARD", # Tipo comum, verifique a documentação para outras opções
                    timeout=datetime.timedelta(seconds=3600)
                )

                print(f"Endpoint '{self.vector_search_endpoint_name}' criado.")
                
                try:
                    endpoint_info_after_create = self.vsc.get_endpoint(name=self.vector_search_endpoint_name)
                    print(f"DEBUG: Informação do endpoint após criação: {endpoint_info_after_create}")
                    print(f"DEBUG: Tipo do endpoint_info_after_create: {type(endpoint_info_after_create)}")
                    endpoint_status = endpoint_info_after_create.get('endpoint_status', {}).get('state', 'UNKNOWN')
                    print(f"Endpoint '{self.vector_search_endpoint_name}' status após criação: {endpoint_status}")
                    if endpoint_status != 'ONLINE':
                        print(f"Aviso: Endpoint '{self.vector_search_endpoint_name}' ainda não está ONLINE após espera.")
                        self.vsc = None 
                except Exception as get_e:
                    print(f"Erro ao verificar status do endpoint '{self.vector_search_endpoint_name}' após tentativa de criação: {get_e}")
                    self.vsc = None 
            else:
                # Outro erro ao tentar obter o endpoint
                print(f"Erro ao verificar/criar endpoint '{self.vector_search_endpoint_name}': {e}")
                self.vsc = None 

        if self.vsc:  # Prossegue se o endpoint existe e está potencialmente online

            # Verifica se o índice existe, cria se não
            existing_indexes = self.vsc.list_indexes(self.vector_search_endpoint_name).get('vector_indexes', [])
            if self.index_table_name not in [idx.get('name') for idx in existing_indexes]:
                print(f"Criando Índice do Vector Search: {self.index_table_name}")

                self.vsc.create_delta_sync_index_and_wait(
                    endpoint_name=self.vector_search_endpoint_name,
                    index_name=self.index_table_name,
                    source_table_name=self.source_table_name ,
                    pipeline_type="TRIGGERED",
                    primary_key=self.primary_key,
                    embedding_dimension=self.embedding_dimension,
                    embedding_vector_column=self.embedding_column,
                    verbose=True, 
                    timeout=datetime.timedelta(days=1)

                )
                print(f"Criação do índice {self.index_table_name} iniciada. A sincronização pode levar alguns minutos. Monitore o status na UI do Databricks.")
            else:
                # Opcional: Dispara sincronização se o índice já existe e o pipeline é TRIGGERED
                index_info = self.vsc.get_index(endpoint_name=self.vector_search_endpoint_name, index_name=self.index_table_name)
                index_describe = index_info.describe()
                if 'delta_sync_index_spec' in index_describe and index_describe.get('delta_sync_index_spec') and index_describe.get('delta_sync_index_spec').get('pipeline_type') == "TRIGGERED":
                    status = index_describe.get('status').get('detailed_state')
                    if status not in ["PROVISIONING", "ONLINE_UPDATING", "ONLINE_NO_PENDING_UPDATE"]:
                        print(f"Índice {self.index_table_name} já existe. Disparando sincronização (se necessário)...")
                        # vsc.sync_index(endpoint_name=vector_search_endpoint_name, index_name=self.index_table_name)
                        index_info.sync()
                        print(f"Comando de disparo de sincronização enviado para {self.index_table_name} (se aplicável).")
                    else:
                        print(f"Índice {self.index_table_name} está atualmente no estado '{status}'. Pulando disparo de sincronização.")
                elif 'delta_sync_index_spec' in index_describe and index_describe.get('delta_sync_index_spec'):
                    print(f"Índice {self.index_table_name} já existe e usa um pipeline CONTINUOUS (sincroniza automaticamente).")
                else:
                    print(f"Índice {self.index_table_name} já existe mas não é um índice Delta Sync ou tipo de pipeline desconhecido.")
    def reload_sync(self):
        index_info = self.vsc.get_index(endpoint_name=self.vector_search_endpoint_name, index_name=self.index_table_name)
        index_info.sync()
    
    def get_index_info(self):
        return self.vsc.get_index(endpoint_name=self.vector_search_endpoint_name, index_name=self.index_table_name).describe()
    
    def get_index_status(self):
        index_info = self.get_index_info()
        return index_info.get('status').get('detailed_state')
    def _format_doc(self, item):
        """Formata um documento para o formato esperado pelo Vector Search."""
        doc = {}
        for i, column in enumerate(self.columns):
            doc[column] = item[i]
            
        return doc
            

    def search_index(self, query_vector, num_results=3, score_threshold=0.0, filters=None):
        """Busca documentos relevantes no índice Vector Search.
        
        """
        if not self.vsc:
            return AiUtils.handler_error("Erro _search_index: vsc (VectorSearchClient) não inicializado.")
        
        if not query_vector:
            return AiUtils.handler_error("Erro _search_index: query_vector está vazio.")

        try:
            print(f"Buscando índice {self.index_table_name}...") # Debug
            index = self.vsc.get_index(endpoint_name=self.vector_search_endpoint_name, index_name=self.index_table_name)
            print(f"Índice {self.index_table_name} encontrado com status: {index.describe()['status']['detailed_state']}")
            results = index.similarity_search(
                query_vector=query_vector,
                num_results=num_results,
                filters=filters,
                score_threshold=score_threshold,
                columns=self.columns # acrescentando 'metadata' no resultado
            )
            print(results)
            
            # Processar 'results' para extrair o contexto
            # Adapte a verificação e extração conforme a estrutura real de 'results'
            if results and isinstance(results, dict) and 'result' in results and isinstance(results['result'], dict) and 'data_array' in results['result']:
                data_array = results['result']['data_array']
                # Extrai o texto do chunk (assumindo que é a primeira coluna retornada)
                relevant_docs = [self._format_doc(item) for item in data_array if item and len(item) > 0 and isinstance(item[0], str)]
                # print(f"Docs relevantes (data_array): {relevant_docs}") # Debug
                return relevant_docs
            elif isinstance(results, dict) and 'docs' in results and isinstance(results['docs'], list):
                relevant_docs = []
                for doc in results['docs']:
                    if hasattr(doc, 'page_content'): relevant_docs.append(doc.page_content)
                    elif isinstance(doc, dict) and 'page_content' in doc: relevant_docs.append(doc['page_content'])
                    elif isinstance(doc, dict) and 'text' in doc: relevant_docs.append(doc['text'])
                    elif isinstance(doc, dict) and 'content' in doc: relevant_docs.append(doc['content']) # Adicionado 'content'
                # print(f"Docs relevantes (docs): {relevant_docs}") # Debug
                return relevant_docs
            else:
                return AiUtils.handler_error(f"Warning _search_index: Formato de results inesperado ou vazio: {results}")
        except Exception as e:
            return AiUtils.handler_error(f"Erro em _search_index durante busca: {e}")
