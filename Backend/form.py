from fastapi import FastAPI,Form

app=FastAPI()

@app.post("/login/")
async def login(user_name:str=Form(...),password:str=Form(...)):
    return{"User name":user_name,"Message":"Login seccessful"}