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
from models import Customer, WorkOrder, ToolConfiguration, Producer

app = FastAPI(title="Beautiful FastAPI Localization & Parameter Wizard")

@app.on_event("startup")
async def startup_event():
    init_db()
    sync_producer_catalog()


# In-memory global store for submitted configurations
SUBMITTED_FORMS = []

# Producers are stored in PostgreSQL, scoped to their tool.
def sync_producer_catalog():
    legacy_path = os.path.join(os.path.dirname(__file__), "data", "producers.json")
    catalog = {tool: list(config.get("producers", [])) for tool, config in TOOLS_CONFIG.items()}
    try:
        with open(legacy_path, "r", encoding="utf-8") as file:
            legacy_catalog = json.load(file)
        if isinstance(legacy_catalog, dict):
            for tool, names in legacy_catalog.items():
                if tool in catalog and isinstance(names, list):
                    catalog[tool].extend(name for name in names if isinstance(name, str) and name.strip())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass

    with Session(engine) as db:
        existing = db.scalars(select(Producer)).all()
        known = {(item.tool_name, item.name.casefold()) for item in existing}
        for tool_name, names in catalog.items():
            for name in names:
                clean_name = name.strip()
                key = (tool_name, clean_name.casefold())
                if clean_name and key not in known:
                    db.add(Producer(tool_name=tool_name, name=clean_name))
                    known.add(key)
        db.commit()


def load_producer_catalog():
    catalog = {tool: [] for tool in TOOLS_CONFIG}
    with Session(engine) as db:
        producers = db.scalars(select(Producer).order_by(Producer.name)).all()
        for producer in producers:
            catalog.setdefault(producer.tool_name, []).append(producer.name)
    return catalog


def save_producer(tool_name: str, producer_name: str):
    if tool_name not in TOOLS_CONFIG:
        raise ValueError("ابزار نامعتبر است")
    producer_name = producer_name.strip()
    if not producer_name:
        raise ValueError("نام سازنده الزامی است")

    with Session(engine) as db:
        existing = db.scalar(
            select(Producer).where(
                Producer.tool_name == tool_name,
                func.lower(Producer.name) == producer_name.casefold()
            )
        )
        if existing:
            saved_name = existing.name
        else:
            existing = Producer(tool_name=tool_name, name=producer_name)
            db.add(existing)
            db.commit()
            db.refresh(existing)
            saved_name = existing.name

        names = db.scalars(
            select(Producer.name).where(Producer.tool_name == tool_name).order_by(Producer.name)
        ).all()
        return saved_name, names

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
            statement = statement.where(
                WorkOrder.work_name.ilike(pattern) | WorkOrder.work_id.ilike(pattern)
            )
        orders = db.scalars(statement.limit(20 if query else 2)).unique().all()
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


@app.post("/work-orders/{work_id}/delete")
def delete_work_order(request: Request, work_id: str):
    if not get_current_user(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    with Session(engine) as db:
        order = db.scalar(
            select(WorkOrder).options(selectinload(WorkOrder.tools))
            .where(WorkOrder.work_id == work_id)
        )
        if order is not None:
            db.delete(order)
            db.commit()

    return RedirectResponse(url="/submissions", status_code=status.HTTP_303_SEE_OTHER)


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
        customer = order.customer
        tools = []
        for tool in order.tools:
            calibration_points = tool.calibration_points or []
            excel_row = [
                customer.name or "",
                customer.description or "",
                customer.national_id or "",
                customer.postal_id or "",
                customer.address or "",
                customer.phone_number or "",
                tool.selected_tool or "",
                tool.producer_name or "",
                tool.model or "",
                tool.tool_range or "",
                tool.resolution or "",
                tool.serial_no or "",
                tool.tool_location or "",
            ]
            # Keep a fixed 6-point layout so every copied tool has the same Excel columns.
            for index in range(6):
                point = calibration_points[index] if index < len(calibration_points) else {}
                excel_row.extend([
                    point.get("uuc", ""),
                    point.get("ref_rising", ""),
                    point.get("ref_falling", ""),
                ])
            tools.append({
                "id": tool.id, "selected_tool": "عمومی" if tool.selected_tool == "General" else tool.selected_tool, "producer_name": tool.producer_name,
                "model": tool.model, "range": tool.tool_range, "resolution": tool.resolution,
                "serial_no": tool.serial_no, "tool_location": tool.tool_location,
                "calibration_points": calibration_points,
                "excel_row": excel_row,
            })
        context = {
            "user": user, "lang": "fa", "text": TRANSLATIONS["fa"],
            "work_order": {
                "work_id": order.work_id, "work_name": order.work_name or "",
                "customer_name": customer.name, "customer_address": customer.address or "",
            },
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
