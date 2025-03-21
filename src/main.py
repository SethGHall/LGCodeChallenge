from typing import Optional
from uuid import UUID
from fastapi import FastAPI, Path, Query, Response

from src.models.enums import Status
from src.models.card import Card
from src.models.invoice import InvoiceRequest
from src.config.settings import Settings
from src.services.invoice_service import InvoicingService
from src.services.health_check_service import HealthCheckService

app=FastAPI()
settings=Settings()
health_check_sevice = HealthCheckService(settings)
invoice_service = InvoicingService(settings)



@app.get("/health-check")
async def health_check(response: Response):
    response.status_code, json_response = await health_check_sevice.health_check()
    return json_response

     
@app.get("/invoice/{invoice_id}")
async def get_invoice(response: Response, invoice_id:UUID = Path(...)):
     response.status_code, json_response = await invoice_service.get_invoice(invoice_id)
     return json_response
