import os
from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# Import modularized translation catalogs and test configuration from constants file
from constants import TRANSLATIONS, TESTS_CONFIG

app = FastAPI(title="Beautiful FastAPI Localization & Parameter Wizard")

# Session Secret Key
app.add_middleware(SessionMiddleware, secret_key="super-secret-fastapi-key-for-templates-bilingual-dynamic")

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

@app.get("/change-lang/{lang}")
async def change_lang(request: Request, lang: str):
    if lang in ["en", "fa"]:
        request.session["lang"] = lang
    referer = request.headers.get("referer", "/parameters")
    if "/submit" in referer:
        referer = "/parameters"
    return RedirectResponse(url=referer, status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/parameters", status_code=status.HTTP_303_SEE_OTHER)

    lang = request.session.get("lang", "en")
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": None,
            "lang": lang,
            "text": TRANSLATIONS[lang]
        }
    )

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    lang = request.session.get("lang", "en")
    if username == "admin" and password == "admin":
        request.session["user"] = username
        return RedirectResponse(url="/parameters", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": TRANSLATIONS[lang]["error_login"],
            "lang": lang,
            "text": TRANSLATIONS[lang]
        }
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

    lang = request.session.get("lang", "en")

    # Retrieve previous customer info if stored in session
    prev_date = request.session.get("prev_customer_date", "")
    prev_name = request.session.get("prev_customer_name", "")
    prev_cert = request.session.get("prev_certificate_id", "")
    prev_place = request.session.get("prev_customer_place", "")
    prev_machine = request.session.get("prev_machine_name", "")

    # Check if any previous data exists for prefill
    has_previous = any([prev_date, prev_name, prev_cert, prev_place, prev_machine])

    return templates.TemplateResponse(
        request=request,
        name="parameters.html",
        context={
            "tests_config": TESTS_CONFIG,
            "user": user,
            "lang": lang,
            "text": TRANSLATIONS[lang],
            "prev_date": prev_date,
            "prev_name": prev_name,
            "prev_cert": prev_cert,
            "prev_place": prev_place,
            "prev_machine": prev_machine,
            "has_previous": has_previous
        }
    )

@app.get("/submit")
async def submit_get(request: Request):
    return RedirectResponse(url="/parameters", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/submit", response_class=HTMLResponse)
async def parameters_post(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    lang = request.session.get("lang", "en")
    form_data = await request.form()

    # Extract customer info
    customer_date = form_data.get("customer_date", "")
    customer_name = form_data.get("customer_name", "")
    certificate_id = form_data.get("certificate_id", "")
    customer_place = form_data.get("customer_place", "")
    machine_name = form_data.get("machine_name", "")

    # Extract test name
    selected_test = form_data.get("selected_test", "Test A")

    # Store in session for prefill next time
    request.session["prev_customer_date"] = customer_date
    request.session["prev_customer_name"] = customer_name
    request.session["prev_certificate_id"] = certificate_id
    request.session["prev_customer_place"] = customer_place
    request.session["prev_machine_name"] = machine_name

    # Construct config values dynamically based on selected test's keys
    submitted_config = {}
    test_keys = TESTS_CONFIG.get(selected_test, TESTS_CONFIG["Test A"]).keys()
    for key in test_keys:
        submitted_config[key] = form_data.get(key, "")

    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context={
            "config": submitted_config,
            "user": user,
            "lang": lang,
            "text": TRANSLATIONS[lang],
            "selected_test": selected_test,
            "customer_date": customer_date,
            "customer_name": customer_name,
            "certificate_id": certificate_id,
            "customer_place": customer_place,
            "machine_name": machine_name
        }
    )
