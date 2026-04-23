from sqlalchemy import String, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column
from db.database import Base


class Part(Base):
    __tablename__ = "parts"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(255))
    brand: Mapped[str] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(Float)
    specs: Mapped[dict] = mapped_column(JSON)
