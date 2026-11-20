import os
import json
import tempfile
import secrets
from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# Import modularized translation catalogs and tools configuration from constants file
from constants import TRANSLATIONS, TOOLS_CONFIG, TOOL_CATEGORIES
from database import init_db, engine
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
from models import Customer, WorkOrder, ToolConfiguration

app = FastAPI(title="Beautiful FastAPI Localization & Parameter Wizard")

@app.on_event("startup")
async def startup_event():
    init_db()


# In-memory global store for submitted configurations
SUBMITTED_FORMS = []

# Persistent custom producer catalog. Producers are stored per tool and survive restarts.
PRODUCERS_FILE = os.path.join(os.path.dirname(__file__), "data", "producers.json")


def load_producer_catalog():
    catalog = {tool: list(config.get("producers", [])) for tool, config in TOOLS_CONFIG.items()}
    try:
        with open(PRODUCERS_FILE, "r", encoding="utf-8") as file:
            saved_catalog = json.load(file)
        if isinstance(saved_catalog, dict):
            for tool, producers in saved_catalog.items():
                if tool in catalog and isinstance(producers, list):
                    known = {name.casefold() for name in catalog[tool]}
                    for producer in producers:
                        if isinstance(producer, str) and producer.strip():
                            name = producer.strip()
                            if name.casefold() not in known:
                                catalog[tool].append(name)
                                known.add(name.casefold())
    except FileNotFoundError:
        pass
    except (json.JSONDecodeError, OSError):
        pass
    return catalog


def save_producer(tool_name: str, producer_name: str):
    catalog = load_producer_catalog()
    if tool_name not in TOOLS_CONFIG:
        raise ValueError("ابزار نامعتبر است")
    producer_name = producer_name.strip()
    if not producer_name:
        raise ValueError("نام سازنده الزامی است")

    existing = next(
        (name for name in catalog[tool_name] if name.casefold() == producer_name.casefold()),
        None
    )
    if existing:
        return existing, catalog[tool_name]

    catalog[tool_name].append(producer_name)
    data_dir = os.path.dirname(PRODUCERS_FILE)
    os.makedirs(data_dir, exist_ok=True)
    fd, temporary_path = tempfile.mkstemp(prefix="producers_", suffix=".tmp", dir=data_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(catalog, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(temporary_path, PRODUCERS_FILE)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)
    return producer_name, catalog[tool_name]

# Session Secret Key
app.add_middleware(SessionMiddleware, secret_key="super-secret-fastapi-key-for-persian-app")

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

    lang = "fa"
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": None,
            "lang": lang,
            "text": TRANSLATIONS["fa"]
        }
    )

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    lang = "fa"
    if username == "admin" and password == "admin":
        request.session["user"] = username
        return RedirectResponse(url="/parameters", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": TRANSLATIONS["fa"]["error_login"],
            "lang": lang,
            "text": TRANSLATIONS["fa"]
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

    lang = "fa"

    # Retrieve previous customer info if stored in session (name and address only)
    prev_name = request.session.get("prev_customer_name", "")
    prev_address = request.session.get("prev_customer_address", "")

    # Check if previous customer data exists for prefill
    has_previous = any([prev_name, prev_address])

    # Default tool and producer catalog (built-in + permanently saved custom producers).
    default_tool_name = list(TOOLS_CONFIG.keys())[0]
    producer_catalog = load_producer_catalog()
    tools_config_for_template = {
        tool: {**config, "producers": producer_catalog.get(tool, config.get("producers", []))}
        for tool, config in TOOLS_CONFIG.items()
    }

    return templates.TemplateResponse(
        request=request,
        name="parameters.html",
        context={
            "tools_config": tools_config_for_template,
            "tool_categories": TOOL_CATEGORIES,
            "default_tool": default_tool_name,
            "user": user,
            "lang": lang,
            "text": TRANSLATIONS["fa"],
            "prev_name": prev_name,
            "prev_address": prev_address,
            "has_previous": has_previous
        }
    )


@app.get("/customers/search")
def search_customers(request: Request, q: str = ""):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "احراز هویت الزامی است"}, status_code=401)

    query = q.strip()
    if len(query) < 2:
        return []

    with Session(engine) as db:
        customers = db.scalars(
            select(Customer)
            .where(Customer.name.ilike(f"%{query}%"))
            .order_by(Customer.name)
            .limit(20)
        ).all()
        return [
            {
                "id": customer.id,
                "name": customer.name,
                "description": customer.description,
                "national_id": customer.national_id,
                "postal_id": customer.postal_id,
                "address": customer.address,
                "phone_number": customer.phone_number,
            }
            for customer in customers
        ]


