from datetime import datetime
from pydantic import BaseModel


class SignedToken(BaseModel):
    token: str
    expires_at: datetime
