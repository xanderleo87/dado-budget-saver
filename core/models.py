"""Pydantic data models for type-safe data transfer."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Expense(BaseModel):
    id: Optional[int] = None
    amount: float
    category_id: int
    category_name: Optional[str] = None
    merchant: Optional[str] = None
    description: str
    date: str
    time: Optional[str] = None
    is_recurring: bool = False
    notes: Optional[str] = None
    created_at: Optional[str] = None


class Loan(BaseModel):
    id: Optional[int] = None
    platform: str
    amount_borrowed: float
    amount_paid: float = 0
    remaining: float = 0
    status: str = "active"
    due_date: Optional[str] = None
    interest_rate: float = 0
    notes: Optional[str] = None
    date: str
    created_at: Optional[str] = None


class LoanPayment(BaseModel):
    id: Optional[int] = None
    loan_id: int
    amount: float
    date: str
    notes: Optional[str] = None
    created_at: Optional[str] = None


class Category(BaseModel):
    id: Optional[int] = None
    name: str
    icon: str = "other"
    color: str = "#6C7B95"
    is_default: bool = False


class Budget(BaseModel):
    id: Optional[int] = None
    category_id: int
    category_name: Optional[str] = None
    monthly_limit: float
    month_year: str
    spent: Optional[float] = 0


class ChatMessage(BaseModel):
    id: Optional[int] = None
    role: str
    message: str
    action_type: Optional[str] = None
    action_data: Optional[str] = None
    timestamp: Optional[str] = None


class Income(BaseModel):
    id: Optional[int] = None
    amount: float
    source: str
    description: Optional[str] = None
    date: str
    is_recurring: bool = False
    notes: Optional[str] = None
    created_at: Optional[str] = None


class AIAction(BaseModel):
    type: str
    data: Optional[dict] = None


class AIResponse(BaseModel):
    message: str
    action: AIAction = Field(default_factory=lambda: AIAction(type="none"))
