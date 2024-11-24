from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from risk_assessment import main as risk_assessment_main

app = FastAPI()

# Указываем папку для шаблонов
templates = Jinja2Templates(directory="templates")

class CompanyRequest(BaseModel):
    company_name: str

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/check_company/", response_class=HTMLResponse)
async def check_company(request: Request, company_name: str = Form(None)):
    if not company_name:
        raise HTTPException(status_code=400, detail="Company name is required")
    
    # Получаем данные из основной логики
    result = await risk_assessment_main(company_name)
    
    if "error" in result:
        return templates.TemplateResponse("index.html", {"request": request, "error": result["error"]})

    # Декодируем риск уровень
    risk_level = result.get("risk_details", {}).get("risk_level", "Unknown")
    risk_description = {
        "Low": "The company is considered safe with minimal risks.",
        "Moderate": "The company has moderate risks. Further investigation is recommended.",
        "High": "The company has significant risks. Proceed with caution.",
        "Critical": "The company is extremely risky. Avoid business dealings."
    }.get(risk_level, "Risk level description unavailable.")
    
    # Подготовка данных для шаблона
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "company_name": result["company_data"]["name"],
            "registration_number": result["company_data"]["registration_number"],
            "status": result["company_data"]["status"],
            "risk_level": risk_level,
            "risk_description": risk_description,
            "directors": result["company_data"]["directors"],
            "sanctions_matches": result.get("sanctions_matches", [])
        }
    )
