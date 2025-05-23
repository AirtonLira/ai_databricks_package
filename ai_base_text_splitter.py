import copy
from typing import (
    Iterable,
    List,
    Callable,
    Literal,
    Union,
    Optional
)

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters.base import TextSplitter

from .split_document import SplitDocument




class AiBaseTextSplitter():

    def __init__(self,
                 context_size: int = 0,
                 chunk_size: int = 0,
                 chunk_overlap: int = 0,
                 length_function: Callable[[str], int] = len,
                 keep_separator: Union[bool, Literal["start", "end"]] = False,
                 strip_whitespace: bool = True,
                 separators: Optional[List[str]] = None,
                 is_separator_regex: bool = False

                 ) -> None:
        self._context_size = context_size
        self._chunk_size = chunk_size
        self._context_min_size = 100
        if self._chunk_size > 0:
            self._splitter = self._create_splitter(chunk_size,
                                                   chunk_overlap,
                                                   length_function,
                                                   keep_separator,
                                                   strip_whitespace,
                                                   separators,
                                                   is_separator_regex
                                                   )
        else:
            self._splitter = None

    def _initialize_document(self, content: str, metadata: dict, original_content: str = None) -> Document:
        if (original_content is not None):
            metadata["original_content"] = original_content
        else:
            metadata["original_content"] = content

        document = Document(
            page_content=content,
            metadata=metadata
        )

        return document

    def _create_splitter(self,
                         chunk_size: int,
                         chunk_overlap: int,
                         length_function: Callable[[str], int],
                         keep_separator: Union[bool, Literal["start", "end"]],
                         strip_whitespace: bool,
                         separators: Optional[List[str]],
                         is_separator_regex: bool
                         ) -> TextSplitter:
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=length_function,
            keep_separator=keep_separator,
            add_start_index=True,
            strip_whitespace=strip_whitespace,
            separators=separators,
            is_separator_regex=is_separator_regex
        )

    # TO override
    def _segment_text(self, text: str, metadata: Optional[dict], format: bool) -> List[Document]:
        return []

    def _format_documents(self, documents: Iterable[Document]) -> List[Document]:
        position = 1
        page = 0
        new_list = []
        for doc in documents:
            document = doc
            original_content = document.metadata.get("original_content")
            if original_content:
                del document.metadata['original_content']
                document = SplitDocument(
                    page_content=original_content,
                    content_to_embed=document.page_content,
                    metadata=document.metadata
                )
            if not document.metadata.get("start_index") or document.metadata["start_index"] == 0:
                position = 1
                page += 1

            new_list.append(self._format_document(document, page, position))

            position += 1

        return new_list

    def _format_document(self, document: Document, page: int, position: int) -> Document:
        document.metadata["page"] = page
        document.metadata["position"] = position
        return document

    def _split_context(self, documents: Iterable[Document]):
        textSplitter = RecursiveCharacterTextSplitter(
            chunk_size=self._context_size,
            chunk_overlap=0
        )
        new_list = []

        for doc in documents:
            split_documents = textSplitter.split_text(doc.page_content)

            savedText = ""
            for d in split_documents:
                if len(d) < self._context_min_size:
                    savedText += d + " "
                    if len(savedText) < self._context_size:
                        continue

                metadata = copy.deepcopy(doc.metadata)

                new_list.append(self._initialize_document(content=savedText + d, metadata=metadata))
                savedText = ""

            if savedText != "":
                metadata = copy.deepcopy(doc.metadata)
                new_list.append(self._initialize_document(content=savedText, metadata=metadata))

        return new_list

    def create_documents(
            self, content: str, metadata: Optional[dict] = None, format: bool = False
    ) -> List[Document]:

        if metadata is None:
            metadata = {}

        md = copy.deepcopy(metadata)

        documents = self._segment_text(content, md, format)

        if self._context_size > 0:
            documents = self._split_context(documents)

        if self._splitter is not None:
            documents = self._splitter.split_documents(documents)

        documents = self._format_documents(documents)

        return documents

    def split_documents(self, documents: Iterable[Document], format: bool = False) -> List[Document]:

        new_documents = []
        for document in documents:
            new_documents.extend(self.create_documents(document.page_content, document.metadata, format))
        return new_documents
