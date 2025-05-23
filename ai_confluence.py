from io import BytesIO

from atlassian import Confluence
from docling.document_converter import DocumentConverter
from docling_core.types.io import DocumentStream

from .ai_utils import AiUtils


###################################
# CLASS AiConfluence
# Author: Airton Lira Junior
# Date: 2025-05-23
###################################

class AiConfluence:
    """
    Classe para interagir com o Confluence e buscar informações das páginas publicadas.
    """
    def __init__(self, config:dict):
        """
        Inicializa a classe AiConfluence.

        Args:
            config (dict): Configurações para inicialiazação da classe
                url (str): URL base da instância do Confluence.
                user (str): Nome de usuário para autenticação no Confluence.
                password (str): Senha para autenticação no Confluence.
        """
        AiUtils.validate_config(config, ["url", "user", "password"])
        self.confluence = Confluence(url=config["url"], username=config["user"], password=config["password"])

    @staticmethod
    def get_instance(config:dict):
        return AiConfluence(config)            
    
    def _format_text(self, html:str, title:str):
        html = "<h1>" + title + "</h1>" + html

        converter = DocumentConverter()
        stream = BytesIO(html.encode('utf-8'))
        file_name =  AiUtils.sanitize_text(title, allow_accents=False, allow_upper_lower=False, allow_parentheses=False, allow_space=False) + ".html"
        result = converter.convert(DocumentStream(name=file_name, stream=stream))

        return result.document.export_to_markdown()

    def _fix_encode(self, original_text):
        try:
            # 1. Codifica de volta para bytes usando a codificação errada (Latin-1)
            bytes_original = original_text.encode('latin-1') # ou 'iso-8859-1' ou 'cp1252'

            # 2. Decodifica os bytes usando a codificação correta (UTF-8)
            fixed_text = bytes_original.decode('utf-8')
        except:
            fixed_text = original_text
        
        return fixed_text
    def _format_page(self, page_id:str, page:dict):
        """
        Formata o resultado da api do confluence em um dict reduzido

        Args:
            page_id (str): ID da página desejada.
            page (dict): Objeto que representa uma página retornada pelo confluence.

        Returns:
            dict: Um dicionário contendo o 'id', 'title' e 'body' da página,
                  ou None se a página não for encontrada ou ocorrer um erro.
        """
    
        if page and 'title' in page and 'body' in page:

            title = self._fix_encode(page['title'])
            page_content_html = page['body']['storage']['value']

            page_content = self._format_text(page_content_html, title)

            page_content = page_content.replace("\u00A0", " ")
            

            webui = None
            if '_links' in page and "webui" in page["_links"]:
                links = page["_links"]
                webui = links["webui"]
            else:
                print("--------------------------------------------------- " + page["title"])
            return {
                'id': page_id,
                'title': title,
                'body': page_content,
                "webui": webui
            }
        else:
            print(f"Página com ID '{page_id}' não encontrada'.")
            return None
        

    def get_page_by_id(self, page_id:str):
        """
        Busca informações de uma página específica baseado no id.

        Args:
            page_id (str): ID da página desejada.

        Returns:
            dict: Um dicionário contendo o 'id', 'title' e 'body' da página,
                  ou None se a página não for encontrada ou ocorrer um erro.
        """
        try:
            page = self.confluence.get_page_by_id(page_id, expand='body.storage')
            return self._format_page(page_id, page)
        except Exception as e:
            print(f"Ocorreu um erro ao buscar a página '{page_id}': {e}")
            return None
        
    def get_all_pages_by_space_key(self, space_key:str, start:int=0, limit:int=-1):
        """
        Busca uma lista de páginas baseado na key do espaço.

        Args:
            space_key (str): KEY do space desejado.
            start (int): OPTIONAL: O início da coleção para ser retornado. Default: 0.
            limit (int): OPTIONAL: O limite de números de páginas para ser retornada. Default: 50

        Returns:
            list: Uma lista de dicionários contendo com o 'id', 'title' e 'body' da página,
                  ou None se ocorrer um erro.
        """
        try:

            _limit = limit if limit != -1 else 50
            all_pages = [] 
            while True:
                response = self.confluence.get_all_pages_from_space_raw(
                    space=space_key,
                    start=start,
                    status='current',
                    expand='body.storage',
                    limit=_limit
                )

                results = response.get("results", [])
                
                for page in results:
                    all_pages.append(self._format_page(page["id"], page))

                # Break o loop quando atigi a quantidade desejada
                if limit != -1 or len(results) < _limit:
                    break

                # Increment the start index for the next batch
                start += _limit
            return all_pages
        except Exception as e:
            print(f"Ocorreu um erro ao buscar a página pelo space '{space_key}': {e}")
            return None