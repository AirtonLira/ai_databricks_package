import copy
import re
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


class AiTextSplitter(AiBaseTextSplitter):

    def __init__(self,
        context_size:int = 0,
        chunk_size: int = 1000,
        chunk_overlap: int = 0,
        length_function: Callable[[str], int] = len,
        keep_separator: Union[bool, Literal["start", "end"]] = False,
        strip_whitespace: bool = True,
        separators: Optional[List[str]] = None,
        is_separator_regex: bool = False,
    ) -> None:
        
        super().__init__(context_size,
                    chunk_size, 
                    chunk_overlap, 
                    length_function, 
                    keep_separator,
                    strip_whitespace,
                    separators,
                    is_separator_regex
                    )

    def _create_document(self, title:str, text:str, metadata:dict) -> Document:
        metadata = copy.deepcopy(metadata)
        if title:
            metadata["title"] = AiSplitterUtils.replace_all_text(title, "\n", "")
        
        return self._initialize_document(
            content=AiSplitterUtils.sanitize_text(text), 
            metadata=metadata
        )

    #Override
    def _segment_text(self, text:str, metadata:Optional[dict], format:bool) -> List[Document]:

        text = AiSplitterUtils.trim_text(text, " ")
        text = AiSplitterUtils.replace_all_text(text, "\n\n\n", "\n\n")
        text = AiSplitterUtils.replace_all_text(text, "\n ", "\n")

        document = self._initialize_document(
            content=text,
            metadata=metadata
        )

        document_list = self._segment_text_in_block([document])

        return document_list

    #Override
    def _format_document(self, document: Document, page:int, position:int) -> Document:
        document = super()._format_document(document, page, position)
        document.page_content=AiSplitterUtils.sanitize_text(document.page_content)
        return document
    
    def _segment_text_in_block(self, document_list:list) -> list:
        new_list = []
        # r = regex + "[^#]"
        for document in document_list:
            text = document.page_content

            text_split = re.split("(\n\n[^(```|#)].{,50}[^.]\n)", text)
            i = 0
            title = None
            for t in text_split:
                if i == 0:
                    ts = re.split("(^.{,50}\n)", t)
                    title_0 = None
                    line = ts[len(ts) - 1]
                    if len(ts) == 3:
                        title_0 = ts[1]     
                    if title_0 is not None:
                        line = title_0 + "\n\n" + line
                    new_list.append(self._create_document(title_0, line, document.metadata))
                else:
                    if title is None:
                        title = t
                    else:
                        new_list.append(self._create_document(title, title + "\n\n" + t, document.metadata))
                        title = None


                i += 1
        return new_list