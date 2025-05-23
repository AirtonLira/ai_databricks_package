import json
import logging
import os

import requests


class Databricks(object):
    """
    Gerencia configurações de Model Serving Endpoints no Databricks,
    com foco na atualização dos AI Guardrails.
    """

    def __init__(self, host: str, token: str, endpoint_name: str):
        """
        Inicializa o gerenciador.

        Args:
            host: A URL do workspace Databricks (ex: https://<id>.cloud.databricks.com).
            token: O Personal Access Token (PAT) do Databricks.
            endpoint_name: O nome exato do Model Serving Endpoint.
        """
        if not host or not token or not endpoint_name:
            raise ValueError("Host, token, e endpoint_name são obrigatórios.")
        if not host.startswith("https://"):
            raise ValueError("Host deve começar com https://")

        self.host = host.rstrip('/')  # Garante que não haja barra no final
        self.token = token
        self.endpoint_name = endpoint_name
        self.base_url = f"{self.host}/api/2.0/serving-endpoints"
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        logging.info(f"Gerenciador inicializado para o endpoint '{self.endpoint_name}' em '{self.host}'")

    def _read_list_from_file(self, filepath: str) -> list[str] | None:
        """
        Lê um arquivo (txt ou csv) e retorna uma lista de strings não vazias.
        Método privado auxiliar.

        Args:
            filepath: O caminho para o arquivo.

        Returns:
            Uma lista de strings ou None se ocorrer um erro.
        """
        if not os.path.exists(filepath):
            logging.error(f"Arquivo não encontrado em '{filepath}'")
            return None
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                items = [line.strip() for line in f if line.strip()]
            logging.info(f"Lidos {len(items)} itens de '{filepath}'")
            return items
        except Exception as e:
            logging.exception(f"Erro ao ler o arquivo '{filepath}': {e}")
            return None

    def get_endpoint_config(self) -> dict | None:
        """
        Busca a configuração atual completa do endpoint.

        Returns:
            Um dicionário com a informação do endpoint ou None em caso de erro.
        """
        url = f"{self.base_url}/{self.endpoint_name}"
        logging.info(f"Buscando configuração do endpoint '{self.endpoint_name}'...")
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # Lança exceção para erros HTTP (4xx ou 5xx)
            config = response.json()
            logging.info("Configuração do endpoint obtida com sucesso.")
            return config
        except requests.exceptions.RequestException as e:
            logging.exception(f"Erro ao buscar configuração do endpoint '{self.endpoint_name}': {e}")
            if response is not None:
                logging.error(f"Resposta da API: {response.text}")
            return None

    def update_endpoint_config(self, new_config_payload: dict) -> dict | None:
        """
        Atualiza a configuração do endpoint usando PUT.
        Espera o payload completo para a API PUT.

        Args:
            new_config_payload: O dicionário contendo a chave 'name' e 'config'
                                para a chamada PUT da API.

        Returns:
            A resposta da API em caso de sucesso, ou None em caso de erro.
        """
        url = f"{self.base_url}/{self.endpoint_name}"
        logging.info(f"Tentando atualizar a configuração do endpoint '{self.endpoint_name}'...")
        logging.debug(f"Payload da atualização:\n{json.dumps(new_config_payload, indent=2)}")

        try:
            response = requests.put(url, headers=self.headers, json=new_config_payload)
            response.raise_for_status()
            logging.info(f"Requisição de atualização para '{self.endpoint_name}' enviada com sucesso!")
            # A resposta PUT pode conter a nova config ou informações sobre a operação assíncrona
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.exception(f"Erro ao atualizar configuração do endpoint '{self.endpoint_name}': {e}")
            if response is not None:
                logging.error(f"Resposta da API: {response.text}")
            return None

    def update_ai_guardrails(self, invalid_keywords_filepath: str | None = None,
                             valid_topics_filepath: str | None = None,
                             enable_pii_detection: bool | None = None) -> bool:
        """
        Atualiza a seção AI Guardrails da configuração do endpoint.

        Args:
            invalid_keywords_filepath: Caminho para o arquivo de palavras-chave inválidas.
            valid_topics_filepath: Caminho para o arquivo de tópicos válidos.
            enable_pii_detection: True/False para habilitar/desabilitar detecção de PII (se aplicável).

        Returns:
            True se a requisição de atualização foi enviada com sucesso, False caso contrário.
        """
        current_endpoint_info = self.get_endpoint_config()
        if not current_endpoint_info:
            logging.error("Não foi possível obter a configuração atual. Abortando atualização dos Guardrails.")
            return False

        # A configuração editável está dentro da chave 'config'
        current_config = current_endpoint_info.get("config", {})

        # Garante que as estruturas aninhadas existam
        ai_gateway_config = current_config.setdefault("ai_gateway_config", {})
        ai_guardrails = ai_gateway_config.setdefault("ai_guardrails", {})
        guardrails_input = ai_guardrails.setdefault("input", {})  # Foco na seção de input

        # Processa palavras-chave inválidas
        if invalid_keywords_filepath:
            invalid_keywords = self._read_list_from_file(invalid_keywords_filepath)
            if invalid_keywords is None:
                logging.warning(
                    f"Não foi possível ler palavras inválidas de '{invalid_keywords_filepath}'. Nenhuma alteração será feita para esta lista.")
            else:
                # A API espera um objeto com uma chave "keywords" contendo a lista
                guardrails_input["invalid_keywords_for_input"] = {"keywords": invalid_keywords}
                logging.info("Lista de palavras inválidas preparada para atualização.")

        # Processa tópicos válidos
        if valid_topics_filepath:
            valid_topics = self._read_list_from_file(valid_topics_filepath)
            if valid_topics is None:
                logging.warning(
                    f"Não foi possível ler tópicos válidos de '{valid_topics_filepath}'. Nenhuma alteração será feita para esta lista.")
            else:
                guardrails_input["valid_topics_for_input"] = {"keywords": valid_topics}
                logging.info("Lista de tópicos válidos preparada para atualização.")

        # Processa detecção de PII (exemplo, verificar estrutura exata na API se necessário)
        if enable_pii_detection is not None:
            # A estrutura exata pode variar (ex: pode ser um objeto {"enabled": True/False})
            # Verifique a documentação da API específica
            pii_config = guardrails_input.setdefault("pii_detection_for_input", {})
            pii_config["enabled"] = enable_pii_detection
            logging.info(f"Detecção de PII definida para: {enable_pii_detection}")

        # Prepara o payload final para a API PUT
        # A API PUT /api/2.0/serving-endpoints/{name} espera o nome e a config completa
        update_payload = {
            "name": self.endpoint_name,
            "config": current_config  # Envia a config completa modificada
        }

        # Envia a atualização
        update_result = self.update_endpoint_config(update_payload)

        if update_result:
            logging.info(
                "Operação de atualização dos Guardrails iniciada. Pode levar alguns minutos para o endpoint ser totalmente atualizado.")
            return True
        else:
            logging.error("Falha ao iniciar a atualização dos Guardrails.")
            return False
