from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from risk_assessment import main as risk_assessment_main

app = FastAPI()

# Определение модели данных
class CompanyRequest(BaseModel):
    company_name: str

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html>
        <head>
            <title>Risk Assessment Service</title>
        </head>
        <body>
            <h1>Risk Assessment Service</h1>
            <form action="/check_company/" method="post">
                <label for="company_name">Enter Company Name:</label>
                <input type="text" id="company_name" name="company_name" required>
                <button type="submit">Check</button>
            </form>
        </body>
    </html>
    """

@app.post("/check_company/")
async def check_company(
    company_name: str = Form(None),  # Для form-data
    json_request: CompanyRequest = None,  # Для JSON
):
    if company_name:
        result = await risk_assessment_main(company_name)  # Асинхронный вызов
        return {"status": "success", "data": result}

    if json_request:
        result = await risk_assessment_main(json_request.company_name)  # Асинхронный вызов
        return {"status": "success", "data": result}

    raise HTTPException(status_code=400, detail="Invalid input format. Provide form-data or JSON.")
