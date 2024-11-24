from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from risk_assessment import main as risk_assessment_main

app = FastAPI()
templates = Jinja2Templates(directory="templates")  # Директория для шаблонов

class CompanyRequest(BaseModel):
    company_name: str

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/check_company/", response_class=HTMLResponse)
async def check_company(request: Request, company_name: str = Form(None)):
    if not company_name:
        raise HTTPException(status_code=400, detail="Company name is required.")
    
    result = await risk_assessment_main(company_name)
    
    if "error" in result:
        return templates.TemplateResponse("error.html", {"request": request, "error": result["error"]})
    
    return templates.TemplateResponse("result.html", {"request": request, "result": result})
