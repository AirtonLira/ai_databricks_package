import re

import requests

from .ai_utils import AiUtils


###################################
# CLASS AiGithub
# Author: Airton Lira Junior
# Date: 2025-05-23
###################################

class AiReadme:
    """
    Classe para interagir com o README
    """

    ENDPOINT_CATEGORY="/api/v1/categories"
    ENDPOINT_DOC_BY_CATEGORY="/api/v1/categories/#slug#/docs"
    ENDPOINT_DOC_BY_SLUG="/api/v1/docs/#slug#"
    def __init__(self, config:dict):
        """
        Inicializa a classe AiReadme.

        Args:
            config (dict): Configurações para inicialiazação da classe
                url (str): URL base da instância do Readme.
                token (str): Token para autenticação no CReadme.
        """
        AiUtils.validate_config(config, ["url", "token"])
        self.url = config["url"]
        self.token = config["token"]
        self.headers = {
                "authorization": "Basic " + self.token,
                "accept": "application/json"
        }

    @staticmethod
    def get_instance(config:dict):
        return AiReadme(config)            

    def _call_request(self, endpoint):

        try:
            url = url = AiUtils.sanitize_url(self.url + endpoint)
            # Realiza a requisição GET para a URL especificada com os headers
            response = requests.get(url, headers=self.headers)

            # Verifica se a requisição foi bem-sucedida (código de status 2xx)
            response.raise_for_status()  # Levanta uma exceção para códigos de status ruins (4xx ou 5xx)

            # Se a requisição foi bem-sucedida, tenta carregar o conteúdo JSON da resposta
            return response.json()
        except requests.exceptions.RequestException as e:
            # Captura erros gerais de requisição (problemas de conexão, timeouts, etc.)
            print(f"Erro de requisição: {e}")
        except requests.exceptions.HTTPError as e:
            # Captura erros HTTP específicos (códigos de status 4xx ou 5xx)
            print(f"Erro HTTP: {e}")
            print(f"Detalhes do erro: {response.text}")
        except Exception as e:
            # Captura qualquer outro erro inesperado
            print(f"Ocorreu um erro inesperado: {e}")

    def get_all_category_raw(self):
        """
        Busca todas as categorias cadastradas no README

        Args:

        Returns:
            dict: Um dicionário com a toda a resposta do README.
        """
        return self._call_request(AiReadme.ENDPOINT_CATEGORY)
    
    def get_all_doc_by_category_raw(self, category_slug:str):
        """
        Busca todos os documentos de uma categoria do README

        Args:

        Returns:
            dict: Um dicionário com a toda a resposta do README.
        """
        endpoint = AiUtils.change_value_path(AiReadme.ENDPOINT_DOC_BY_CATEGORY, "slug", category_slug)
        return self._call_request(endpoint)

    def get_doc_by_slug_raw(self, slug:str):
        """
        Busca o documento pelo slug

        Args:

        Returns:
            dict: Um dicionário com a toda a resposta do README.
        """
        endpoint = AiUtils.change_value_path(AiReadme.ENDPOINT_DOC_BY_SLUG, "slug", slug)
        return self._call_request(endpoint)


    def get_all_doc(self):
        """
        Busca todos os documentos do README

        Args:

        Returns:
            dict: Um dicionário contendo o 'id', 'title' e 'body' do doc.
        """
        category_list = self.get_all_category_raw()
        all_doc = []
        for category in category_list:
            doc_list = self.get_all_doc_by_category_raw(category["slug"])
            for doc_raw in doc_list:
                all_doc.extend(self.load_doc(doc_raw))
            
        return all_doc

    def _format_body(self, body, title):
        r = '#[^#]'
        if re.match("^" + r, body) is not None:
            body = "# " + title + "\n\n" + body
            body = body.replace("\n##### ", "\n###### ")
            body = body.replace("\n#### ", "\n##### ")
            body = body.replace("\n### ", "\n#### ")
            body = body.replace("\n## ", "\n### ")
            body = body.replace("\n# ", "\n## ")
        else:
            body = "# " + title + "\n\n" + body

        return body
    
    def load_doc(self, doc_raw):
        """
        Dado um doc ele carrega o detalhe desse doc e de seu filhos

        Args:

        Returns:
            dict: Um dicionário contendo o 'id', 'title' e 'body' do doc.
        """
        all_doc = []
        if doc_raw["hidden"] == False:
            doc_details = self.get_doc_by_slug_raw(doc_raw["slug"])
            body = self._format_body(doc_details["body"], doc_details["title"])
            if body is not None and body != "":
                all_doc.append({
                    'id': doc_details["slug"],
                    'title': doc_details["title"],
                    'body': body
                })

            if (len(doc_raw["children"]) > 0):
                for dr in doc_raw["children"]:
                    all_doc.extend(self.load_doc(dr))
    
        return all_doc
