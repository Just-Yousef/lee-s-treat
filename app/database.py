import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "food.db"


def get_connection() -> sqlite3.Connection:
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise RuntimeError(f"Failed to connect to database: {str(e)}")


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                category TEXT,
                image TEXT
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                customer_name TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                status TEXT DEFAULT 'placed',
                total REAL DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            );

            CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
            CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
            """
        )


def seed_items() -> None:
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        if count:
            return
        items = [
            ("Margherita Pizza", "Classic tomato, mozzarella and basil", 9.99, "Pizza", "https://images.unsplash.com/photo-1513104890138-7c749659a591?"),
            ("Pepperoni Pizza", "Pepperoni, mozzarella and tomato sauce", 12.49, "Pizza", "https://images.unsplash.com/photo-1628840042765-356cda07504e?"),
            ("Cheeseburger", "Beef patty, cheddar cheese, lettuce and tomato", 8.79, "Burgers", "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?"),
            ("Double Bacon Burger", "Double beef, crispy bacon and BBQ sauce", 11.99, "Burgers", "https://images.unsplash.com/photo-1553979459-d2229ba7433b?"),
            ("Chicken Salad", "Grilled chicken, fresh greens and vinaigrette", 10.49, "Salads", "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?"),
            ("Caesar Salad", "Romaine, croutons, parmesan and caesar dressing", 9.29, "Salads", "https://images.unsplash.com/photo-1550304943-4f24f54ddde9?"),
            ("Spaghetti Bolognese", "Pasta with slow-cooked beef ragu", 11.49, "Pasta", "https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?"),
            ("Penne Arrabbiata", "Pasta in spicy tomato and garlic sauce", 9.99, "Pasta", "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?"),
            ("Chocolate Lava Cake", "Warm, gooey chocolate cake with vanilla ice cream", 6.49, "Desserts", "https://images.unsplash.com/photo-1624353365286-3f8d62daad51?"),
            ("Cheesecake", "Creamy cheesecake with berry topping", 5.99, "Desserts", "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?"),
            ("Orange Juice", "Freshly squeezed orange juice", 3.49, "Drinks", "https://images.unsplash.com/photo-1600271886742-f049cd451bba?"),
            ("Sparkling Water", "Chilled sparkling mineral water", 2.29, "Drinks", "https://images.unsplash.com/photo-1581006852262-e4307cf6283a?"),
        ]
        conn.executemany(
            "INSERT INTO items (name, description, price, category, image) VALUES (?, ?, ?, ?, ?)",
            items,
        )