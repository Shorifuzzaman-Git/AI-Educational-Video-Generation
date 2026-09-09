#Pydantic is a pyhton library for data parsing and validation 
#using python type annotation

from fastapi import FastAPI
from pydantic import BaseModel,EmailStr,conint,constr,field_validator

app=FastAPI()

class User(BaseModel):
    name: constr(pattern=r'^[A-Za-z ]+$') #valid name
    age:conint(gt=0)
    email:EmailStr # valid email

    # @field_validator('name')
    # def username_must_not_contain_space(cls,v):
    #     if ' ' in v:
    #         raise ValueError("User name must not contain space")
    #     return v

@app.post("/register/")
async def register_user(user:User):
    return {"Name":user.name,"Age":user.age,"Email":user.email}
