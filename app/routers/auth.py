from fastapi import APIRouter, Depends, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session
from ..db import get_session
from .. import auth
from ..main import templates

router = APIRouter()


def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        auth.COOKIE_NAME, token, max_age=auth.SESSION_DAYS * 86400,
        httponly=True, samesite="lax")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
def login(request: Request, session: Session = Depends(get_session),
          username: str = Form(...), password: str = Form(...)):
    user = auth.authenticate(session, username, password)
    if user is None:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Identifiants incorrects."}, status_code=200)
    token = auth.create_session(session, user)
    response = RedirectResponse("/", status_code=303)
    _set_cookie(response, token)
    return response


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@router.post("/register")
def register(request: Request, session: Session = Depends(get_session),
             username: str = Form(...), password: str = Form(...)):
    try:
        user = auth.create_user(session, username, password)
    except auth.UsernameTaken:
        return templates.TemplateResponse(
            "register.html", {"request": request, "error": "Ce nom est déjà pris."}, status_code=200)
    token = auth.create_session(session, user)
    response = RedirectResponse("/", status_code=303)
    _set_cookie(response, token)
    return response


@router.post("/logout")
@router.get("/logout")
def logout(request: Request, session: Session = Depends(get_session)):
    auth.delete_session(session, request.cookies.get(auth.COOKIE_NAME))
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(auth.COOKIE_NAME)
    return response
