import re
from datetime import datetime
from html import unescape

import unicodedata
from bs4 import BeautifulSoup


###################################
# CLASS AiUtils
# Author: Airton Lira Junior
# Date: 2025-05-23
################################### 

class AiUtils:
    @staticmethod
    def replace_all_text(text:str, old:str, new:str):
        while (old in text):
            text = text.replace(old, new)
        return text
    
    @staticmethod
    def get_argument(widgets, name:str, default_value:str="") -> str:
        widgets.text(name, default_value, name)
        value = widgets.get(name)
        if value == "":
            raise ValueError("Argumento '" + name + "' is required")
        else:
            print("Argumento '" + name + "' = " + value)
            return value
   
    @staticmethod
    def get_list_argument(widgets, name:str, default_value:str="") -> str:
        value = AiUtils.get_argument(widgets, name, default_value)
        value = AiUtils.replace_all_text(value, ", ", ",")
        value = AiUtils.replace_all_text(value, " ,", ",")
        return value.split(",")

        
    @staticmethod
    def handler_error(message:str) -> str:
        print(message)
        raise ValueError(message)
        

    @staticmethod
    def sanitize_file_path(path:str) -> str:
        """
        Sanitiza um caminho de arquivo, tornando-o mais consistente
        e removendo redundâncias comuns.

        Args:
            path (str): O caminho do arquivo a ser sanitizado.

        Returns:
            str: O caminho do arquivo sanitizado.
        """
        # Substitui todas as ocorrências de barra invertida (\),
        # que é o separador de caminho no Windows, por barra normal (/),
        # que é o separador de caminho na maioria dos outros sistemas
        # e geralmente é aceito pelo Python em ambos os sistemas.
        path = path.replace("\\","/")

        # Remove ocorrências de barras duplas (//) que podem surgir
        # por erros de digitação ou concatenação inadequada de caminhos.
        # O loop 'while' garante que todas as ocorrências sejam removidas,
        # mesmo que haja múltiplas barras duplas consecutivas.
        while "//" in path:
            path = path.replace("//","/")

        # Retorna o caminho do arquivo sanitizado.
        return path
    
    @staticmethod
    def change_value_path(url:str, key:str, value:str) -> str:
        """
        Troca a chave do path pelo valor passado.

        Args:
            url (str): url que será alterada.
            key (str): a chave que será procurrada para ser alterada
            value (str): valor que fará parte da url

        Returns:
            str: retorna a url com o valor alterado
        """
        return url.replace("#" + key + "#", value)
    
    @staticmethod
    def sanitize_url(url:str) -> str:
        """
        Sanitiza uma url, removendo os //.

        Args:
            url (str): A url a ser sanitizado.

        Returns:
            str:A url sanitizado.
        """
        TK = "://"
        uri = url.split(TK)

        while "//" in uri[1]:
            uri[1] = uri[1].replace("//","/")

        # Retorna o caminho do arquivo sanitizado.
        return uri[0] + TK + uri[1]
    
    @staticmethod
    def remove_accents(texto:str) -> str:
        """
        Remove caracteres acentuados de uma string.

        Args:
            texto (str): testo com caracteres acentuados.

        Returns:
            str: O caminho do arquivo sanitizado.
        """
        # Normaliza a string para separar os caracteres base dos seus sinais diacríticos
        nfkd_form = unicodedata.normalize('NFKD', texto)
        # Mantém apenas os caracteres que não são sinais diacríticos (categoria Mn - Mark, Nonspacing)
        only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('ASCII')
        return only_ascii

    @staticmethod
    def sanitize_text(value:str, allow_dot:bool=False, allow_space:bool=True, allow_upper_lower:bool=True, allow_parentheses:bool=True, allow_accents:bool=True, upper:bool=False) -> str:
        """
        Sanitiza uma string de texto, removendo ou substituindo caracteres
        que podem ser problemáticos em certos contextos, como nomes de arquivos.

        Args:
            value (str): A string de texto a ser sanitizada.
            allow_dot (bool): Se for False, os pontos serão removidos da Str (DEFAULT: False)
            allow_space (bool): Se for False, os espaços serão removidos da Str (DEFAULT: True)
            allow_upper_lower (bool): Se for False, os caracteres serão minusculos da Str (DEFAULT: True)
            allow_parentheses (bool): Se for False, os parenteses serão removidos da Str (DEFAULT: True)
            allow_accents (bool): Se for False, osacentos serão removidos da Str (DEFAULT: True)
            upper (bool): Se for true, todos os caracteres serão passados para maiusculo Str (DEFAULT: False)
            
        Returns:
            str: A string de texto sanitizada.
        """
        # Define caracteres considerados inválidos em muitos sistemas de arquivos.
        # Estes caracteres são: barra invertida, barra normal, dois pontos, asterisco,
        # interrogação, aspas duplas, sinal de menor que, sinal de maior que e pipe.
        invalid_char = '\\/:*?"<>|'

        if allow_dot == False:
            invalid_char += '.'

        if allow_space == False:
            invalid_char += ' '
        
        if allow_parentheses == False:
            invalid_char += '()'
        
        # substituir todas as ocorrências dos caracteres inválidos encontrados
        value = re.sub(r'[' + invalid_char + ']', '_', value)

        # Remove quaisquer espaços em branco (incluindo tabs, novas linhas, etc.)
        # que possam existir no início ou no final da string 'value'.
        value = value.strip()

        if allow_upper_lower == False:
            if upper == True:
                value = value.upper()
            else:
                value = value.lower()

        if allow_accents == False:
            value = AiUtils.remove_accents(value)

        while "__" in value:
            value = value.replace("__","_")

        if value.startswith('_'):
            value = value[1:]  # Remove o primeiro caractere

        if value.endswith('_'):
            value = value[:-1] # Remove o último caractere

        # Define um tamanho máximo para a string sanitizada. Nomes muito longos 
        # podem causar problemas em alguns sistemas operacionais.
        max_size = 255  # Um valor seguro

        # Verifica se o comprimento da string 'value' é maior que o tamanho máximo definido.
        if len(value) > max_size:
            # Se for maior, trunca a string 'value' para conter apenas os
            # primeiros 'max_size' caracteres.
            value = value[:max_size]


        # Retorna a string de texto sanitizada, após todas as substituições
        # e remoções terem sido aplicadas.
        return value
    
    @staticmethod
    def _format_table_line(title:str, content:str) -> str:
        """
        Formata a linha da tabela em texto.

        Args:
            title (str): título da tabela.
            content (str): conteúdo da tabela.

        Returns:
            str: retorna um texto formatado para ser adicionado ao conteúdo da página do confuence.
        """
        return  title + ": " + content + "\n"

    @staticmethod
    def sanitize_tag_html(html_content:str) -> str:
        """
        Sanitiza um texto com conteúdo html, removendo todas as suas tags.

        Args:
            html_content (str): A string de texto a ser sanitizada.
            
        Returns:
            str: A string de texto sanitizada.
        """

        html_content = unescape(html_content.replace('&nbsp;', ' '))

        beautifulSoup = BeautifulSoup(html_content, features="lxml")
        html_content = str(beautifulSoup)
        tables = beautifulSoup("table")

        for table in tables:
            table_txt = "\n"
            titles = None
            rowspan_values = {}  # Guarda os valores de rowspan e o conteúdo para as próximas linhas
            rows = table.find_all('tr')
            for row_index, row in enumerate(rows):
                if titles is None:
                    titles = row.find_all(['td', 'th'])
                else:
                    cells = row.find_all(['td', 'th'])
                    cell_index = 0
                    rowspan_cell_index = 0
                    if len(titles) == len(cells):
                        rowspan_values = {} 

                    while rowspan_cell_index + cell_index < len(titles):
                        title = titles[rowspan_cell_index + cell_index].get_text(strip=True)
                        content = None
                        if len(cells) > cell_index:
                            cell = cells[cell_index]
                            content = cell.get_text(strip=True)
                        if (len(titles) > len(cells) and rowspan_values):
                            rowspan_line = rowspan_values[row_index]

                            if rowspan_line:
                                rowspan_value = rowspan_line.get(rowspan_cell_index + cell_index)
                                if rowspan_value is not None:
                                    rowspan_cell_index += 1
                                    table_txt += AiUtils._format_table_line(title, rowspan_value)
                                    continue
                            
                        rowspan = int(cell.get('rowspan', 1))

                        table_txt += AiUtils._format_table_line(title, content)

                        # Guarda o valor para as próximas linhas se rowspan > 1
                        if rowspan > 1:
                            for i in range(row_index + 1, row_index + rowspan):
                                if i not in rowspan_values:
                                    rowspan_values[i] = {}
                                rowspan_values[i][cell_index] = content

                        cell_index += 1
                    table_txt += "\n"

            html_content = html_content.replace(str(table), table_txt)
        
        html_content = re.sub(r'<\/((h[0-9])|p)>', '\n', html_content)
        
        html_content = re.sub(r'<[^>]+>', '', html_content)

        return html_content

    @staticmethod
    def validate_config(config:dict, properties:list):
        """
        Valida todas as propriedades necessarias do congid para um componente

        Args:
            config (dict): Dicionário com as configurações do componente.
            properties (list): Lista de propriedades para serem validadas.
        """
        validate = True
        for property in properties:
            if property not in config or config[property] == "" or config[property] is None:
                print("Error validate config: property not found: " + property)
                validate = False

        if not validate:
            raise ValueError("Configurações inválidas. Verifique se todas as chaves necessárias estão presentes.")

    @staticmethod
    def current_date() -> str:
        """
        Retorna a data atual em formato de String

        Args:
        
        Returns:
            str: data atual em formato de str
        """
        return datetime.now().strftime("%Y-%m-%d")
    
    @staticmethod
    def define_extraction_path(category:str="", extraction_date="", sub_category:str=""):
        """
        Define o path de extração dos dados

        Args:
            category (str): nome que servirá de caminho inicial da path (prefix)
            sub_category (str): nome que servirá de caminho final da path (sulfix)
        
        Returns:
            str: path de extração
        """

        if not extraction_date:
            extraction_date = AiUtils.current_date()

        return ((category + "/") if (category is not None and category != "") else "") + "extraction_date=" + extraction_date + (("/"  + sub_category) if (sub_category is not None and sub_category != "") else "")

