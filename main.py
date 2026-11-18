from fastapi import FastAPI

from crm.companies import router as companies_router
from crm.contacts import router as contacts_router
from crm.deals import router as deals_router


app = FastAPI(
    title="Atlant CRM API",
    version="0.1.0",
    description="A base CRM API for managing companies, contacts, and deals.",
)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {"message": "Atlant CRM API", "docs": "/docs"}


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(companies_router, prefix="/api/v1")
app.include_router(contacts_router, prefix="/api/v1")
app.include_router(deals_router, prefix="/api/v1")
