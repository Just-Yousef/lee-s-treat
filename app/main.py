from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from . import database, routes

app = FastAPI(title="Lee's Treats")
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_cache_control(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=86400"
    return response


BASE_DIR = Path(__file__).resolve().parent


@app.on_event("startup")
def on_startup():
    database.init_db()
    database.seed_items()


app.include_router(routes.router, prefix="/api")
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static", html=True),
    name="static",
)


@app.get("/", response_class=HTMLResponse)
def landing():
    return (BASE_DIR / "templates" / "landing.html").read_text()


@app.get("/menu", response_class=HTMLResponse)
def menu():
    return (BASE_DIR / "templates" / "menu.html").read_text()


@app.get("/login.html", response_class=HTMLResponse)
def login_page():
    return (BASE_DIR / "templates" / "login.html").read_text()


@app.get("/register.html", response_class=HTMLResponse)
def register_page():
    return (BASE_DIR / "templates" / "register.html").read_text()


@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return (BASE_DIR / "templates" / "admin.html").read_text()


@app.get("/admin/orders", response_class=HTMLResponse)
def admin_orders_page():
    return (BASE_DIR / "templates" / "admin-orders.html").read_text()


@app.get("/admin/menu", response_class=HTMLResponse)
def admin_menu_page():
    return (BASE_DIR / "templates" / "admin-menu.html").read_text()