from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse

from .db import init_db
from .i18n import t
from .auth import NotAuthenticated, current_user
from .models import User

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["t"] = t

app = FastAPI(title="fitai")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.exception_handler(NotAuthenticated)
def _redirect_to_login(request: Request, exc: NotAuthenticated):
    return RedirectResponse("/login", status_code=303)


@app.on_event("startup")
def _startup() -> None:
    init_db()


def register_routers() -> None:
    from importlib import import_module
    for name in ("auth", "home", "metrics", "goals", "plan", "workouts", "nutrition", "settings"):
        if not (BASE_DIR / "routers" / f"{name}.py").exists():
            continue
        module = import_module(f"app.routers.{name}")
        app.include_router(module.router)


register_routers()
