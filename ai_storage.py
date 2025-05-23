import io
import json
import os
import shutil
from tempfile import NamedTemporaryFile

import boto3
import botocore

from .ai_utils import AiUtils


###################################
# CLASS AiStorage
# Author: Airton Lira Junior
# Date: 2025-05-23
################################### 

class AiStorage:
    """
    Classe base para interagir com o storage.
    """
    def __init__(self, config):
        """
        Inicializa a classe AiStorage.

        Args:
            config (dict): Configurações para inicialiazação da classe
                host (str): path (quando for DISK) e zone (Quando for S3)
                base_path (str): path (quando for DISK) e bucket e path (Quando for S3)
        """
        AiUtils.validate_config(config, ["host", "base_path"])
        self.host = "" if config["host"] is None else config["host"]
        self.base_path = "" if config["base_path"] is None else config["base_path"]

    @staticmethod
    def get_instance(config:dict):
        """
        retorna a instância pelo tipo solicitado

        Args:
            config (dict): Configurações para inicialiazação da classe
                host (str): path (quando for DISK) e zone (Quando for S3)
                base_path (str): path (quando for DISK) e bucket e path (Quando for S3)
                type (str): (DISK/AWS) DEFAULT: DISK
        """
        if ((config["type"].upper() if config["type"] is not None else "DISK") == "AWS"):
            return AiAwsStorage(config)            
        else:
            return AiDiskStorage(config)
    
    def get_base_path(self):
        return self.base_path
    
    def save(self, file_path:str, file_name:str, content:str, metadata:dict = None):
        """
        Salva um conteúdo em um arquivo no caminho especificado.

        Args:
            file_path (str): O caminho para o arquivo a ser criado/modificado.
            file_name (str): O nome do arquivo a ser criado/modificado.
            content (str): O texto a ser escrito no arquivo.
        """
        raise Exception("method not implemented.")

    def save_by_file(self, file_path:str, file_name:str, local_path:str, metadata:dict = None):
        """
        Faz upload de um arquivo para um bucket S3.

        Args:
            file_path (str): O caminho para o arquivo a ser criado/modificado.
            file_name (str): O nome do arquivo a ser criado/modificado.
            local_path (str): path local onde está o arquivo.

        Returns:
            bool: True se o upload for bem-sucedido, False caso contrário.
        """
        raise Exception("method not implemented.")
    
    def list_path(self, path:str, prefix:str="", type:str="") -> list:
        """
        Lista todos os arquivos e subpastas (prefixos) dentro de uma path.

        Args:
            path (str): pasta para busca ''.
            prefix (str, optional): Um prefixo para filtrar os resultados. Defaults para ''.
            type (str, optional): tipo da procura (FILE/PATH). Defaults para ''.

        Returns:
            list : Lista todos os arquivos e subpastas (prefixos) dentro de uma path. 
        """
        raise Exception("method not implemented.")
    
    def download_file(self, file_path:str, file_name:str, local_path:str):
        raise Exception("method not implemented.")
