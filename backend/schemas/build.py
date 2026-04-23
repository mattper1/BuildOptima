from datetime import datetime
from pydantic import BaseModel


class ComponentIn(BaseModel):
    category: str
    part_name: str
    part_price: float
    reason_selected: str


class BuildSaveRequest(BaseModel):
    build_name: str
    use_case: str
    budget: int
    total_price: float
    components: list[ComponentIn]


class ComponentOut(BaseModel):
    id: int
    component_category: str
    part_name: str
    part_price: float
    reason_selected: str

    model_config = {"from_attributes": True}


class BuildOut(BaseModel):
    id: int
    build_name: str
    use_case: str
    budget: int
    total_price: float
    created_at: datetime

    model_config = {"from_attributes": True}


class BuildDetailOut(BuildOut):
    components: list[ComponentOut]
