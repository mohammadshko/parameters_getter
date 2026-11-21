from sqlalchemy import BigInteger, String, Text, ForeignKey, DateTime, JSON, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    national_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    postal_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(30), nullable=True)


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    work_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    work_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    customer: Mapped["Customer"] = relationship()
    tools: Mapped[list["ToolConfiguration"]] = relationship(
        back_populates="work_order", cascade="all, delete-orphan", order_by="ToolConfiguration.id"
    )


class ToolConfiguration(Base):
    __tablename__ = "tool_configurations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    work_order_id: Mapped[int] = mapped_column(ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_tool: Mapped[str] = mapped_column(String(255), nullable=False)
    producer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    tool_range: Mapped[str] = mapped_column(String(255), nullable=False)
    resolution: Mapped[str] = mapped_column(String(255), nullable=False)
    serial_no: Mapped[str] = mapped_column(String(255), nullable=False)
    tool_location: Mapped[str] = mapped_column(String(255), nullable=False)
    calibration_points: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    work_order: Mapped["WorkOrder"] = relationship(back_populates="tools")


class Producer(Base):
    __tablename__ = "producers"
    __table_args__ = (UniqueConstraint("tool_name", "name", name="uq_producer_tool_name_name"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
