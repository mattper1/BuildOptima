from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class Build(Base):
    __tablename__ = "builds"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    build_name: Mapped[str] = mapped_column(String(255))
    use_case: Mapped[str] = mapped_column(String(50))
    budget: Mapped[int] = mapped_column(Integer)
    total_price: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="builds")
    components: Mapped[list["BuildComponent"]] = relationship(
        back_populates="build", cascade="all, delete-orphan"
    )


class BuildComponent(Base):
    __tablename__ = "build_components"

    id: Mapped[int] = mapped_column(primary_key=True)
    build_id: Mapped[int] = mapped_column(ForeignKey("builds.id", ondelete="CASCADE"))
    component_category: Mapped[str] = mapped_column(String(50))
    part_name: Mapped[str] = mapped_column(String(255))
    part_price: Mapped[float] = mapped_column(Float)
    reason_selected: Mapped[str] = mapped_column(Text)

    build: Mapped["Build"] = relationship(back_populates="components")
