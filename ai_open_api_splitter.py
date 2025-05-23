import copy
import json
from typing import (
    List,
    Callable,
    Literal,
    Union,
    Optional
)

from langchain_core.documents import Document

from .ai_base_text_splitter import AiBaseTextSplitter
from .ai_splitter_utils import AiSplitterUtils

class AiOpenApiSplitter(AiBaseTextSplitter):

    def __init__(self) -> None:
        super().__init__()

    def _segment_text(self, text:str, metadata:Optional[dict], format:bool):
        """
        Segmenta um dicionário Python carregado de um JSON OpenAPI em Documentos LangChain.
        """
        openapi_data = json.loads(text)
        openapi_data = AiSplitterUtils.remove_ref_openapi_spec(openapi_data)


        documents = []
        indent = 2 if format else None

        # 1. Informações Gerais da API (Info)
        info_title = ""
        info_description = ""
        if 'info' in openapi_data:
            info_title = openapi_data['info'].get('title', '')
            info_description = openapi_data['info'].get('description', '')
        
        base_spec = {}
        
        AiSplitterUtils.copy_property(openapi_data, base_spec, 'openapi')
        AiSplitterUtils.copy_property(openapi_data, base_spec, 'servers')
        AiSplitterUtils.copy_property(openapi_data, base_spec, 'components.securitySchemes')
        AiSplitterUtils.copy_property(openapi_data, base_spec, 'security')
 
        # Endpoints (Paths)
        if 'paths' in openapi_data:
            for path, path_item in openapi_data['paths'].items():
                for method, operation in path_item.items():
                    # Ignora entradas não padrão como 'parameters' no nível do path_item aqui
                    if method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                        continue
                    
                    spec = copy.deepcopy(base_spec)
                    spec["paths"] = {}
                    spec["paths"][path] = {}

                    if "parameters" in path_item:
                        spec["paths"][path]["parameters"] = path_item["parameters"]

                    spec["paths"][path][method] = operation

                    md = copy.deepcopy(metadata)
                    md["subtitle"] = "endpoint"
                    md["section"] = method.upper() + " " + path 



                    method_summary = operation.get('summary', '')
                    method_description = operation.get('description', '')

   
                    content_to_embed = f"Exemplo de uma chamada '{method}' ao endpoint '{path}' na api '{info_title}'. Esse script '{method_summary}' tem a função de '{method_description}'. "
                    content_to_embed += f"E essa api tem a responsabilidade de '{info_description}'"
                    content_to_embed = AiSplitterUtils.replace_all_text(content_to_embed, "\n", "")

                    documents.append(self._initialize_document(content=content_to_embed, metadata=md, original_content=json.dumps(spec, indent=indent, ensure_ascii=False)))
        return documents
