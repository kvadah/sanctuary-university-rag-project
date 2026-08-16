from pydantic import BaseModel


class PaginationMeta(BaseModel):
    """Pagination envelope metadata for collection endpoints (see API spec §13)."""
    page: int
    page_size: int
    total_items: int
    total_pages: int
