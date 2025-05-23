import base64
import json
import os

import boto3


###################################
# CLASS AiSecret
# Author: Airton Lira Junior
# Date: 2025-05-23
###################################

class AiSecret:
    """
    Classe base para buscar os segredos.
    """
    def __init__(self, config):
        """
        Inicializa a classe AiSecret.

        Args:
            config (dict): Configurações para inicialiazação da classe
        """

    @staticmethod
    def get_instance(config:dict):
        if ((config["type"].upper() if config["type"] is not None else "OS") == "AWS"):
            return AiAwsSecret(config)            
        else:
            return AiOsSecret(config)
        
    def get_secret(self, secret_name:str):
        raise Exception("method not implemented.")

    def get_map_secret(self, secret_name:str, secret_key:str):
        secret = self.get_secret(secret_name)
        if secret is not None and secret.startswith('{'):
            return json.loads(secret)[secret_key]
        return None

###################################
# CLASS AiOsSecret
# Author: Leonaro Cabral
# Date: 2025-04-11
################################### 

class AiOsSecret(AiSecret):
    """
    Classe para interagir os segredos que estão em váriável de ambiente
    """
    def __init__(self, config:dict):
        """
        Inicializa a classe AiOsSecret.

        Args:
            config (dict): Configurações para inicialiazação da classe
        """
        super().__init__(config)

    # Override
    def get_secret(self, secret_name:str):
        return os.environ.get(secret_name)
    
###################################
# CLASS AiAwsSecret
# Author: Leonaro Cabral
# Date: 2025-04-11
###################################

class AiAwsSecret (AiSecret):
    """
    Classe para interagir com os secrets na AWS
    """
    def __init__(self, config:dict):
        """
        Inicializa a classe AiAwsSecret.

        Args:
            config (dict): Configurações para inicialiazação da classe
                host (str): zone do S3
        """
        super().__init__(config)
        self.host = "" if config["host"] is None else config["host"]
        # Inicializa o cliente do S3
        self.aws_client = boto3.client('secretsmanager', region_name=("us-east-2" if config["host"] is None else config["host"]))

     # Override
    def get_secret(self, secret_name:str):
        try:
            response = self.aws_client.get_secret_value(SecretId=secret_name)
           # Verifica se o segredo é uma string ou um binário
            if 'SecretString' in response:
                secret = response['SecretString']
                return secret
            elif 'SecretBinary' in response:
                return base64.b64decode(response['SecretBinary']).decode('utf-8')
            else:
                print(f"Erro: Resposta inesperada do Secrets Manager para '{secret_name}'.")
                return None

        except self.aws_client.exceptions.ResourceNotFoundException:
            print(f"Erro: Segredo '{secret_name}' não encontrado na região '{self.host}'.")
            return None
        except Exception as e:
            print(f"Erro ao buscar o segredo '{secret_name}': {e}")
            return None
