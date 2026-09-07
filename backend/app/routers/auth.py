from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.user import UserRegisterRequest, UserLoginRequest, UserProfileResponse, UserUpdateRequest
import uuid
import jwt
from datetime import datetime, timedelta
from app.core.config import settings

router = APIRouter()

# In-memory mock DB for standalone local development & instant auth
MOCK_USERS_DB = {
    "arvykrane@dietsense.ai": {
        "id": "usr_99a8b7c6-d5e4-4f3a-2b1c-001122334455",
        "email": "arvykrane@dietsense.ai",
        "password": "password123",
        "full_name": "Arvy Krane",
        "age": 26,
        "gender": "male",
        "height_cm": 175.0,
        "weight_kg": 75.0,
        "goal": "lose_weight",
        "activity_level": "lightly_active",
        "daily_calorie_target": 1850,
        "is_solo_cook": True,
        "active_meal_frequency": "3_meals"
    }
}

def create_jwt_token(email: str) -> str:
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

@router.post("/register", response_model=UserProfileResponse)
async def register(req: UserRegisterRequest):
    if req.email in MOCK_USERS_DB:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Calculate initial BMR & TDEE
    bmr = 10 * req.weight_kg + 6.25 * req.height_cm - 5 * req.age + (5 if req.gender == "male" else -161)
    act_mult = 1.375 if req.activity_level == "lightly_active" else 1.2
    tdee = bmr * act_mult
    target_cal = round(tdee - 400 if req.goal == "lose_weight" else (tdee + 300 if req.goal == "gain_weight" else tdee))
    
    new_user = {
        "id": f"usr_{uuid.uuid4().hex[:12]}",
        "email": req.email,
        "password": req.password,
        "full_name": req.full_name,
        "age": req.age,
        "gender": req.gender.value,
        "height_cm": req.height_cm,
        "weight_kg": req.weight_kg,
        "goal": req.goal.value,
        "activity_level": req.activity_level.value,
        "daily_calorie_target": target_cal,
        "is_solo_cook": True,
        "active_meal_frequency": "3_meals"
    }
    MOCK_USERS_DB[req.email] = new_user
    token = create_jwt_token(req.email)
    
    return UserProfileResponse(**new_user, token=token)

@router.post("/login", response_model=UserProfileResponse)
async def login(req: UserLoginRequest):
    user = MOCK_USERS_DB.get(req.email)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    token = create_jwt_token(req.email)
    return UserProfileResponse(**user, token=token)

@router.get("/me", response_model=UserProfileResponse)
async def get_current_user(email: str = "arvykrane@dietsense.ai"):
    user = MOCK_USERS_DB.get(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfileResponse(**user)

@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(req: UserUpdateRequest, email: str = "arvykrane@dietsense.ai"):
    user = MOCK_USERS_DB.get(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, val in req.model_dump(exclude_unset=True).items():
        if val is not None:
            user[key] = val.value if hasattr(val, "value") else val
            
    # Recalculate TDEE if biometrics changed
    bmr = 10 * user["weight_kg"] + 6.25 * user["height_cm"] - 5 * user["age"] + (5 if user["gender"] == "male" else -161)
    act_mult = 1.375 if user["activity_level"] == "lightly_active" else 1.2
    tdee = bmr * act_mult
    user["daily_calorie_target"] = round(tdee - 400 if user["goal"] == "lose_weight" else (tdee + 300 if user["goal"] == "gain_weight" else tdee))
    
    return UserProfileResponse(**user)
