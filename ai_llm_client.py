from mlflow.deployments import get_deploy_client

from .ai_utils import AiUtils


# ###################################
# CLASS AiLlmClient
# Author: Airton Lira Junior
# Date: 2025-05-23
###################################

class AiLlmClient():
    def __init__(self, llm_model_name:str="databricks-meta-llama-3-1-8b-instruct", max_tokens:int=8000, temperature:float=0.1):
        """
        Inicializa o modelo. Os clientes são inicializados aqui,
        pois geralmente são seguros para serialização ou lidam com ela.
        As configurações são definidas como atributos.
        """
        self.llm_model_name = llm_model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.deploy_client = get_deploy_client("databricks")

    
    def call(self, prompt) -> str:
        """Chama o LLM para gerar a resposta final."""
        if not self.deploy_client:
            return AiUtils.handler_error("Erro _get_llm_response: deploy_client não inicializado.")

        try:
            # print(f"Chamando LLM (interno) com prompt: {prompt[:500]}...") # Debug (cuidado com prompt longo)
            response = self.deploy_client.predict(
                endpoint=self.llm_model_name,
                inputs={
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": self.max_tokens, # Ajuste conforme necessário
                    "temperature": self.temperature
                }
            )

            if 'choices' in response and response['choices']:
                if 'message' in response['choices'][0] and 'content' in response['choices'][0]['message']:
                    return response['choices'][0]['message']['content']
                else:
                    return AiUtils.handler_error(f"Erro _get_llm_response: Resposta LLM incompleta. Choice: {response['choices'][0]}")
            else:
                return AiUtils.handler_error(f"Erro _get_llm_response: Resposta LLM inesperada. Response: {response}")
        except Exception as e:
            return AiUtils.handler_error(f"Erro _get_llm_response ao chamar endpoint LLM {self.llm_model_name}: {e}")
    