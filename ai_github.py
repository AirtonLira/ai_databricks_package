import tempfile
from tempfile import NamedTemporaryFile

import os
import requests

from .ai_file_utils import AiFileUtils
from .ai_utils import AiUtils


###################################
# CLASS AiGithub
# Author: Airton Lira Junior
# Date: 2025-05-23
###################################

class AiGithub:
    """
    Classe para interagir com o github via HTTPS
    """
    ENDPOINT_BRANCH = "/archive/refs/heads/#branch#.zip"
    ENDPOINT_FILE = "/raw/refs/heads/#branch#/"
    def __init__(self, config:dict):
        """
        Inicializa a classe AiGithub.

        Args:
            config (dict): Configurações para inicialiazação da classe
 
        """
        AiUtils.validate_config(config, ["token", "owner", "repo", "branch"])

        self.headers = {'Authorization': f'Bearer {config["token"]}'}
        self.url = (config["url"] if ("url" in config and config["url"] != "") else "https://github.com/#owner#/#repo#")
        self.owner = config["owner"]
        self.repo = config["repo"]
        self.branch = config["branch"]

        self.url = AiUtils.change_value_path(self.url, "owner", self.owner)
        self.url = AiUtils.change_value_path(self.url, "repo", self.repo)

    @staticmethod
    def get_instance(config:dict):
        return AiGithub(config)            
    
    def download_branch(self) -> str:
        url = self.url + AiGithub.ENDPOINT_BRANCH
        url = AiUtils.sanitize_url(AiUtils.change_value_path(url, "branch", self.branch))

        temp_file_name = AiUtils.sanitize_file_path(self.owner + "_" + self.repo + "_" + self.branch + "_").replace("-", "_")

        temp_file_path = None
        try:
            extract_path = None
            # Cria um arquivo temporário
            with NamedTemporaryFile(delete=False, prefix=temp_file_name, suffix=".zip") as temp_file:
                temp_file_path = temp_file.name

                print(f"Baixando {url} para {temp_file_path}.")

                # Usar stream=True é bom para arquivos grandes
                response = requests.get(url, headers=self.headers, stream=True, allow_redirects=True)
                response.raise_for_status() # Verifica se houve erro HTTP (4xx ou 5xx)

                for chunk in response.iter_content(chunk_size=8192):
                    # Escreve os chunks no arquivo local
                    temp_file.write(chunk)

            extract_path = AiUtils.sanitize_file_path(tempfile.gettempdir() + "/extract/")

            return_path = AiUtils.sanitize_file_path(extract_path + "/" + self.repo + "-" + self.branch)

            if os.path.exists(return_path):
                AiFileUtils.delete_path(return_path, True)

            print(f"Descompactando o arquivo para {extract_path}")

            if extract_path: # Verifica se há um diretório no path (não é apenas um nome de arquivo)
                os.makedirs(extract_path, exist_ok=True)

            AiFileUtils.extract_zip(temp_file_path, extract_path)

            print(f"Download concluído")

            return return_path

        except requests.exceptions.RequestException as e:
            print(f"Erro durante o download: {e}")
            # Se for erro 404, pode ser que o repo/branch não existe ou o token não tem permissão
            if response.status_code == 404:
                print("Verifique o nome do usuário/repositório/branch e as permissões do token.")
            elif response.status_code == 401:
                print("Erro de autenticação. Verifique se o token está correto e válido.")

        finally:
            if temp_file_path:
                AiFileUtils.delete_path(temp_file_path, True)
        return None
    