@app.get("/work-orders/search")
def search_work_orders(request: Request, q: str = ""):
    if not get_current_user(request):
        return JSONResponse({"error": "احراز هویت الزامی است"}, status_code=401)
    query = q.strip()
    with Session(engine) as db:
        statement = (
            select(WorkOrder).options(selectinload(WorkOrder.customer))
            .order_by(WorkOrder.created_at.desc())
        )
        if query:
            pattern = f"%{query}%"
            statement = statement.join(WorkOrder.customer).where(
                WorkOrder.work_name.ilike(pattern)
                | WorkOrder.work_id.ilike(pattern)
                | Customer.name.ilike(pattern)
            )
        orders = db.scalars(statement.limit(20)).unique().all()
        return [{
            "work_id": order.work_id,
            "work_name": order.work_name or "",
            "customer_id": order.customer_id,
            "customer_name": order.customer.name,
            "customer_address": order.customer.address or "",
            "tool_count": len(order.tools),
        } for order in orders]


@app.post("/work-orders")
async def create_work_order(request: Request):
    if not get_current_user(request):
        return JSONResponse({"error": "احراز هویت الزامی است"}, status_code=401)
    try:
        payload = await request.json()
        customer_id = int(payload.get("customer_id"))
        work_name = str(payload.get("work_name", "")).strip()
        if not work_name:
            return JSONResponse({"error": "نام پرونده کاری الزامی است"}, status_code=400)
        if len(work_name) > 255:
            return JSONResponse({"error": "نام پرونده نباید بیشتر از ۲۵۵ نویسه باشد"}, status_code=400)
    except (TypeError, ValueError, AttributeError):
        return JSONResponse({"error": "اطلاعات پرونده یا مشتری معتبر نیست"}, status_code=400)

    with Session(engine) as db:
        customer = db.get(Customer, customer_id)
        if customer is None:
            return JSONResponse({"error": "مشتری یافت نشد"}, status_code=404)
        # Use a temporary unique value for the insert, then replace it with
        # the database-generated auto-incrementing primary key.
        order = WorkOrder(
            work_id="PENDING-" + secrets.token_hex(8).upper(),
            work_name=work_name,
            customer_id=customer.id
        )
        db.add(order)
        db.flush()
        order.work_id = str(order.id)
        db.commit()
        return {"work_id": order.work_id, "work_name": order.work_name, "customer_id": customer.id, "customer_name": customer.name}


@app.get("/work-orders/{work_id}", response_class=HTMLResponse)
def work_order_detail(request: Request, work_id: str):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    with Session(engine) as db:
        order = db.scalar(
            select(WorkOrder).options(
                selectinload(WorkOrder.customer), selectinload(WorkOrder.tools)
            ).where(WorkOrder.work_id == work_id)
        )
        if order is None:
            return RedirectResponse(url="/submissions", status_code=status.HTTP_303_SEE_OTHER)
        tools = [{
            "id": tool.id, "selected_tool": tool.selected_tool, "producer_name": tool.producer_name,
            "model": tool.model, "range": tool.tool_range, "resolution": tool.resolution,
            "serial_no": tool.serial_no, "tool_location": tool.tool_location,
            "calibration_points": tool.calibration_points or [],
        } for tool in order.tools]
        context = {
            "user": user, "lang": "fa", "text": TRANSLATIONS["fa"],
            "work_order": {"work_id": order.work_id, "work_name": order.work_name or "", "customer_name": order.customer.name,
                           "customer_address": order.customer.address or ""},
            "tools": tools,
        }
    return templates.TemplateResponse(request=request, name="work_order_detail.html", context=context)


