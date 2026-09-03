"""
Separate admin application running on port 8001
"""
from pathlib import Path
import os
import secrets
import time
import sqlite3

from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional

from app import database

app = FastAPI(title="Lee's Treats Admin")

BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "app"

# Admin credentials - use environment variables in production
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# Store active sessions with timestamps (in production, use a database or Redis)
active_sessions = {}
SESSION_TTL = 86400  # 24 hours


def cleanup_expired_sessions():
    """Remove expired sessions from memory"""
    now = time.time()
    expired = [token for token, created in active_sessions.items() if now - created > SESSION_TTL]
    for token in expired:
        del active_sessions[token]


class LoginRequest(BaseModel):
    username: str
    password: str


def is_authenticated(request: Request) -> bool:
    """Check if user is logged in"""
    cleanup_expired_sessions()  # Periodic cleanup on each auth check
    token = request.cookies.get("admin_token")
    if not token or token not in active_sessions:
        return False

    created = active_sessions[token]
    if time.time() - created > SESSION_TTL:
        del active_sessions[token]
        return False

    return True


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if is_authenticated(request):
        return RedirectResponse(url="/admin/")
    return (APP_DIR / "admin" / "templates" / "login.html").read_text()


@app.post("/api/login")
def login(request: LoginRequest):
    if request.username != ADMIN_USERNAME or request.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = secrets.token_urlsafe(32)
    import time
    active_sessions[token] = time.time()
    response = JSONResponse({"success": True})
    response.set_cookie("admin_token", token, max_age=86400, httponly=True)  # 24 hours
    return response


@app.post("/api/logout")
def logout(response: Response, request: Request):
    token = request.cookies.get("admin_token")
    if token in active_sessions:
        del active_sessions[token]
    response = Response()
    response.delete_cookie("admin_token")
    return {"success": True}


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login")
    return (APP_DIR / "admin" / "templates" / "dashboard.html").read_text()


@app.get("/orders", response_class=HTMLResponse)
def admin_orders(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login")
    return (APP_DIR / "admin" / "templates" / "orders.html").read_text()


@app.get("/menu", response_class=HTMLResponse)
def admin_menu(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login")
    return (APP_DIR / "admin" / "templates" / "menu.html").read_text()


# API Endpoints for admin operations
@app.get("/api/orders")
def get_orders(request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        with database.get_connection() as conn:
            orders = conn.execute(
                "SELECT id, customer_name, address, phone, status, total, created_at FROM orders ORDER BY created_at DESC"
            ).fetchall()

            if not orders:
                return []

            # Batch fetch all order items in one query
            order_ids = [order["id"] for order in orders]
            placeholders = ",".join("?" * len(order_ids))
            items = conn.execute(
                f"SELECT order_id, item_name, quantity, unit_price FROM order_items WHERE order_id IN ({placeholders})",
                order_ids,
            ).fetchall()

            # Group items by order_id
            items_by_order = {}
            for item in items:
                items_by_order.setdefault(item["order_id"], []).append(dict(item))

            result = []
            for order in orders:
                result.append({
                    "id": order["id"],
                    "customer_name": order["customer_name"],
                    "address": order["address"],
                    "phone": order["phone"],
                    "status": order["status"],
                    "total": order["total"],
                    "created_at": order["created_at"],
                    "items": items_by_order.get(order["id"], [])
                })
        return result
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


class UpdateOrderRequest(BaseModel):
    status: str

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        allowed = {"placed", "preparing", "out_for_delivery", "delivered", "cancelled"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        return v


class ItemRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    price: float = Field(..., gt=0, le=10000)
    category: str = Field(..., min_length=1, max_length=50)
    image: Optional[str] = Field(default=None, max_length=500)


@app.patch("/api/orders/{order_id}")
@app.put("/api/orders/{order_id}")
def update_order(order_id: int, data: UpdateOrderRequest, request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        with database.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (data.status, order_id)
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Order not found")

        return {"success": True}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/items")
def get_items(request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        with database.get_connection() as conn:
            items = conn.execute(
                "SELECT id, name, description, price, category, image FROM items ORDER BY category, name"
            ).fetchall()
        return [dict(item) for item in items]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/api/items")
def create_item(item: ItemRequest, request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        with database.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO items (name, description, price, category, image) VALUES (?, ?, ?, ?, ?)",
                (item.name, item.description, item.price, item.category, item.image)
            )
            item_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        return dict(row)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.put("/api/items/{item_id}")
def update_item(item_id: int, item: ItemRequest, request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        with database.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE items SET name = ?, description = ?, price = ?, category = ?, image = ? WHERE id = ?",
                (item.name, item.description, item.price, item.category, item.image, item_id)
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Item not found")
            row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        return dict(row)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.delete("/api/items/{item_id}")
def delete_item(item_id: int, request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        with database.get_connection() as conn:
            cursor = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        return None
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)