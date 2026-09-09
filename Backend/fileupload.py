from fastapi import FastAPI,UploadFile,File
from typing import Annotated

app=FastAPI()

#-----------------------------------------------------
# @app.post("/file/")
# async def file_upload(file:UploadFile=File(...)):
#     return{"File name":file.filename}
#-----------------------------------------------------


#-----------------------------------------------------
#Multiple file upload
#Ei part ta kaj kore nai, error age
@app.post("/file/")
async def multiple_file_upload(files:Annotated[list[UploadFile],File()]):
    return {"File name": [file.filename for file in files]}
