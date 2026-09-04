import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("DB_PATH", str(Path(__file__).resolve().parent.parent / "food.db")))


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


            CREATE TABLE IF NOT EXISTS tokens (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );

            CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
            CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
            """
        )


def seed_items() -> None:
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        if count:
            local_images = {
                "Margherita Pizza": "/static/images/margherita-pizza.jpg",
                "Pepperoni Pizza": "/static/images/pepperoni-pizza.jpg",
                "Cheeseburger": "/static/images/cheeseburger.jpg",
                "Double Bacon Burger": "/static/images/double-bacon-burger.jpg",
                "Chicken Salad": "/static/images/chicken-salad.jpg",
                "Caesar Salad": "/static/images/caesar-salad.jpg",
                "Spaghetti Bolognese": "/static/images/spaghetti-bolognese.jpg",
                "Penne Arrabbiata": "/static/images/penne-arrabbiata.jpg",
                "Chocolate Lava Cake": "/static/images/chocolate-lava-cake.jpg",
                "Cheesecake": "/static/images/cheesecake.jpg",
                "Orange Juice": "/static/images/orange-juice.jpg",
                "Sparkling Water": "/static/images/sparkling-water.jpg",
            }
            for name, image in local_images.items():
                conn.execute(
                    "UPDATE items SET image = ? WHERE name = ? AND image LIKE 'https://images.unsplash.com/%'",
                    (image, name),
                )
            return
        items = [
            ("Margherita Pizza", "Classic tomato, mozzarella and basil", 9.99, "Pizza", "/static/images/margherita-pizza.jpg"),
            ("Pepperoni Pizza", "Pepperoni, mozzarella and tomato sauce", 12.49, "Pizza", "/static/images/pepperoni-pizza.jpg"),
            ("Cheeseburger", "Beef patty, cheddar cheese, lettuce and tomato", 8.79, "Burgers", "/static/images/cheeseburger.jpg"),
            ("Double Bacon Burger", "Double beef, crispy bacon and BBQ sauce", 11.99, "Burgers", "/static/images/double-bacon-burger.jpg"),
            ("Chicken Salad", "Grilled chicken, fresh greens and vinaigrette", 10.49, "Salads", "/static/images/chicken-salad.jpg"),
            ("Caesar Salad", "Romaine, croutons, parmesan and caesar dressing", 9.29, "Salads", "/static/images/caesar-salad.jpg"),
            ("Spaghetti Bolognese", "Pasta with slow-cooked beef ragu", 11.49, "Pasta", "/static/images/spaghetti-bolognese.jpg"),
            ("Penne Arrabbiata", "Pasta in spicy tomato and garlic sauce", 9.99, "Pasta", "/static/images/penne-arrabbiata.jpg"),
            ("Chocolate Lava Cake", "Warm, gooey chocolate cake with vanilla ice cream", 6.49, "Desserts", "/static/images/chocolate-lava-cake.jpg"),
            ("Cheesecake", "Creamy cheesecake with berry topping", 5.99, "Desserts", "/static/images/cheesecake.jpg"),
            ("Orange Juice", "Freshly squeezed orange juice", 3.49, "Drinks", "/static/images/orange-juice.jpg"),
            ("Sparkling Water", "Chilled sparkling mineral water", 2.29, "Drinks", "/static/images/sparkling-water.jpg"),
        ]
        conn.executemany(
            "INSERT INTO items (name, description, price, category, image) VALUES (?, ?, ?, ?, ?)",
            items,
        )