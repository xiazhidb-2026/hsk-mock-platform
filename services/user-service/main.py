"""
HSK Mock Platform - User Service
设备管理、订阅管理
"""

import os
import uuid
import json
from datetime import datetime, date
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, SmallInteger, Boolean, Integer, Date, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ============== 配置 ==============
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hskuser:hsk123456@localhost:5432/hskdb")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ============== 数据库模型 ==============
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Device(Base):
    __tablename__ = "devices"
    
    uuid = Column(String(36), primary_key=True)
    nickname = Column(String(50))
    device_info = Column(JSONB)
    native_language = Column(String(20), default="en")
    target_level = Column(SmallInteger)
    is_subscriber = Column(Boolean, default=False)
    subscriber_level = Column(String(20))
    free_exam_remaining = Column(SmallInteger, default=3)
    last_free_reset = Column(Date, default=date.today)
    total_exams = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)


class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_uuid = Column(String(36), nullable=False)
    plan_type = Column(String(20), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="active")
    payment_method = Column(String(50))
    amount = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============== Pydantic模型 ==============
class DeviceRegisterRequest(BaseModel):
    device_info: Optional[dict] = None
    nickname: Optional[str] = None
    native_language: Optional[str] = "en"
    target_level: Optional[int] = None


class DeviceResponse(BaseModel):
    uuid: str
    nickname: Optional[str]
    native_language: str
    target_level: Optional[int]
    is_subscriber: bool
    free_exam_remaining: int
    total_exams: int


class SubscriptionCreateRequest(BaseModel):
    device_uuid: str
    plan_type: str  # monthly / yearly
    payment_method: str


class SubscriptionResponse(BaseModel):
    id: str
    plan_type: str
    start_date: datetime
    end_date: datetime
    status: str
    amount: int


class ExamQuotaResponse(BaseModel):
    can_exam: bool
    remaining: int
    is_subscriber: bool
    reset_date: Optional[date]


# ============== 依赖 ==============
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============== 应用 ==============
app = FastAPI(title="HSK User Service", version="1.0.0")


# ============== 设备API ==============
@app.post("/device/register", response_model=DeviceResponse)
def register_device(request: DeviceRegisterRequest, db: Session = Depends(get_db)):
    """注册新设备，返回UUID"""
    device_uuid = str(uuid.uuid4())
    
    device = Device(
        uuid=device_uuid,
        nickname=request.nickname,
        device_info=request.device_info,
        native_language=request.native_language or "en",
        target_level=request.target_level,
        free_exam_remaining=3,
        last_free_reset=date.today()
    )
    
    db.add(device)
    db.commit()
    db.refresh(device)
    
    return DeviceResponse(
        uuid=device.uuid,
        nickname=device.nickname,
        native_language=device.native_language,
        target_level=device.target_level,
        is_subscriber=device.is_subscriber,
        free_exam_remaining=device.free_exam_remaining,
        total_exams=device.total_exams
    )


@app.get("/device/{device_uuid}", response_model=DeviceResponse)
def get_device(device_uuid: str, db: Session = Depends(get_db)):
    """获取设备信息"""
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # 检查是否需要重置免费次数
    today = date.today()
    if device.last_free_reset != today:
        device.free_exam_remaining = 3
        device.last_free_reset = today
        db.commit()
    
    return DeviceResponse(
        uuid=device.uuid,
        nickname=device.nickname,
        native_language=device.native_language,
        target_level=device.target_level,
        is_subscriber=device.is_subscriber,
        free_exam_remaining=device.free_exam_remaining,
        total_exams=device.total_exams
    )


@app.put("/device/{device_uuid}", response_model=DeviceResponse)
def update_device(device_uuid: str, request: DeviceRegisterRequest, db: Session = Depends(get_db)):
    """更新设备信息"""
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if request.nickname:
        device.nickname = request.nickname
    if request.native_language:
        device.native_language = request.native_language
    if request.target_level:
        device.target_level = request.target_level
    
    device.last_active_at = datetime.utcnow()
    db.commit()
    db.refresh(device)
    
    return DeviceResponse(
        uuid=device.uuid,
        nickname=device.nickname,
        native_language=device.native_language,
        target_level=device.target_level,
        is_subscriber=device.is_subscriber,
        free_exam_remaining=device.free_exam_remaining,
        total_exams=device.total_exams
    )


