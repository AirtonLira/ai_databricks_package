from typing import Any, Literal

from langchain_core.documents import Document


class SplitDocument(Document):
    content_to_embed: str
    """String text."""
    type: Literal["SplitDocument"] = "SplitDocument"

    def __init__(self, page_content: str, content_to_embed: str = None, **kwargs: Any) -> None:
        super().__init__(page_content=page_content, content_to_embed=content_to_embed, **kwargs)
        self.content_to_embed = content_to_embed
