from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from enum import Enum

class GoalType(str, Enum):
    lose_weight = "lose_weight"
    maintain_weight = "maintain_weight"
    gain_weight = "gain_weight"

class ActivityLevel(str, Enum):
    sedentary = "sedentary"
    lightly_active = "lightly_active"
    moderately_active = "moderately_active"
    very_active = "very_active"
    extra_active = "extra_active"

class GenderType(str, Enum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str
    age: int = Field(ge=10, le=120, default=26)
    gender: GenderType = GenderType.male
    height_cm: float = Field(gt=0, default=175.0)
    weight_kg: float = Field(gt=0, default=75.0)
    goal: GoalType = GoalType.lose_weight
    activity_level: ActivityLevel = ActivityLevel.lightly_active

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    goal: str
    activity_level: str
    daily_calorie_target: int
    is_solo_cook: bool = True
    active_meal_frequency: str = "3_meals"
    token: Optional[str] = None

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[GenderType] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    goal: Optional[GoalType] = None
    activity_level: Optional[ActivityLevel] = None
    is_solo_cook: Optional[bool] = None
    active_meal_frequency: Optional[str] = None
