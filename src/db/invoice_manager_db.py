from functools import wraps
from typing import Optional, List, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy import exists, select
from src.db.invoice_db_model import InvoiceDB, CustomerDB
from src.config.settings import Settings
from src.models.enums import Status
from src.models.invoice import InvoiceRequest

settings = Settings()

url = f'mysql+mysqlconnector://{settings.db_user}:{settings.db_password}@{settings.db_url}'  
engine = create_engine(url, echo=True)

# Create a sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Decorator to automatically manage the database session
def with_db_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create session
        db = SessionLocal()
        try:
            return func(*args, db=db, **kwargs)
        finally:
            db.close()
    return wrapper


@with_db_session
def db_health_check(db=None):
    print(f">>>{url}")
    try:
        statement = exists(select(1)).select()
        check  = db.execute(statement).scalar()
        return (200, {"status": "UP"}) if check else (502, {"status": "DOWN"})
    except OperationalError as error:
        # If there is a connection issue or any other operational error, catch it and return an error message
        print(f"DATABASE DOWN ERROR: {error}")
        return (502, {"status": "DOWN"})


@with_db_session 
def get_joined_invoice_customer_by_id(invoice_id: str, db=None):
    """
    Fetch full invoice details by ID, including all invoice and customer fields.
    """
    invoice_customer = db.query(InvoiceDB, CustomerDB).join(
        CustomerDB, CustomerDB.customer_id == InvoiceDB.customer_id
    ).filter(InvoiceDB.id == invoice_id).first() 
    
    return invoice_customer


@with_db_session
def get_all_invoices(invoice_status: Optional[Status] = None, db=None) -> List[Tuple[InvoiceDB, CustomerDB]]:
    """
    Fetch all invoices (optionally filtered by invoice_status), with customer details.
    Returns a list of tuples (InvoiceDB, CustomerDB)
    """
    query = db.query(InvoiceDB, CustomerDB).join(
        CustomerDB, CustomerDB.customer_id == InvoiceDB.customer_id
    )

    if invoice_status:
        query = query.filter(InvoiceDB.invoice_status == invoice_status)

    return query.all()


@with_db_session
def save_invoice(invoice_request: InvoiceRequest, invoice_id: str, db=None) -> InvoiceDB:
    try:
        invoice_db = InvoiceDB(
            id=invoice_id,
            job_description=invoice_request.job_description,
            customer_id=invoice_request.customer_id,
            amount=float(invoice_request.amount) # Ensure float, because it might be str
        )
        db.add(invoice_db)
        db.commit()
        db.refresh(invoice_db)
        return invoice_db
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error saving invoice: {e}")
        raise