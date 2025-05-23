from strip_markdown import strip_markdown
import re
import copy, json
from urllib.parse import unquote

class AiSplitterUtils:
    @staticmethod
    def trim_text(text:str, str:str):
        while (text.startswith(str)):
            text = text[len(str):]
        while (text.endswith(str)):
            text = text[:-len(str)]
        return text

    @staticmethod
    def replace_all_text(text:str, old:str, new:str):
        while (old in text):
            text = text.replace(old, new)
        return text
    
    @staticmethod    
    def sanitize_text(text):
        text = AiSplitterUtils.trim_text(text, " ")
        text = AiSplitterUtils.trim_text(text, "\n")
        text = AiSplitterUtils.replace_all_text(text, "^\n", "")
        text = AiSplitterUtils.replace_all_text(text, "\n", ". ")
        text = AiSplitterUtils.replace_all_text(text, " .", ".")
        text = AiSplitterUtils.replace_all_text(text, "..", ".")
        return text

    @staticmethod
    def get_block_content(match_obj, type):
        text = match_obj.group(0) 
        text = re.sub(r'\[block:' + type + r'\]', "", text)
        text = re.sub(r'\[/block\]', "", text)
        text = re.sub(r'\\`', "", text)
        text = re.sub(r'\\"', "", text)
        text = re.sub(r'\\n', "", text)
        text = re.sub(r'\\', "", text)
        json_obj = json.loads(text)
        return json_obj

    @staticmethod
    def sanatize_image_block(match_obj):
        images = AiSplitterUtils.get_block_content(match_obj, "image")["images"]
        result = ""
        for image in images:
            data = image["image"]
            for link in data:
                if link and link.startswith("http"):
                    if len(result) > 0:
                        result += ""
                    result += link

        return result


    @staticmethod
    def sanatize_html_block(match_obj):
        return ""

    @staticmethod
    def sanatize_parameters_block(match_obj):
        content = AiSplitterUtils.get_block_content(match_obj, "parameters")
        data = content["data"]
        result = json.dumps(data)
        return result
    
    @staticmethod
    def sanatize_block(text):
        text = re.sub(r'\[block:(image)\].*?\[/block\]', AiSplitterUtils.sanatize_image_block, text, flags=re.DOTALL)
        text = re.sub(r'\[block:(embed)\].*?\[/block\]', AiSplitterUtils.sanatize_embed_block, text, flags=re.DOTALL)
        text = re.sub(r'\[block:(html)\].*?\[/block\]', AiSplitterUtils.sanatize_html_block, text, flags=re.DOTALL)
        text = re.sub(r'\[block:(parameters)\].*?\[/block\]', AiSplitterUtils.sanatize_parameters_block, text, flags=re.DOTALL)
        return text


    @staticmethod
    def sanitize_markdow(text):
        text = strip_markdown(text)
        text = AiSplitterUtils.sanatize_block(text)
        return AiSplitterUtils.sanitize_text(text)


    @staticmethod
    def _resolve_json_pointer(pointer, document):
        """Resolve um JSON Pointer (RFC 6901) dentro de um documento."""
        if not pointer.startswith('#/'):
            # Este código lida apenas com referências internas locais.
            # Poderia ser estendido para lidar com URIs externos se necessário.
            raise ValueError(f"Referência externa ou inválida não suportada: {pointer}")

        parts = pointer[2:].split('/')
        current = document
        try:
            for part in parts:
                # Decodifica sequências de escape ~1 para / e ~0 para ~
                part = unquote(part.replace('~1', '/').replace('~0', '~'))
                if isinstance(current, list):
                    current = current[int(part)]
                elif isinstance(current, dict):
                    current = current[part]
                else:
                    raise LookupError(f"Parte do ponteiro '{part}' não pode ser resolvida em um tipo não indexável: {type(current)}")
            return current
        except (KeyError, IndexError, ValueError) as e:
            raise LookupError(f"Erro ao resolver o ponteiro '{pointer}': {e}") from e

    @staticmethod
    def _remove_ref_recursive(item, root_document, resolving_stack=None):
        """
        Percorre recursivamente o item (dict, list, etc.) e resolve as referências $ref.
        Usa resolving_stack para detectar e evitar referências circulares.
        """
        if resolving_stack is None:
            resolving_stack = set()

        if isinstance(item, dict):
            if '$ref' in item:
                ref_pointer = item['$ref']
                if not isinstance(ref_pointer, str) or not ref_pointer.startswith('#/'):
                    # Ignora refs que não sejam strings ou não sejam internos
                    # Você pode querer adicionar tratamento de erro ou log aqui
                    return item # Retorna o dicionário original com o $ref não resolvido

                if ref_pointer in resolving_stack:
                    # Detectado ciclo! Não expanda mais, retorne o $ref original.
                    # Isso evita recursão infinita.
                    # print(f"Ciclo detectado para: {ref_pointer}. Mantendo $ref.")
                    return copy.deepcopy(item) # Retorna uma cópia para evitar modificar o original

                # Adiciona o ponteiro atual à pilha de resolução
                resolving_stack.add(ref_pointer)

                try:
                    # Encontra o objeto referenciado
                    resolved_target = AiSplitterUtils._resolve_json_pointer(ref_pointer, root_document)
                    # É CRUCIAL fazer uma cópia profunda ANTES de desreferenciar recursivamente
                    # para evitar modificar a definição original e lidar com refs compartilhadas
                    resolved_copy = copy.deepcopy(resolved_target)
                    # Desreferencia recursivamente o conteúdo do objeto copiado
                    result = AiSplitterUtils._remove_ref_recursive(resolved_copy, root_document, resolving_stack)
                except LookupError as e:
                    print(f"Aviso: Não foi possível resolver a referência: {e}. Mantendo $ref.")
                    result = copy.deepcopy(item) # Retorna o ref original se não puder ser resolvido
                except Exception as e:
                    print(f"Erro inesperado ao resolver {ref_pointer}: {e}. Mantendo $ref.")
                    result = copy.deepcopy(item) # Segurança

                # Remove o ponteiro da pilha ao retornar
                resolving_stack.remove(ref_pointer)
                return result
            else:
                # Se não for um $ref, processa os filhos recursivamente
                new_dict = {}
                for key, value in item.items():
                    new_dict[key] = AiSplitterUtils._remove_ref_recursive(value, root_document, resolving_stack)
                return new_dict

        elif isinstance(item, list):
            # Processa listas recursivamente
            new_list = []
            for element in item:
                new_list.append(AiSplitterUtils._remove_ref_recursive(element, root_document, resolving_stack))
            return new_list

        else:
            # Tipos primitivos (string, int, bool, null) são retornados como estão
            return item
    
    @staticmethod
    def remove_ref_openapi_spec(openapi_spec):
        """
        Função principal para desreferenciar um especificador OpenAPI carregado como um dict.
        Retorna uma *nova* especificação com todas as referências internas resolvidas.
        """
        if not isinstance(openapi_spec, dict):
            raise TypeError("A especificação OpenAPI de entrada deve ser um dicionário.")

        # Faz uma cópia profunda para não modificar o objeto original
        spec_copy = copy.deepcopy(openapi_spec)

        # Inicia o processo recursivo na cópia, usando a cópia também como documento raiz
        # para garantir que as resoluções ocorram dentro do contexto desreferenciado.
        # Passar spec_copy como root_document é importante se você quiser
        # que referências resolvidas possam ser usadas por outras referências.
        # Se você sempre quiser resolver a partir do original *não modificado*, passe openapi_spec aqui.
        # Geralmente, passar spec_copy é o comportamento desejado.
        spec = AiSplitterUtils._remove_ref_recursive(spec_copy, spec_copy)

        return spec

    @staticmethod
    def copy_property(src, target, property):
        prop_list = property.split(".")
        if len(prop_list) > 1:
            p = prop_list[0]
            if p in src:
                if p not in target:
                    target[p] = {}    
                prop_list.pop(0)
                AiSplitterUtils.copy_property(src[p], target[p], ".".join(prop_list))
        else:
            if property in src:
                value = copy.deepcopy(src[property])
                target[property] = value
