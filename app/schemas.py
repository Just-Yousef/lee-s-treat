from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class Item(BaseModel):
    id: int
    name: str
    description: str
    price: float
    category: str
    image: Optional[str] = None


class ItemIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    price: float = Field(..., gt=0, le=10000)
    category: str = Field(default="Other", min_length=1, max_length=50)
    image: Optional[str] = Field(default=None, max_length=500)


class OrderStatusIn(BaseModel):
    status: str


class OrderItemIn(BaseModel):
    item_id: int = Field(..., gt=0)
    quantity: int = Field(default=1, gt=0, le=100)


class OrderIn(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100)
    address: str = Field(default="", max_length=500)
    phone: str = Field(default="", max_length=20)
    items: List[OrderItemIn] = Field(..., min_length=1)


class OrderItemOut(BaseModel):
    item_name: str
    quantity: int
    unit_price: float


class OrderOut(BaseModel):
    id: int
    customer_name: str
    address: str
    phone: str
    status: str
    total: float
    created_at: str
    items: List[OrderItemOut]


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class OrderOutWithUser(OrderOut):
    user_id: Optional[int] = None