###################################
# CLASS AiDiskStorage
# Author: Leonaro Cabral
# Date: 2025-04-11
################################### 
#  
class AiDiskStorage(AiStorage):
    """
    Classe para interagir com o arquivos em disco
    """
    def __init__(self, config:dict):
        """
        Inicializa a classe AiDiskStorage.

        Args:
            config (dict): Configurações para inicialiazação da classe
                host (str): path no disco
                base_path (str): path2 no disco
                type (str): DISK
        """
        super().__init__(config)

    # Override
    def save(self, file_path:str, file_name:str, content:str, metadata:dict = None):
        """
        Salva um texto no Disco em um arquivo no caminho especificado.

        Args:
            file_path (str): O caminho para o arquivo a ser criado/modificado.
            file_name (str): O nome do arquivo a ser criado/modificado.
            content (str): O texto a ser escrito no arquivo.
        """
        file = AiUtils.sanitize_file_path(self.host + "/" + self.base_path + "/" + ((file_path + "/") if file_path is not None and file_path != "" else "") + file_name)

        try:
            with open(file, 'w', encoding='utf-8') as arquivo:
                arquivo.write(content)

            print(f"Texto salvo com sucesso em: {file}")
            return True
        except FileNotFoundError:
            print(f"Erro: O diretório '{path}' não foi encontrado.")
            return False
        except PermissionError:
            print(f"Erro: Permissão negada para acessar o diretório '{path}'.")
            return False
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")
            return False
    
    # Override
    def save_by_file(self, file_path:str, file_name:str, local_path:str, metadata:dict = None):
        """
        Faz upload de um arquivo para um bucket S3.

        Args:
            file_path (str): O caminho para o arquivo a ser criado/modificado.
            file_name (str): O nome do arquivo a ser criado/modificado.
            local_path (str): path local onde está o arquivo.

        Returns:
            bool: True se o upload for bem-sucedido, False caso contrário.
        """
        # Verifica se o arquivo local existe
        if not os.path.exists(local_path):
            print(f"Erro: Arquivo local não encontrado em '{local_path}'")
            return False
        
        file = AiUtils.sanitize_file_path(self.host + "/" + self.base_path + "/" + ((file_path + "/") if file_path is not None and file_path != "" else "") + file_name)

        # Verificar se a origem e o destino são o mesmo arquivo
        # shutil.copy2 levantaria shutil.SameFileError, mas é bom verificar antes.
        if os.path.abspath(local_path) == os.path.abspath(file):
             print(f"Erro: O arquivo de origem e destino são os mesmos ('{local_path}').")
             return False

        try:
            shutil.copy2(local_path, file)
            print(f"Sucesso: Arquivo '{local_path}' duplicado como '{file}'.")
            return True
        except FileNotFoundError:
            print(f"Erro: O diretório '{path}' não foi encontrado.")
            return False
        except PermissionError:
            print(f"Erro: Permissão negada para acessar o diretório '{path}'.")
            return False
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")
            return False

    def list_path(self, path:str, prefix:str="", type:str="") -> list:
        """
        Lista todos os arquivos e subpastas (prefixos) dentro de uma path.

        Args:
            path (str): pasta para busca ''.
            prefix (str, optional): Um prefixo para filtrar os resultados. Defaults para ''.
            type (str, optional): tipo da procura (FILE/PATH). Defaults para ''.

        Returns:
            list : Lista todos os arquivos e subpastas (prefixos) dentro de uma path. 
        """
        files = []
        path = AiUtils.sanitize_file_path(self.host + "/" + self.base_path + "/" + ((path) if path is not None and path != "" else ""))
        try:
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                if type != "PATH" and os.path.isfile(full_path):
                    files.append({'name': full_path, 'type': "FILE"})
                elif type != "FILE" and os.path.isdir(full_path):
                    files.append({'name': full_path, 'type': "PATH"})
            
            return files
        except FileNotFoundError:
            print(f"Erro: O diretório '{path}' não foi encontrado.")
            return None
        except PermissionError:
            print(f"Erro: Permissão negada para acessar o diretório '{path}'.")
            return None
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")
            return None

###################################
# CLASS AiAwsStorage
# Author: Leonaro Cabral
# Date: 2025-04-11
################################### 

