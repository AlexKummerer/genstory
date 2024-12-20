from pydantic import BaseModel


class Trait(BaseModel):
    trait_title: str
    trait_value: str

    class Config:
        schema_extra = {
            "example": {
                "trait_title": "Bravery",
                "trait_value": "High",
            }
        }
