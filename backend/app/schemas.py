from pydantic import BaseModel, Field

class PriceRequest(BaseModel):
    crop: str = "Tomato"
    market: str = "Kolar"
    quality: str = "Grade A"
    quantity: float = Field(gt=0)

class PriceResponse(BaseModel):
    recommended_price: float
    min_price: float
    max_price: float
    current_mandi_price: float
    predicted_price: float
    demand: str
    trend_percent: float
    explanation: list[str]
    model: str

class ProductCreate(BaseModel):
    farmer_name: str
    crop: str = "Tomato"
    quantity: float = Field(gt=0)
    price_per_kg: float = Field(gt=0)
    quality: str = "Grade A"
    location: str
    latitude: float
    longitude: float

class ProductOut(ProductCreate):
    id: int
    status: str

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    product_id: int
    buyer_name: str
    quantity: float = Field(gt=0)
    delivery_lat: float
    delivery_lon: float

class OrderOut(OrderCreate):
    id: int
    total_price: float
    status: str

    class Config:
        from_attributes = True

class Stop(BaseModel):
    name: str
    lat: float
    lon: float
    pickup_kg: float = 0
    delivery_kg: float = 0

class RouteRequest(BaseModel):
    stops: list[Stop]
    vehicle_capacity_kg: float = Field(default=1000, gt=0)

class RouteResponse(BaseModel):
    ordered_stops: list[Stop]
    total_distance_km: float
    estimated_minutes: int
    estimated_fuel_cost: float
    method: str
