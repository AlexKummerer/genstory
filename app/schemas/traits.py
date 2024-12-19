from pydantic import BaseModel


class Trait(BaseModel):
    name: str
    value: str

    class Config:
        schema_extra = {
            "example": {
                "name": "Bravery",
                "value": "High",
            }
        }
