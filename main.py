import os
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="Beautiful FastAPI Configuration & Customer Wizard")

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

# In-memory storage
# Each customer: {"id": int, "name": str, "email": str, "services": [dict]}
customers_db = []

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
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="login.html", context={"error": None})

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "admin":
        request.session["user"] = username
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": "Invalid username or password. Please try admin/admin."}
    )

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_get(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Find active customer from session
    active_id = request.session.get("active_customer_id")
    active_customer = None
    if active_id is not None:
        for c in customers_db:
            if c["id"] == int(active_id):
                active_customer = c
                break

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user,
            "customers": customers_db,
            "active_customer": active_customer
        }
    )

@app.get("/customer/new", response_class=HTMLResponse)
async def customer_new_get(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="customer_new.html", context={"user": user})

@app.post("/customer/new", response_class=HTMLResponse)
async def customer_new_post(request: Request, name: str = Form(...), email: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Create customer
    new_id = len(customers_db)
    new_customer = {
        "id": new_id,
        "name": name,
        "email": email,
        "services": []
    }
    customers_db.append(new_customer)
    request.session["active_customer_id"] = new_id

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/customer/select/{customer_id}")
async def customer_select(request: Request, customer_id: int):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    for c in customers_db:
        if c["id"] == customer_id:
            request.session["active_customer_id"] = customer_id
            break

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/parameters", response_class=HTMLResponse)
async def parameters_get(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Get active customer
    active_id = request.session.get("active_customer_id")
    active_customer = None
    if active_id is not None:
        for c in customers_db:
            if c["id"] == int(active_id):
                active_customer = c
                break

    return templates.TemplateResponse(
        request=request,
        name="parameters.html",
        context={
            "config": DEFAULT_CONFIG,
            "user": user,
            "active_customer": active_customer
        }
    )

@app.post("/submit", response_class=HTMLResponse)
async def parameters_post(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    form_data = await request.form()

    # Construct config values from form data
    submitted_config = {}
    for key in DEFAULT_CONFIG.keys():
        submitted_config[key] = form_data.get(key, DEFAULT_CONFIG[key])

    # Associate with active customer if any
    active_id = request.session.get("active_customer_id")
    active_customer = None
    if active_id is not None:
        for c in customers_db:
            if c["id"] == int(active_id):
                c["services"].append(submitted_config)
                active_customer = c
                break

    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context={
            "config": submitted_config,
            "user": user,
            "active_customer": active_customer
        }
    )
