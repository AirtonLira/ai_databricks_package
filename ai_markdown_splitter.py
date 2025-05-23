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
from langchain_text_splitters import MarkdownTextSplitter
from langchain_text_splitters.base import TextSplitter

from .ai_splitter_utils import AiSplitterUtils
from .ai_base_text_splitter import AiBaseTextSplitter

class AiMarkdownSplitter(AiBaseTextSplitter):

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

    #Override
    def _create_splitter(self,
                        chunk_size: int,
                        chunk_overlap: int,
                        length_function: Callable[[str], int],
                        keep_separator: Union[bool, Literal["start", "end"]],
                        strip_whitespace: bool,
                        separators: Optional[List[str]],
                        is_separator_regex: bool
                    ) -> TextSplitter:
        return MarkdownTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap, 
            length_function=length_function,
            keep_separator=keep_separator,
            add_start_index=True,
            strip_whitespace=strip_whitespace,
            is_separator_regex=is_separator_regex
        )
    
    def _segment_in_block(self, document_list:list, regex:str):
        new_list = []
        r = regex + "[^#]"
        for document in document_list:
            text = document.page_content

            text_split = re.split("\n\n" + r, text);
            i = 0
            for t in text_split:
                t = (regex if not t.startswith("#") and (i > 0 or t[:1] != text[:1]) else "") + t.strip()
                metadata = copy.deepcopy(document.metadata)
                if re.match("^" + r, t):
                    field_label = "title"
                    if regex == "##":
                        field_label = "subtitle"
                    elif regex == "###":
                        field_label = "section"
                    
                    metadata[field_label] =  AiSplitterUtils.trim_text(t.split("\n")[0].replace("#", ""), " ")
                
                new_list.append(self._initialize_document(
                    content=t,
                    metadata=metadata
                ))

        return new_list

    #Override
    def _segment_text(self, text:str, metadata:Optional[dict], format:bool) -> List[Document]:

        text = text.strip()
        text = AiSplitterUtils.replace_all_text(text, "\n\n\n", "\n\n")
        text = AiSplitterUtils.replace_all_text(text, "\n ", "\n")
        text = AiSplitterUtils.replace_all_text(text, "\r", "")

        document = self._initialize_document(
            content=text,
            metadata=metadata
        )

        document_list = self._segment_in_block([document], "#")
        document_list = self._segment_in_block(document_list, "##")
        document_list = self._segment_in_block(document_list, "###")

        return document_list

    #Override
    def _format_document(self, document: Document, page:int, position:int) -> Document:
        document = super()._format_document(document, page, position)
        document.page_content=AiSplitterUtils.sanitize_markdow(document.page_content)
        document.content_to_embed=AiSplitterUtils.sanitize_markdow(document.content_to_embed)
        return document