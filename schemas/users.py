from pydantic import BaseModel, Field, EmailStr, ConfigDict, UUID4

class UserBase(BaseModel):
    email: EmailStr | None = Field(default=None, description='Email of the user')
    is_active: bool = True

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int = Field(..., description='Id of the user')
    user_uuid: UUID4 = Field(..., description='Unique ID of the user')
    
    model_config = ConfigDict(from_attributes=True)

class EmailRequest(BaseModel):
    email: EmailStr
