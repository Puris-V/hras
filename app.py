from fastapi import FastAPI, HTTPException
from pydantic import BaseModel  # Импортируем BaseModel для создания модели запроса
from risk_assessment import analyze_company


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
    try:
        result = analyze_company(request.company_name)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
