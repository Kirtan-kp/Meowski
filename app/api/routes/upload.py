from fastapi import APIRouter, Depends, File, Form, UploadFile
from app.api.dependencies import get_vector_store
from app.services.upload_service import UploadService

router = APIRouter()

def get_upload_service(vector_store = Depends(get_vector_store)):
    return UploadService(vector_store)

@router.post("/upload")
def upload(file : UploadFile = File(...) , user_id : str = Form(...) ,
           session_id : str = Form(...) , upload_service : UploadService = Depends(get_upload_service)):
    
    chunks = upload_service.upload(file = file , user_id = user_id , session_id = session_id)

    return {"message" : "File uploaded successfully" , "chunks" : len(chunks)}