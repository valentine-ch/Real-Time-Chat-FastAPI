from pydantic import BaseModel


class Username(BaseModel):
    name: str
