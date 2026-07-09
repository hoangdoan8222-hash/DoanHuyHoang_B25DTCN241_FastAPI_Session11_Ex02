from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import create_engine, Column, Integer, String, Double
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime

DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/ecommerce_db"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


class SmartHomePlan(Base):
    __tablename__ = "smart_home_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_code = Column(String(50), unique=True, nullable=False)
    plan_name = Column(String(255), nullable=False)
    device_quantity = Column(Integer, nullable=False)
    price = Column(Double, nullable=False)


Base.metadata.create_all(bind=engine)


class SmartHomePlanCreate(BaseModel):
    plan_code: str
    plan_name: str = Field(min_length=1)
    device_quantity: int = Field(gt=0)
    price: float = Field(gt=0)


class SmartHomePlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_code: str
    plan_name: str
    device_quantity: int
    price: float


app = FastAPI()


def response(status_code, message, error, data, path):
    return {
        "statusCode": status_code,
        "message": message,
        "error": error,
        "data": data,
        "path": path,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.post("/smart-home-plans", status_code=status.HTTP_201_CREATED)
def create_plan(plan: SmartHomePlanCreate, request: Request):
    db = SessionLocal()

    try:
        new_plan = SmartHomePlan(
            plan_code=plan.plan_code,
            plan_name=plan.plan_name,
            device_quantity=plan.device_quantity,
            price=plan.price
        )

        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)

        return response(
            201,
            "Thêm gói thiết bị thành công",
            None,
            SmartHomePlanResponse.model_validate(new_plan).model_dump(),
            str(request.url.path)
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Plan code already exists"
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database Error"
        )

    finally:
        db.close()


@app.get("/smart-home-plans")
def get_all_plans(request: Request):
    db = SessionLocal()

    try:
        plans = db.query(SmartHomePlan).all()

        data = [
            SmartHomePlanResponse.model_validate(plan).model_dump()
            for plan in plans
        ]

        return response(
            200,
            "Lấy danh sách thành công",
            None,
            data,
            str(request.url.path)
        )

    finally:
        db.close()


@app.get("/smart-home-plans/{plan_id}")
def get_plan(plan_id: int, request: Request):
    db = SessionLocal()

    try:
        plan = db.query(SmartHomePlan).filter(
            SmartHomePlan.id == plan_id
        ).first()

        if plan is None:
            raise HTTPException(
                status_code=404,
                detail="Plan not found"
            )

        return response(
            200,
            "Lấy thông tin gói thiết bị thành công",
            None,
            SmartHomePlanResponse.model_validate(plan).model_dump(),
            str(request.url.path)
        )

    finally:
        db.close()