class AiAwsStorage (AiStorage):
    """
    Classe para interagir com os arquivos no Aws
    """
    def __init__(self, config:dict):
        """
        Inicializa a classe AiAwsStorage.

        Args:
            config (dict): Configurações para inicialiazação da classe
                host (str): path no disco
                base_path (str): path2 no disco
                type (str): AWS
        """
        super().__init__(config)
        # Inicializa o cliente do S3
        self.aws_client = boto3.client('s3', region_name=("us-east-2" if config["host"] is None else config["host"]))
        
    # Override
    def save(self, file_path:str, file_name:str, content:str, metadata:dict = None):
        """
        Salva um texto no S3 em um arquivo no caminho especificado.

        Args:
            file_path (str): O caminho para o arquivo a ser criado/modificado.
            file_name (str): O nome do arquivo a ser criado/modificado.
            content (str): O texto a ser escrito no arquivo.
        Returns:
            bool: True se o upload for bem-sucedido, False caso contrário.
        """
        object_name = AiUtils.sanitize_file_path(((file_path + "/") if (file_path is not None and file_path != "") else "") + file_name)
        try:
            self.aws_client.put_object(Body=content.encode('utf-8'), Bucket=self.base_path, Key=object_name)
            if (metadata is not None):
                metadata_json = json.dumps(metadata)
                metadata_name = AiUtils.sanitize_file_path(((file_path + "/") if (file_path is not None and file_path != "") else "") + "/.metadata/" + file_name + ".metadata")
                self.aws_client.put_object(Body=metadata_json.encode('utf-8'), Bucket=self.base_path, Key=metadata_name)
            print(f"Arquivo '{object_name}' subido com sucesso para o bucket '{self.base_path}'.")
            return True
        except botocore.exceptions.NoCredentialsError:
            print("Erro: Credenciais AWS não encontradas.")
            print("Configure suas credenciais via variáveis de ambiente, ~/.aws/credentials, ou role do IAM.")
            return False
        except botocore.exceptions.PartialCredentialsError:
            print("Erro: Credenciais AWS incompletas.")
            return False
        except botocore.exceptions.ClientError as e:
            # Erros específicos do serviço AWS (S3 neste caso)
            error_code = e.response.get("Error", {}).get("Code")
            error_message = e.response.get("Error", {}).get("Message")
            if error_code == 'NoSuchBucket':
                print(f"Erro: O bucket '{self.base_path}' não existe.")
            elif error_code == 'AccessDenied':
                print(f"Erro: Acesso negado ao bucket '{self.base_path}' ou ao tentar criar o objeto '{object_name}'. Verifique as permissões do IAM.")
            else:
                print(f"Erro do Cliente S3 ao fazer upload: {error_code} - {error_message}")
            # Você pode querer inspecionar mais o objeto 'e' para detalhes
            # print(e.response)
            return False
        except Exception as e:
            # Captura outros erros inesperados
            print(f"Ocorreu um erro inesperado durante o upload: {e}")
            return False
    
    # Override
    def save_by_file(self, file_path:str, file_name:str, local_path:str, metadata:dict = None):
        """
        Faz upload de um arquivo para um bucket S3.

        Args:
            file_path (str): O caminho para o arquivo a ser criado/modificado.
            file_name (str): O nome do arquivo a ser criado/modificado.
            local_path (str): path local onde está o arquivo.

        Returns:
            bool: True se o upload for bem-sucedido, False caso contrário.
        """
        # Verifica se o arquivo local existe
        if not os.path.exists(local_path):
            print(f"Erro: Arquivo local não encontrado em '{local_path}'")
            return False

        print(f"Iniciando upload de '{local_path}' para S3 bucket '{self.base_path}'...")

        object_name = AiUtils.sanitize_file_path(((file_path + "/") if (file_path is not None and file_path != "") else "") + file_name)
        try:

            # O método upload_file gerencia arquivos grandes e multipart upload automaticamente.
            # Argumentos: CaminhoLocal, NomeBucket, ChaveObjetoS3
            response = self.aws_client.upload_file(local_path, Bucket=self.base_path, Key=object_name)

            if (metadata is not None):
                metadata_json = json.dumps(metadata)
                metadata_name = AiUtils.sanitize_file_path(((file_path + "/") if (file_path is not None and file_path != "") else "") + "/.metadata/" + file_name + ".metadata")
                self.aws_client.put_object(Body=metadata_json.encode('utf-8'), Bucket=self.base_path, Key=metadata_name)

            # Se o método não levantar exceção, o upload foi (provavelmente) bem-sucedido.
            # A resposta para upload_file é None em caso de sucesso.
            print("Upload concluído com sucesso!")
            return True

        except FileNotFoundError:
            # Redundante devido à verificação inicial, mas bom ter
            print(f"Erro: Arquivo local não encontrado em '{local_path}' (durante upload).")
            return False
        except botocore.exceptions.NoCredentialsError:
            print("Erro: Credenciais AWS não encontradas.")
            print("Configure suas credenciais via variáveis de ambiente, ~/.aws/credentials, ou role do IAM.")
            return False
        except botocore.exceptions.PartialCredentialsError:
            print("Erro: Credenciais AWS incompletas.")
            return False
        except botocore.exceptions.ClientError as e:
            # Erros específicos do serviço AWS (S3 neste caso)
            error_code = e.response.get("Error", {}).get("Code")
            error_message = e.response.get("Error", {}).get("Message")
            if error_code == 'NoSuchBucket':
                print(f"Erro: O bucket '{self.base_path}' não existe.")
            elif error_code == 'AccessDenied':
                print(f"Erro: Acesso negado ao bucket '{self.base_path}' ou ao tentar criar o objeto '{object_name}'. Verifique as permissões do IAM.")
            else:
                print(f"Erro do Cliente S3 ao fazer upload: {error_code} - {error_message}")
            # Você pode querer inspecionar mais o objeto 'e' para detalhes
            # print(e.response)
            return False
        except Exception as e:
            # Captura outros erros inesperados
            print(f"Ocorreu um erro inesperado durante o upload: {e}")
            return False
        
    def list_path(self, path:str, prefix:str="", type:str="") -> list:
        """
        Lista todos os arquivos e subpastas (prefixos) dentro de uma path.

        Args:
            path (str): pasta para busca ''.
            prefix (str, optional): Um prefixo para filtrar os resultados. Defaults para ''.
            type (str, optional): tipo da procura (FILE/PATH). Defaults para ''.

        Returns:
            list : Lista todos os arquivos e subpastas (prefixos) dentro de uma path. 
        """

        files = []
        p = AiUtils.sanitize_file_path(((path + "/") if path is not None and path != "" else "") + prefix)
        print(f"p: {p}")
        try:
            paginator = self.aws_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.base_path, Prefix=p, Delimiter="/")

            for page in pages:
                if type != "PATH" and 'Contents' in page:
                    for obj in page['Contents']:
                        files.append({'name': obj['Key'], 'type': "FILE"})
                if type != "FILE" and 'CommonPrefixes' in page:
                    for prefix_data in page['CommonPrefixes']:
                        files.append({'name': prefix_data['Prefix'].rstrip('/'), "type": "PATH"})
            return files

        except botocore.exceptions.NoCredentialsError:
            print("Erro: Credenciais AWS não encontradas.")
            print("Configure suas credenciais via variáveis de ambiente, ~/.aws/credentials, ou role do IAM.")
            return None
        except botocore.exceptions.PartialCredentialsError:
            print("Erro: Credenciais AWS incompletas.")
            return None
        except botocore.exceptions.ClientError as e:
            # Erros específicos do serviço AWS (S3 neste caso)
            error_code = e.response.get("Error", {}).get("Code")
            error_message = e.response.get("Error", {}).get("Message")
            if error_code == 'NoSuchBucket':
                print(f"Erro: O bucket '{self.base_path}' não existe.")
            elif error_code == 'AccessDenied':
                print(f"Erro: Acesso negado ao bucket '{self.base_path}' ou ao tentar criar o objeto '{object_name}'. Verifique as permissões do IAM.")
            else:
                print(f"Erro ao acessar o bucket: {error_code} - {error_message}")
            # Você pode querer inspecionar mais o objeto 'e' para detalhes
            # print(e.response)
            return None
        except Exception as e:
            # Captura outros erros inesperados
            print(f"Ocorreu um erro inesperado durante a execução do v: {e}")
            return None


    def download_file(self, file_path:str, file_name:str):
        """
        Download file para um arquivo temporário

        Args:
            file_path (str): O caminho para o arquivo a ser criado/modificado.
            file_name (str): O nome do arquivo a ser criado/modificado.

        Returns:
            str: Caminho do arquivo temporário que foi feito download do S3
        """
        object_name = AiUtils.sanitize_file_path(((file_path + "/") if (file_path is not None and file_path != "") else "") + file_name)
        try:
            base_p, ext = os.path.splitext(file_name)

            # Cria um arquivo temporário
            with NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                temp_file_path = temp_file.name

            self.aws_client.download_file(self.base_path, object_name, temp_file_path)
            return temp_file_path

        except botocore.exceptions.NoCredentialsError:
            print("Erro: Credenciais AWS não encontradas.")
            print("Configure suas credenciais via variáveis de ambiente, ~/.aws/credentials, ou role do IAM.")
            return None
        except botocore.exceptions.PartialCredentialsError:
            print("Erro: Credenciais AWS incompletas.")
            return None
        except botocore.exceptions.ClientError as e:
            # Erros específicos do serviço AWS (S3 neste caso)
            error_code = e.response.get("Error", {}).get("Code")
            error_message = e.response.get("Error", {}).get("Message")
            if error_code == 'NoSuchBucket':
                print(f"Erro: O bucket '{self.base_path}' não existe.")
            elif error_code == 'AccessDenied':
                print(f"Erro: Acesso negado ao bucket '{self.base_path}' ou ao tentar criar o objeto '{object_name}'. Verifique as permissões do IAM.")
            else:
                print(f"Erro ao acessar o bucket: {error_code} - {error_message}")
            # Você pode querer inspecionar mais o objeto 'e' para detalhes
            # print(e.response)
            return None
        except Exception as e:
            # Captura outros erros inesperados
            print(f"Ocorreu um erro inesperado durante o download: {e}")
            return None

    def download_fileobj(self, file_path:str, file_name:str, encoding:str="utf-8"):
        """
        Download file para um arquivo para text

        Args:
            file_path (str): O caminho para o arquivo a ser criado/modificado.
            file_name (str): O nome do arquivo a ser criado/modificado.
            encoding (str, optional): Codificação do arquivo. Defaults to "utf-8")
        Returns:
            str: Conteúdo dó arquivo foi feito download do S3
        """
        object_name = AiUtils.sanitize_file_path(((file_path + "/") if file_path is not None and file_path != "" else "") + file_name)
       
        try:
            in_memory_file = io.BytesIO()
            
            self.aws_client.download_fileobj(Bucket=self.base_path, Key=object_name, Fileobj=in_memory_file)
            in_memory_file.seek(0)
            file_in_byte = in_memory_file.read()
            text = file_in_byte.decode(encoding)

            return text

        except botocore.exceptions.NoCredentialsError:
            print("Erro: Credenciais AWS não encontradas.")
            print("Configure suas credenciais via variáveis de ambiente, ~/.aws/credentials, ou role do IAM.")
            return None
        except botocore.exceptions.PartialCredentialsError:
            print("Erro: Credenciais AWS incompletas.")
            return None
        except botocore.exceptions.ClientError as e:
            # Erros específicos do serviço AWS (S3 neste caso)
            error_code = e.response.get("Error", {}).get("Code")
            error_message = e.response.get("Error", {}).get("Message")
            if error_code == 'NoSuchBucket':
                print(f"Erro: O bucket '{self.base_path}' não existe.")
            elif error_code == 'AccessDenied':
                print(f"Erro: Acesso negado ao bucket '{self.base_path}' ou ao tentar criar o objeto '{object_name}'. Verifique as permissões do IAM.")
            else:
                print(f"Erro ao acessar o bucket: {error_code} - {error_message}: {self.base_path}/{object_name}")
            # Você pode querer inspecionar mais o objeto 'e' para detalhes
            # print(e.response)
            return None

        except UnicodeDecodeError:
            print(f"Erro: Não foi possível decodificar o arquivo usando a codificação '{encoding}'.")
            return None

        except Exception as e:
            # Captura outros erros inesperados
            print(f"Ocorreu um erro inesperado durante o download: {e}")
            return None
       