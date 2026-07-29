import os
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="Beautiful FastAPI Configuration Wizard")

# Session Secret Key
app.add_middleware(SessionMiddleware, secret_key="super-secret-fastapi-key-for-templates")

# Config Dict
DEFAULT_CONFIG = {
    "Database Host": "localhost",
    "Database Port": "5432",
    "API Key": "super-secret-api-key-123",
    "Max Retries": "5",
    "Timeout (seconds)": "30"
}

# Templates configuration
templates = Jinja2Templates(directory="templates")

# Dependency to check authentication
def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        return None
    return user

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/parameters", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/parameters", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="login.html", context={"error": None})

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "admin":
        request.session["user"] = username
        return RedirectResponse(url="/parameters", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": "Invalid username or password. Please try admin/admin."}
    )

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/parameters", response_class=HTMLResponse)
async def parameters_get(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Retrieve previous customer info if stored in session
    prev_name = request.session.get("prev_customer_name", "")
    prev_email = request.session.get("prev_customer_email", "")

    return templates.TemplateResponse(
        request=request,
        name="parameters.html",
        context={
            "config": DEFAULT_CONFIG,
            "user": user,
            "prev_name": prev_name,
            "prev_email": prev_email
        }
    )

@app.post("/submit", response_class=HTMLResponse)
async def parameters_post(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    form_data = await request.form()

    # Extract customer info
    customer_name = form_data.get("customer_name", "")
    customer_email = form_data.get("customer_email", "")

    # Store in session for prefill next time
    if customer_name:
        request.session["prev_customer_name"] = customer_name
    if customer_email:
        request.session["prev_customer_email"] = customer_email

    # Construct config values from form data
    submitted_config = {}
    for key in DEFAULT_CONFIG.keys():
        submitted_config[key] = form_data.get(key, DEFAULT_CONFIG[key])

    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context={
            "config": submitted_config,
            "user": user,
            "customer_name": customer_name,
            "customer_email": customer_email
        }
    )
