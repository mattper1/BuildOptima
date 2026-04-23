from typing import Any, Literal
from pydantic import BaseModel, field_validator


class OptimizeRequest(BaseModel):
    budget: int
    use_case: Literal["gaming", "content_creation", "workstation", "general"]
    future_proofing: bool = False
    owns_gpu: bool = False
    prefer_quiet_cooling: bool = False

    @field_validator("budget")
    @classmethod
    def budget_in_range(cls, v: int) -> int:
        if not 300 <= v <= 5000:
            raise ValueError("Budget must be between 300 and 5000")
        return v


class ComponentResult(BaseModel):
    category: str
    name: str
    brand: str
    price: float
    reason: str
    specs: dict[str, Any]


class OptimizeResponse(BaseModel):
    use_case: str
    budget: int
    total_price: float
    components: list[ComponentResult]
