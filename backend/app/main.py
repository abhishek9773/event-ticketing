from fastapi import FastAPI
from app.database import engine, Base, SessionLocal
from app.api.v1 import login, events, tickets
from app.models import User
from app import schemas, crud
from sqlalchemy.orm import Session 

def create_db_and_tables():
    Base.metadata.create_all(bind=engine)
    
def create_initial_admin(db: Session):
    # Check if any user exists
    if db.query(User).count() == 0:
        print("--- Creating initial Admin user (username: admin, password: admin123, email: admin@example.com) ---") 
        try:
            admin_data = schemas.UserCreate(
                username="admin", 
                password="admin123",
                email="admin@example.com"
            )
            crud.create_user(db, admin_data, is_admin=True)
        except Exception as e:
            print(f"Failed to create initial admin: {e}")

app = FastAPI(
    title="Event Ticketing API v1.0",
    description="Scalable REST API with Authentication & Role-Based Access for intership.",
    version="v1.0",
    docs_url="/docs", # Automatic Swagger documentation
    redoc_url="/redoc"
)

@app.on_event("startup")
def on_startup():
    """Run database initialization and create admin on application start."""
    print("Initializing Database...")
    create_db_and_tables()
    
    db = SessionLocal()
    create_initial_admin(db)
    db.close()
    print("Initialization complete.")


app.include_router(login.router, prefix="/v1")
app.include_router(events.router, prefix="/v1")
app.include_router(tickets.router, prefix="/v1")


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the Event Ticketing API v1.0. Check /docs for endpoints."}