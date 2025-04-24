from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class CreateSpimexTrading(BaseModel):
    id: int
    exchange_product_id: str = Field(max_length=11)
    exchange_product_name: str
    oil_id: str = Field(max_length=4)
    delivery_basis_id: str = Field(max_length=3)
    delivery_basis_name: str
    delivery_type_id: str = Field(max_length=1)
    volume: int
    total: int
    count: int
    date: datetime
    created_on: datetime = Field(default_factory=datetime.now)
    updated_on: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
