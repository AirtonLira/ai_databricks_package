import copy
from typing import (
    List,
    Callable,
    Literal,
    Union,
    Optional
)

from langchain_core.documents import Document

from .ai_base_text_splitter import AiBaseTextSplitter


class AiJsonSplitter(AiBaseTextSplitter):

    def __init__(self,
        context_size:int = 0,
    ) -> None:
        
        super().__init__(0,
            context_size=context_size
        )

    #Override
    def _segment_text(self, text:str, metadata:Optional[dict], format:bool) -> List[Document]:
        metadata = copy.deepcopy(metadata)
        metadata["title"] = "json"

        document = self._initialize_document(
            content=text,
            metadata=metadata
        )

        return [document]