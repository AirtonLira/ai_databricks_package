from .ai_embedding import AiEmbedding
from .ai_llm_client import AiLlmClient
from .ai_vector_search import AiVectorSearch


# ###################################
# CLASS AiRagChatModel
# Author: Airton Lira Junior
# Date: 2025-05-23
###################################

class AiRagChatModel():
    def __init__(self, vector_search_endpoint_name: str, source_table_name: str,
                 llm_model_name: str = "databricks-meta-llama-3-1-8b-instruct", max_tokens: int = 8000,
                 temperature: float = 0.1, embedding_dimension:int=384):
        """
        Inicializa o modelo. Os clientes são inicializados aqui,
        pois geralmente são seguros para serialização ou lidam com ela.
        As configurações são definidas como atributos.
        """
        self.vectorSearch = AiVectorSearch(vector_search_endpoint_name, source_table_name, embedding_dimension=embedding_dimension, columns=["content", "reference_url"])
        self.llmClient = AiLlmClient(llm_model_name, max_tokens, temperature)

    def _embed_query(self, user_query):
        return AiEmbedding.process_embedding(user_query)

    def _search_index(self, query_vector, num_results=3, score_threshold=0.6, filters = None):
        return self.vectorSearch.search_index(query_vector, num_results, score_threshold, filters = filters)

    def _create_augmented_prompt(self, user_query, context, chat_history=""):
        return self.create_prompt(user_query, context, chat_history=chat_history)

    def _get_llm_response(self, prompt):
        return self.llmClient.call(prompt)

    def create_prompt(self, user_query, context, chat_history=""):
        """
        Cria o prompt aumentado para o LLM.
        (Mantido igual ao seu exemplo, com chaves escapadas)
        """
        system_prompt = """
            Você é o Assistente Técnico , especialista em APIs da plataforma BaaS. Seu objetivo é esclarecer dúvidas de desenvolvedores sobre regras de negócio, fluxos de integração e endpoints, de forma respeitosa e formal, sempre em português do Brasil.
    
            PRINCÍPIOS CHAVE:
            1.  **PERSONA:** Aja como "Assistente Técnico ". Não se revele como IA. Mantenha tom profissional e foco na plataforma.
            2.  **LÓGICA DE RESPOSTA:**
                * **Perguntas Técnicas (APIs, código, fluxos , regras de negócio):** Responda ESTritamente com base no `<contexto>`. Se o contexto for insuficiente, informe que não encontrou a informação e peça para reformular. Não invente.
                * **Perguntas Não Técnicas (saudações, conversas gerais não sobre a API):** Pode usar conhecimento geral, mesmo sem `<contexto>`, mas NÃO forneça dados técnicos  que não estejam no `<contexto>`. Se a conversa virar técnica, volte à regra anterior.
                * **Idioma do Contexto Técnico:** Mantenha o idioma original de exemplos de código/payloads do `<contexto>`, mas explique em português.
            3.  **FORMATAÇÃO (Markdown Obrigatório):**
                * Parágrafos: Quebras duplas.
                * Listas: Hífens ou asteriscos.
                * Blocos de Código: Crases triplas (```), com linguagem (ex: ```json).
                * Inline: Crase simples (`campo_exemplo`).
                * Ênfase: Negrito (`**texto**`).
                * Estrutura: Respostas claras e bem estruturadas.
            4.  **RESTRIÇÕES IMPORTANTES:**
                * NÃO se identifique como IA.
                * NÃO repita sua persona desnecessariamente.
                * NÃO forneça informações técnicas fora do `<contexto>`.
                * NÃO forneça links externos (a menos que no `<contexto>` e relevantes).
                * NÃO dê exemplos de API a menos que solicitado ou essencial para explicar algo do `<contexto>`.
                * NÃO especule nem dê opiniões.
    
            CONTEXTO E HISTÓRICO:
            <contexto>
            {context}
            </contexto>
    
            <dialog_history>
            {chat_history}
            </dialog_history>
    
            PERGUNTA DO USUÁRIO:
            {query}
    
            SUA RESPOSTA (em Markdown):
        """
        if not context:
            print("Aviso _create_augmented_prompt: Contexto está vazio.")
            return "Desculpe não encontrei informações sobre {user_query}."
        return system_prompt.format(context=context, query=user_query, chat_history=chat_history)

    def run(self, user_query: str, chat_history: list = None, num_results: int=3, score_threshold: float = 0.6, filters = None):
        final_answer = None

        try:
            if not user_query or user_query.strip() == "":
                return "Como posso te ajudar?."

            # 1. Gerar embedding para a consulta
            try:
                query_vector = self._embed_query(user_query)
                if not query_vector or isinstance(query_vector, str) and query_vector.startswith("Erro"):
                    print(f"Falha ao gerar embedding: {query_vector}")
            except Exception as e:
                print(f"Erro ao gerar embedding: {e}")
                query_vector = None

            # 2. Buscar contexto relevante (se embedding foi gerado)
            retrieved_context = ""
            if query_vector and not isinstance(query_vector, str):
                try:
                    retrieved_context = self._search_index(query_vector, num_results=num_results, score_threshold=score_threshold, filters=filters)
                    if isinstance(retrieved_context, str) and retrieved_context.startswith("Erro"):
                        print(f"Falha na busca do índice: {retrieved_context}")
                        retrieved_context = ""
                    # else:
                        # print(f"Contexto recuperado: '{retrieved_context[:100]}...'")
                except Exception as e:
                    print(f"Erro durante a busca no índice vetorial: {e}")
                    retrieved_context = ""
            else:
                print(f"Predict: Pulando busca no índice pois query_vector não é válido: {query_vector}")
                retrieved_context = ""

            # 3. Formatar histórico de chat no novo formato
            formatted_history = ""
            if chat_history:
                for msg in chat_history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    formatted_history += (
                            "<|eot_id|><|start_header_id|>"
                            + role
                            + "<|end_header_id|>\n\n"
                            + content.strip()
                            + "\n"
                    )
            # 4. Criar prompt aumentado (incluindo histórico)
            try:
                augmented_prompt = self._create_augmented_prompt(
                    user_query,
                    retrieved_context,
                    chat_history=formatted_history
                )
                if isinstance(augmented_prompt, str) and augmented_prompt.startswith("Aviso"):
                    print(f"Aviso ao criar prompt: {augmented_prompt}")
            except Exception as e:
                print(f"Erro ao criar prompt aumentado: {e}")
                augmented_prompt = None

            # 5. Chamar LLM para gerar a resposta final
            final_answer = None
            if augmented_prompt:
                try:
                    final_answer = self._get_llm_response(augmented_prompt)
                    if isinstance(final_answer, str) and final_answer.startswith("Erro"):
                        print(f"Erro retornado pelo LLM: {final_answer}")
                except Exception as e:
                    print(f"Erro ao chamar o LLM: {e}")
                    final_answer = f"Ocorreu um erro ao tentar gerar a resposta para: '{user_query}'. Por favor, tente novamente."
            else:
                # Caso onde _create_augmented_prompt retorne None/vazio
                print("Erro interno ao criar o prompt para o LLM.")
                final_answer = f"Não foi possível processar sua pergunta '{user_query}' devido a um erro interno na criação do prompt."


        except Exception as e:
            print(f"Erro ao chamar o LLM: {e}")
            final_answer = f"Ocorreu um erro ao tentar gerar sua resposta para: '{user_query}'. Por favor, tente novamente."

        return final_answer