@app.post("/producers")
async def add_producer(request: Request):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "احراز هویت الزامی است"}, status_code=401)
    try:
        payload = await request.json()
        tool_name = str(payload.get("tool_name", "")).strip()
        producer_name = str(payload.get("producer_name", "")).strip()
        saved_name, producers = save_producer(tool_name, producer_name)
        return {"producer": saved_name, "producers": producers}
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except (TypeError, AttributeError, json.JSONDecodeError):
        return JSONResponse({"error": "درخواست نامعتبر است"}, status_code=400)

@app.get("/submissions", response_class=HTMLResponse)
async def submissions_get(request: Request, page: int = 1):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    page_size = 20
    page = max(1, page)
    with Session(engine) as db:
        total_count = db.scalar(select(func.count()).select_from(WorkOrder)) or 0
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        page = min(page, total_pages)
        orders = db.scalars(
            select(WorkOrder).options(
                selectinload(WorkOrder.customer), selectinload(WorkOrder.tools)
            ).order_by(WorkOrder.created_at.desc(), WorkOrder.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        work_orders = [{
            "work_id": order.work_id,
            "work_name": order.work_name or "",
            "customer_name": order.customer.name,
            "customer_address": order.customer.address or "",
            "tool_count": len(order.tools),
            "created_at": order.created_at,
        } for order in orders]

    return templates.TemplateResponse(
        request=request, name="submissions.html",
        context={
            "user": user, "lang": "fa", "text": TRANSLATIONS["fa"],
            "submissions": work_orders, "page": page, "page_size": page_size,
            "total_count": total_count, "total_pages": total_pages,
            "start_index": (page - 1) * page_size,
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
        "نام مشتری",
        "آدرس مشتری",
        "ابزار",
        "سازنده",
        "مدل",
        "گستره",
        "تفکیک‌پذیری",
        "شماره سریال",
        "محل استقرار ابزار",
        "نقاط کالیبراسیون (UUC، افزایشی، کاهشی)"
    ])

    for sub in SUBMITTED_FORMS:
        # Format calibration points
        cal_str_list = []
        for pt in sub.get("calibration_points", []):
            if pt.get("uuc") or pt.get("ref_rising") or pt.get("ref_falling"):
                cal_str_list.append(f"UUC:{pt.get('uuc')}|افزایشی:{pt.get('ref_rising')}|کاهشی:{pt.get('ref_falling')}")
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

    lang = "fa"
    form_data = await request.form()

    work_id = form_data.get("work_id", "").strip()
    if not work_id:
        return JSONResponse({"error": "شناسه پرونده الزامی است"}, status_code=400)

    with Session(engine) as db:
        order = db.scalar(
            select(WorkOrder).options(selectinload(WorkOrder.customer))
            .where(WorkOrder.work_id == work_id)
        )
        if order is None:
            return JSONResponse({"error": "پرونده کاری یافت نشد"}, status_code=404)
        customer_name = order.customer.name
        customer_address = order.customer.address or ""
        customer_id = order.customer_id

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
        "customer_id": customer_id,
        "customer_name": customer_name,
        "customer_address": customer_address,
        "work_id": work_id,
        "selected_tool": selected_tool,
        "producer_name": producer_name,
        "model": model,
        "range": tool_range,
        "resolution": resolution,
        "serial_no": serial_no,
        "tool_location": tool_location,
        "calibration_points": calibration_points
    }

    with Session(engine) as db:
        order = db.scalar(select(WorkOrder).where(WorkOrder.work_id == work_id))
        if order is None or order.customer_id != customer_id:
            return JSONResponse({"error": "پرونده کاری معتبر نیست"}, status_code=400)
        db.add(ToolConfiguration(
            work_order_id=order.id, selected_tool=selected_tool, producer_name=producer_name,
            model=model, tool_range=tool_range, resolution=resolution, serial_no=serial_no,
            tool_location=tool_location, calibration_points=calibration_points
        ))
        db.commit()

    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context={
            "user": user,
            "lang": lang,
            "text": TRANSLATIONS["fa"],
            "record": submission_record
        }
    )
