import os
from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="Beautiful FastAPI Localization & Parameter Wizard")

# Session Secret Key
app.add_middleware(SessionMiddleware, secret_key="super-secret-fastapi-key-for-templates-bilingual")

# Config Dict
DEFAULT_CONFIG = {
    "Database Host": "localhost",
    "Database Port": "5432",
    "API Key": "super-secret-api-key-123",
    "Max Retries": "5",
    "Timeout (seconds)": "30"
}

# Translation Catalog for English and Persian (RTL support included)
TRANSLATIONS = {
    "en": {
        "title": "ConfigFlow",
        "login_title": "Sign in to your account",
        "login_subtitle": "Manage and deploy service configurations elegantly",
        "username": "Username",
        "password": "Password",
        "sign_in": "Sign In",
        "logout": "Logout",
        "logged_in_as": "Logged in as",
        "step": "Step",
        "of": "of",
        "wizard_title": "Service Configuration",
        "wizard_subtitle": "Please fill in the details below to deploy your configuration.",
        "customer_section": "Customer Profile",
        "customer_section_desc": "Enter the customer details for this configuration.",
        "prefill_title": "Use previous customer details?",
        "prefill_btn": "Prefill",
        "prefilled_btn": "Prefilled!",
        "customer_date": "Date",
        "customer_name": "Customer Name",
        "certificate_id": "Certificate ID",
        "customer_place": "Place",
        "machine_name": "Machine Name",
        "back": "Back",
        "forward": "Forward",
        "submit": "Submit Configuration",
        "success_title": "Configuration Submitted",
        "success_subtitle": "Successfully created and saved service configuration for",
        "submitted_details": "Just Submitted Service Configuration",
        "configure_another": "Configure Another Service",
        "sign_out": "Sign Out",
        "error_login": "Invalid username or password. Please try admin/admin.",
        # Parameter labels
        "Database Host": "Database Host",
        "Database Port": "Database Port",
        "API Key": "API Key",
        "Max Retries": "Max Retries",
        "Timeout (seconds)": "Timeout (seconds)"
    },
    "fa": {
        "title": "جریان پیکربندی",
        "login_title": "ورود به حساب کاربری",
        "login_subtitle": "پیکربندی خدمات خود را به زیبایی مدیریت و مستقر کنید",
        "username": "نام کاربری",
        "password": "رمز عبور",
        "sign_in": "ورود",
        "logout": "خروج",
        "logged_in_as": "وارد شده به عنوان",
        "step": "مرحله",
        "of": "از",
        "wizard_title": "پیکربندی سرویس",
        "wizard_subtitle": "لطفاً جزئیات زیر را برای استقرار پیکربندی خود وارد کنید.",
        "customer_section": "پروفایل مشتری",
        "customer_section_desc": "مشخصات سازمان مشتری را برای این پیکربندی وارد کنید.",
        "prefill_title": "استفاده از اطلاعات مشتری قبلی؟",
        "prefill_btn": "تکمیل خودکار",
        "prefilled_btn": "تکمیل شد!",
        "customer_date": "تاریخ",
        "customer_name": "نام مشتری",
        "certificate_id": "شناسه گواهینامه",
        "customer_place": "محل",
        "machine_name": "نام دستگاه",
        "back": "قبلی",
        "forward": "بعدی",
        "submit": "ثبت پیکربندی",
        "success_title": "پیکربندی با موفقیت ثبت شد",
        "success_subtitle": "پیکربندی سرویس با موفقیت ایجاد و برای مشتری ذخیره شد:",
        "submitted_details": "پیکربندی سرویس ارسال شده",
        "configure_another": "پیکربندی یک سرویس دیگر",
        "sign_out": "خروج از سیستم",
        "error_login": "نام کاربری یا رمز عبور نامعتبر است. لطفا admin/admin را امتحان کنید.",
        # Parameter labels
        "Database Host": "آدرس پایگاه داده",
        "Database Port": "پورت پایگاه داده",
        "API Key": "کلید API",
        "Max Retries": "حداکثر دفعات تلاش",
        "Timeout (seconds)": "زمان انتظار (ثانیه)"
    }
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
            "config": DEFAULT_CONFIG,
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

    # Store in session for prefill next time
    request.session["prev_customer_date"] = customer_date
    request.session["prev_customer_name"] = customer_name
    request.session["prev_certificate_id"] = certificate_id
    request.session["prev_customer_place"] = customer_place
    request.session["prev_machine_name"] = machine_name

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
            "lang": lang,
            "text": TRANSLATIONS[lang],
            "customer_date": customer_date,
            "customer_name": customer_name,
            "certificate_id": certificate_id,
            "customer_place": customer_place,
            "machine_name": machine_name
        }
    )
