from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from risk_assessment import main as risk_assessment_main


app = FastAPI()

# Главная страница
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
class CompanyRequest(BaseModel):
    company_name: str
    
@app.post("/check_company/")
async def check_company(request: CompanyRequest):
    company_name = request.company_name
    result = risk_assessment_main(company_name)  # Если вы используете основную функцию main
    return {"status": "success", "data": result}

