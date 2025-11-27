# app/schemas/shared.py

from pydantic import BaseModel


class SuccessResponse(BaseModel):
    message: str
