from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from risk_assessment import main as risk_assessment_main

app = FastAPI()

class CompanyRequest(BaseModel):
    company_name: str

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Risk Assessment Service</title>
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
            <style>
                body {
                    font-family: 'Roboto', sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 0;
                }
                header {
                    background-color: #4CAF50;
                    color: white;
                    padding: 1rem 0;
                    text-align: center;
                    font-size: 1.5rem;
                    font-weight: 500;
                }
                main {
                    max-width: 600px;
                    margin: 2rem auto;
                    background: white;
                    padding: 2rem;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }
                form {
                    display: flex;
                    flex-direction: column;
                    gap: 1rem;
                }
                label {
                    font-size: 1rem;
                    font-weight: 500;
                }
                input[type="text"] {
                    padding: 0.5rem;
                    font-size: 1rem;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                }
                button {
                    background-color: #4CAF50;
                    color: white;
                    padding: 0.75rem;
                    font-size: 1rem;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: 500;
                    transition: background-color 0.3s ease;
                }
                button:hover {
                    background-color: #45a049;
                }
                footer {
                    text-align: center;
                    margin-top: 2rem;
                    color: #777;
                    font-size: 0.9rem;
                }
            </style>
        </head>
        <body>
            <header>Risk Assessment Service</header>
            <main>
                <form action="/check_company/" method="post">
                    <label for="company_name">Enter Company Name:</label>
                    <input type="text" id="company_name" name="company_name" placeholder="e.g., RCB Finance" required>
                    <button type="submit">Check</button>
                </form>
            </main>
            <footer>
                &copy; 2024 Risk Assessment Service. All rights reserved.
            </footer>
        </body>
    </html>
    """

@app.post("/check_company/")
async def check_company(
    company_name: str = Form(None), 
    json_request: CompanyRequest = None
):
    if company_name:
        result = await risk_assessment_main(company_name)
        return {"status": "success", "data": result}

    if json_request:
        result = await risk_assessment_main(json_request.company_name)
        return {"status": "success", "data": result}

    raise HTTPException(status_code=400, detail="Invalid input format. Provide form-data or JSON.")
