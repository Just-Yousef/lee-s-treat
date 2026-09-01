import sqlite3
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import auth, database, schemas

router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.get("/items", response_model=list[schemas.Item])
def list_items(category: str | None = None):
    try:
        with database.get_connection() as conn:
            if category:
                rows = conn.execute(
                    "SELECT * FROM items WHERE category = ?", (category,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM items").fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/items/{item_id}", response_model=schemas.Item)
def get_item(item_id: int):
    try:
        with database.get_connection() as conn:
            row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Item not found")
        return dict(row)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/items", response_model=schemas.Item, status_code=201)
def create_item(item: schemas.ItemIn):
    try:
        with database.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO items (name, description, price, category, image) VALUES (?, ?, ?, ?, ?)",
                (item.name, item.description, item.price, item.category, item.image),
            )
            item_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        return dict(row)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put("/items/{item_id}", response_model=schemas.Item)
def update_item(item_id: int, item: schemas.ItemIn):
    try:
        with database.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE items SET name = ?, description = ?, price = ?, category = ?, image = ? WHERE id = ?",
                (item.name, item.description, item.price, item.category, item.image, item_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Item not found")
            row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        return dict(row)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    try:
        with database.get_connection() as conn:
            cursor = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/categories")
def list_categories():
    try:
        with database.get_connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT category FROM items ORDER BY category"
            ).fetchall()
        return [r["category"] for r in rows]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Authentication endpoints
@router.post("/auth/register", response_model=schemas.TokenResponse, status_code=201)
def register(user_data: schemas.UserRegister):
    try:
        # Check if username exists
        if auth.get_user_by_username(user_data.username):
            raise HTTPException(status_code=400, detail="Username already taken")

        # Check if email exists
        if auth.get_user_by_email(user_data.email):
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create user
        user_id = auth.create_user(user_data.username, user_data.email, user_data.password)

        # Create token
        token = auth.create_token(user_id)

        # Return user and token
        user = auth.get_user_by_username(user_data.username)
        return schemas.TokenResponse(
            access_token=token,
            user=schemas.UserOut(
                id=user["id"],
                username=user["username"],
                email=user["email"],
                created_at=user["created_at"],
            ),
        )
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/auth/login", response_model=schemas.TokenResponse)
def login(user_data: schemas.UserLogin):
    try:
        user = auth.authenticate_user(user_data.username, user_data.password)
        if not user:
            raise HTTPException(
                status_code=401, detail="Invalid username or password"
            )

        token = auth.create_token(user["id"])

        return schemas.TokenResponse(
            access_token=token,
            user=schemas.UserOut(
                id=user["id"],
                username=user["username"],
                email=user["email"],
                created_at=user["created_at"],
            ),
        )
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/auth/me", response_model=schemas.UserOut)
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Get current user info from token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = auth.validate_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    with database.get_connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

    return schemas.UserOut(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        created_at=user["created_at"],
    )


@router.post("/auth/logout", status_code=204)
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout user by invalidating token."""
    if credentials:
        auth.logout_user(credentials.credentials)


@router.post("/orders", response_model=schemas.OrderOutWithUser, status_code=201)
def create_order(
    order: schemas.OrderIn,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    try:
        user_id = None
        if credentials:
            user_id = auth.validate_token(credentials.credentials)

        with database.get_connection() as conn:
            total = 0.0
            lines = []
            for line in order.items:
                row = conn.execute(
                    "SELECT * FROM items WHERE id = ?", (line.item_id,)
                ).fetchone()
                if not row:
                    raise HTTPException(
                        status_code=404, detail=f"Item {line.item_id} not found"
                    )
                subtotal = row["price"] * line.quantity
                total += subtotal
                lines.append((row["name"], line.quantity, row["price"]))

            cursor = conn.execute(
                "INSERT INTO orders (user_id, customer_name, address, phone, total) VALUES (?, ?, ?, ?, ?)",
                (user_id, order.customer_name, order.address, order.phone, round(total, 2)),
            )
            order_id = cursor.lastrowid
            conn.executemany(
                "INSERT INTO order_items (order_id, item_name, quantity, unit_price) VALUES (?, ?, ?, ?)",
                [(order_id, n, q, p) for n, q, p in lines],
            )

        return get_order_response(order_id)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/orders", response_model=list[schemas.OrderOutWithUser])
def list_orders(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    try:
        user_id = None
        if credentials:
            user_id = auth.validate_token(credentials.credentials)

        if not user_id:
            return []

        with database.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC",
                (user_id,),
            ).fetchall()

            if not rows:
                return []
            # Batch fetch all order items in one query
            order_ids = [r["id"] for r in rows]
            placeholders = ",".join("?" * len(order_ids))
            items_rows = conn.execute(
                f"SELECT order_id, item_name, quantity, unit_price FROM order_items WHERE order_id IN ({placeholders})",
                order_ids,
            ).fetchall()
            items_by_order = {}
            for item in items_rows:
                items_by_order.setdefault(item["order_id"], []).append(dict(item))

            return [
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "customer_name": row["customer_name"],
                    "address": row["address"],
                    "phone": row["phone"],
                    "status": row["status"],
                    "total": row["total"],
                    "created_at": row["created_at"],
                    "items": items_by_order.get(row["id"], []),
                }
                for row in rows
            ]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.patch("/orders/{order_id}", response_model=schemas.OrderOut)
def update_order_status(order_id: int, update: schemas.OrderStatusIn):
    allowed = {"placed", "preparing", "out_for_delivery", "delivered", "cancelled"}
    if update.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(sorted(allowed))}")
    try:
        with database.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE orders SET status = ? WHERE id = ?", (update.status, order_id)
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Order not found")
        return get_order_response(order_id)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


def get_order_response(order_id: int, conn=None):
    own_conn = conn is None
    conn = conn or database.get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        items = conn.execute(
            "SELECT item_name, quantity, unit_price FROM order_items WHERE order_id = ?",
            (order_id,),
        ).fetchall()
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "customer_name": row["customer_name"],
            "address": row["address"],
            "phone": row["phone"],
            "status": row["status"],
            "total": row["total"],
            "created_at": row["created_at"],
            "items": [dict(i) for i in items],
        }
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if own_conn:
            conn.close()