# ============== 考试配额API ==============
@app.get("/exam/quota/{device_uuid}", response_model=ExamQuotaResponse)
def check_exam_quota(device_uuid: str, db: Session = Depends(get_db)):
    """检查考试配额"""
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # 检查订阅状态
    subscription = db.query(Subscription).filter(
        Subscription.device_uuid == device_uuid,
        Subscription.status == "active",
        Subscription.end_date > datetime.utcnow()
    ).first()
    
    is_subscriber = subscription is not None
    
    # 检查免费次数
    today = date.today()
    if device.last_free_reset != today:
        device.free_exam_remaining = 3
        device.last_free_reset = today
        db.commit()
    
    can_exam = is_subscriber or device.free_exam_remaining > 0
    
    # 计算下月重置日期
    if today.month == 12:
        reset_date = date(today.year + 1, 1, 1)
    else:
        reset_date = date(today.year, today.month + 1, 1)
    
    return ExamQuotaResponse(
        can_exam=can_exam,
        remaining=device.free_exam_remaining if not is_subscriber else -1,
        is_subscriber=is_subscriber,
        reset_date=reset_date if not is_subscriber else None
    )


@app.post("/exam/use-quota/{device_uuid}")
def use_exam_quota(device_uuid: str, db: Session = Depends(get_db)):
    """使用一次考试配额"""
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # 检查订阅
    subscription = db.query(Subscription).filter(
        Subscription.device_uuid == device_uuid,
        Subscription.status == "active",
        Subscription.end_date > datetime.utcnow()
    ).first()
    
    if subscription:
        # 订阅用户不消耗免费次数
        device.total_exams += 1
        device.last_active_at = datetime.utcnow()
        db.commit()
        return {"success": True, "message": "Using subscription"}
    
    # 使用免费次数
    if device.free_exam_remaining <= 0:
        raise HTTPException(status_code=403, detail="No exam quota remaining")
    
    device.free_exam_remaining -= 1
    device.total_exams += 1
    device.last_active_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "remaining": device.free_exam_remaining}


# ============== 订阅API ==============
@app.post("/subscription/create", response_model=SubscriptionResponse)
def create_subscription(request: SubscriptionCreateRequest, db: Session = Depends(get_db)):
    """创建订阅"""
    device = db.query(Device).filter(Device.uuid == request.device_uuid).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # 计算订阅时长
    now = datetime.utcnow()
    if request.plan_type == "monthly":
        from datetime import timedelta
        end_date = now + timedelta(days=30)
        amount = 3000  # 30元
    elif request.plan_type == "yearly":
        from datetime import timedelta
        end_date = now + timedelta(days=365)
        amount = 30000  # 300元
    else:
        raise HTTPException(status_code=400, detail="Invalid plan type")
    
    subscription = Subscription(
        device_uuid=request.device_uuid,
        plan_type=request.plan_type,
        start_date=now,
        end_date=end_date,
        payment_method=request.payment_method,
        amount=amount,
        status="active"
    )
    
    # 更新设备订阅状态
    device.is_subscriber = True
    device.subscriber_level = "gold" if request.plan_type == "yearly" else "silver"
    
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    return SubscriptionResponse(
        id=subscription.id,
        plan_type=subscription.plan_type,
        start_date=subscription.start_date,
        end_date=subscription.end_date,
        status=subscription.status,
        amount=subscription.amount
    )


@app.get("/subscription/{device_uuid}", response_model=SubscriptionResponse)
def get_subscription(device_uuid: str, db: Session = Depends(get_db)):
    """获取当前订阅状态"""
    subscription = db.query(Subscription).filter(
        Subscription.device_uuid == device_uuid,
        Subscription.status == "active",
        Subscription.end_date > datetime.utcnow()
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription")
    
    return SubscriptionResponse(
        id=subscription.id,
        plan_type=subscription.plan_type,
        start_date=subscription.start_date,
        end_date=subscription.end_date,
        status=subscription.status,
        amount=subscription.amount
    )


# ============== 健康检查 ==============
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "user-service"}


# ============== 启动 ==============
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
