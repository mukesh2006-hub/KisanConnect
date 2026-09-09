from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Product, Order
from .schemas import ProductCreate, ProductOut, OrderCreate, OrderOut, PriceRequest, PriceResponse, RouteRequest, RouteResponse
from .ml.price_engine import recommend_price
from .routing.route_engine import optimize_route

Base.metadata.create_all(bind=engine)

app = FastAPI(title="KisanConnect API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"project": "KisanConnect", "problem_statement": "SIH26033"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ai/predict-price", response_model=PriceResponse)
def predict_price(payload: PriceRequest):
    return recommend_price(
        crop=payload.crop,
        market=payload.market,
        quality=payload.quality,
        quantity=payload.quantity,
    )

@app.post("/products", response_model=ProductOut)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@app.get("/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).filter(Product.status == "AVAILABLE").order_by(Product.created_at.desc()).all()

@app.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/orders", response_model=OrderOut)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if payload.quantity <= 0 or payload.quantity > product.quantity:
        raise HTTPException(status_code=400, detail="Invalid quantity")
    order = Order(
        product_id=product.id,
        buyer_name=payload.buyer_name,
        quantity=payload.quantity,
        total_price=payload.quantity * product.price_per_kg,
        delivery_lat=payload.delivery_lat,
        delivery_lon=payload.delivery_lon,
        status="PLACED",
    )
    product.quantity -= payload.quantity
    if product.quantity == 0:
        product.status = "SOLD_OUT"
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@app.post("/route/optimize", response_model=RouteResponse)
def route(payload: RouteRequest):
    try:
        return optimize_route(
            payload.stops,
            payload.vehicle_capacity_kg
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )