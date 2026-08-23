from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    code: str
    message: str


class APIResponse(BaseModel, Generic[DataT]):
    success: bool
    data: Optional[DataT] = None
    error: Optional[ErrorDetail] = None
    request_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
