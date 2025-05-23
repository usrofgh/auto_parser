from pydantic import BaseModel

from src.parsers.ria.model import LinkType, ParseStatus


class RiaErrorSchema(BaseModel):
    url: str
    status: ParseStatus
    link_type: LinkType
    error_message: str | None = None
    count_retries: int | None = None
