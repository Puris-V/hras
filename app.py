from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from risk_assessment import main as risk_assessment_main  # Импорт вашей логики

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

# Обработка формы
@app.post("/check_company/", response_class=HTMLResponse)
async def check_company(company_name: str = Form(...)):
    result = risk_assessment_main(company_name)
    return f"""
    <html>
        <head>
            <title>Risk Assessment Service</title>
        </head>
        <body>
            <h1>Risk Assessment Service</h1>
            <h2>Results for {company_name}:</h2>
            <pre>{result}</pre>
            <a href="/">Go Back</a>
        </body>
    </html>
    """
	