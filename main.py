import os
from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# Import modularized translation catalogs and tools configuration from constants file
from constants import TRANSLATIONS, TOOLS_CONFIG

app = FastAPI(title="Beautiful FastAPI Localization & Parameter Wizard")

# In-memory global store for submitted configurations
SUBMITTED_FORMS = []

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

    # Retrieve previous customer info if stored in session (name and address only)
    prev_name = request.session.get("prev_customer_name", "")
    prev_address = request.session.get("prev_customer_address", "")

    # Check if previous customer data exists for prefill
    has_previous = any([prev_name, prev_address])

    # Default tool
    default_tool_name = list(TOOLS_CONFIG.keys())[0]

    return templates.TemplateResponse(
        request=request,
        name="parameters.html",
        context={
            "tools_config": TOOLS_CONFIG,
            "default_tool": default_tool_name,
            "user": user,
            "lang": lang,
            "text": TRANSLATIONS[lang],
            "prev_name": prev_name,
            "prev_address": prev_address,
            "has_previous": has_previous
        }
    )

@app.get("/submissions", response_class=HTMLResponse)
async def submissions_get(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    lang = request.session.get("lang", "en")
    return templates.TemplateResponse(
        request=request,
        name="submissions.html",
        context={
            "user": user,
            "lang": lang,
            "text": TRANSLATIONS[lang],
            "submissions": SUBMITTED_FORMS
        }
    )

@app.get("/submissions/download")
async def submissions_download(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    import csv
    import io
    from fastapi.responses import StreamingResponse

    # Generate CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write dynamic header
    writer.writerow([
        "Customer Name",
        "Customer Address",
        "Tool",
        "Producer",
        "Model",
        "Range",
        "Resolution",
        "Serial No",
        "Location of Tool",
        "Calibration Points (UUC, Rising, Falling)"
    ])

    for sub in SUBMITTED_FORMS:
        # Format calibration points
        cal_str_list = []
        for pt in sub.get("calibration_points", []):
            if pt.get("uuc") or pt.get("ref_rising") or pt.get("ref_falling"):
                cal_str_list.append(f"UUC:{pt.get('uuc')}|Rising:{pt.get('ref_rising')}|Falling:{pt.get('ref_falling')}")
        cal_str = "; ".join(cal_str_list)

        writer.writerow([
            sub["customer_name"],
            sub["customer_address"],
            sub["selected_tool"],
            sub["producer_name"],
            sub["model"],
            sub["range"],
            sub["resolution"],
            sub["serial_no"],
            sub["tool_location"],
            cal_str
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=calibrations_submissions.csv"}
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

    # Extract customer info (only name and address as requested)
    customer_name = form_data.get("customer_name", "").strip()
    customer_address = form_data.get("customer_address", "").strip()

    # Store in session for prefill next time
    request.session["prev_customer_name"] = customer_name
    request.session["prev_customer_address"] = customer_address

    # Extract tool and producer info
    selected_tool = form_data.get("selected_tool", list(TOOLS_CONFIG.keys())[0]).strip()
    producer_name = form_data.get("producer_name", "").strip()

    # Extract tool specs
    model = form_data.get("model", "").strip()
    tool_range = form_data.get("range", "").strip()
    resolution = form_data.get("resolution", "").strip()
    serial_no = form_data.get("serial_no", "").strip()
    tool_location = form_data.get("tool_location", "").strip()

    # Extract calibration table rows (6 rows default)
    # Unit Under Calibration (mbar), Reference value (mbar): Rising, Falling
    calibration_points = []
    # Collect indices from form_data
    row_count = 6
    for i in range(row_count):
        uuc = form_data.get(f"uuc_{i}", "").strip()
        ref_rising = form_data.get(f"ref_rising_{i}", "").strip()
        ref_falling = form_data.get(f"ref_falling_{i}", "").strip()
        if uuc or ref_rising or ref_falling:
            calibration_points.append({
                "uuc": uuc,
                "ref_rising": ref_rising,
                "ref_falling": ref_falling
            })

    submission_record = {
        "customer_name": customer_name,
        "customer_address": customer_address,
        "selected_tool": selected_tool,
        "producer_name": producer_name,
        "model": model,
        "range": tool_range,
        "resolution": resolution,
        "serial_no": serial_no,
        "tool_location": tool_location,
        "calibration_points": calibration_points
    }

    # Save the submission in the global list
    SUBMITTED_FORMS.append(submission_record)

    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context={
            "user": user,
            "lang": lang,
            "text": TRANSLATIONS[lang],
            "record": submission_record
        }
    )
