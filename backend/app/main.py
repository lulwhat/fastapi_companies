from fastapi import FastAPI

from api.v1.routers import buildings, categories, companies, export


app = FastAPI(
    title="Companies catalogue",
    description="Companies catalogue API Documentation",
    version="1.0.0",
    root_path="/api/v1",
    docs_url="/docs",
)

app.include_router(buildings.router)
app.include_router(categories.router)
app.include_router(companies.router)
app.include_router(export.router)
