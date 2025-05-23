import os
import shutil
import zipfile

from .ai_utils import AiUtils


###################################
# CLASS AiFileUtils
# Author: Airton Lira Junior
# Date: 2025-05-23
################################### 

class AiFileUtils:

    @staticmethod
    def extract_zip(zip_path:str, extract_path:str):
        """
        Extrai todo o conteúdo de um arquivo ZIP para um diretório específico.

        Args:
            zip_path (str): O caminho completo para o arquivo .zip que será 
                            descompactado.
            extract_path (str): O caminho do diretório onde os arquivos
                                extraídos serão salvos. Se o diretório não
                                existir, ele será criado.

        """
    
        # Diretório onde você quer extrair os arquivos
        # Se não existir, vamos criá-lo
        if not os.path.exists(extract_path):
            os.makedirs(extract_path)

        try:
            # Abre o arquivo ZIP em modo de leitura ('r')
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extrai todo o conteúdo para a pasta de destino
                zip_ref.extractall(extract_path)
            print(f"Arquivos extraídos com sucesso para '{extract_path}'")

        except FileNotFoundError:
            print(f"Erro: O arquivo '{zip_path}' não foi encontrado.")
        except zipfile.BadZipFile:
            print(f"Erro: O arquivo '{zip_path}' não é um arquivo ZIP válido ou está corrompido.")
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")        

    @staticmethod
    def delete_path(path:str, delete_root_folder:bool=False) -> bool:
        """
        Deleta um arquivo ou diretório com todo seu conteúdo de forma recursiva.

        Args:
            path (str): O caminho completo para o diretório a ser
                                     deletado com todo o seu conteúdo.

        Returns:
            bool: Retorna True se foi deletado com sucesso, False caso 
                contrário (diretório não encontrado.

        """
        print(f"Tentando deletar o caminho: '{path}'")

        try:
            # 1. Validação: Verificar se o caminho existe e é um diretório
            if not os.path.exists(path):
                print(f"Erro: O caminho '{path}' não foi encontrado.")
                return False # Diretório não existe

            if os.path.isfile(path):
                os.remove(path)
                print(f"Sucesso: Arquivo '{path}' deletado.")
                return True # Sucesso na exclusão
            elif os.path.isdir(path):
                if delete_root_folder:
                    shutil.rmtree(path)
                    print(f"Sucesso: Diretório '{path}' e seu conteúdo foram deletados.")
                    return True # Sucesso na exclusão
                else:
                    success = True # Flag para rastrear se ocorreu algum erro

                    # 2. Iterar sobre o conteúdo e remover
                    # os.listdir() retorna apenas os nomes, precisamos juntar com o caminho base
                    try:
                        for item_name in os.listdir(path):
                            item_path = os.path.join(path, item_name)
                            try:
                                if os.path.isfile(item_path) or os.path.islink(item_path):
                                    os.remove(item_path)
                                elif os.path.isdir(item_path):
                                    shutil.rmtree(item_path)
                                else:
                                    print(f"  -> Aviso: Item '{item_name}' de tipo desconhecido, não removido.")
                                    success = False # Considera falha parcial se encontrar algo inesperado
                            except PermissionError:
                                print(f"  -> Erro de Permissão ao remover '{item_name}'.")
                                success = False # Marca falha se qualquer item falhar
                            except OSError as e:
                                print(f"  -> Erro de SO ao remover '{item_name}': {e}")
                                success = False # Marca falha
                            except Exception as e:
                                print(f"  -> Erro Inesperado ao remover '{item_name}': {e}")
                                sucessosuccess_geral = False # Marca falha

                    except Exception as e:
                        # Erro ao listar o diretório, por exemplo
                        print(f"Erro ao acessar o conteúdo de '{path}': {e}")
                        return False # Falha crítica ao acessar o diretório

                    return success


                    
            else:
                print(f"Falha: Erro ao tentar deletar o caminho '{path}'.")
                return False # Não é um diretório

        # 3. Tratamento de Erros Específicos
        except PermissionError:
            print(f"Erro de Permissão: Não foi possível deletar '{path}' ou seu conteúdo.")
            print("   -> Verifique as permissões ou se algum arquivo/subdiretório está em uso.")
            return False # Falha devido à permissão

        except NotADirectoryError: # Embora já verificado, é bom capturar explicitamente
             print(f"Erro: O caminho '{path}' não é um diretório (Erro interno?).")
             return False

        except OSError as e:
            # Pode ocorrer se um arquivo dentro do diretório estiver em uso, etc.
            print(f"Erro do Sistema Operacional ao deletar '{path}': {e}")
            return False # Falha devido a erro do SO

        except Exception as e:
            # Captura qualquer outro erro inesperado
            print(f"Erro Inesperado ao deletar '{path}': {e}")
            return False # Falha inesperada

    @staticmethod
    def get_all_file(path:str) -> list:
        """
        Lista todos os arquivos em um diretório e seus subdiretórios.

        Args:
            path (str): O caminho para o diretório inicial.

        Returns:
            list: Uma lista contendo os caminhos completos para cada arquivo encontrado.
                Retorna uma lista vazia se o diretório não existir ou não for um diretório.
        """
        files = []
        # Verifica se o caminho existe e é um diretório
        if not os.path.isdir(path):
            files.append(path)
            return files

        # os.walk() gera tuplas (diretorio_atual, subdiretorios, arquivos)
        for actual_path, sub_path, file_list in os.walk(path):
            for file_name in file_list:
                # Monta o caminho completo do arquivo
                full_path = os.path.join(actual_path, file_name)
                files.append(AiUtils.sanitize_file_path(full_path))

        return files