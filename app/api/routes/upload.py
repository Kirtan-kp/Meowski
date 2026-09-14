from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from app.api.dependencies import get_vector_store , get_session_service
from app.services.upload_service import UploadService
from app.db.databse import get_db

router = APIRouter()

def get_upload_service(vector_store = Depends(get_vector_store) , db = Depends(get_db) , session_service = Depends(get_session_service)):
    return UploadService(vector_store , db , session_service)

@router.post("/upload")
def upload(file : UploadFile = File(...) , user_id : str = Form(...) ,
           session_id : str = Form(...) , upload_service : UploadService = Depends(get_upload_service)):
    try:
        chunks = upload_service.upload(file = file , user_id = user_id , session_id = session_id)

        return {"message" : "File uploaded successfully" , "chunks" : len(chunks)}

    except ValueError as exc:
        message = str(exc)

        if "10 MB" in message:
            raise HTTPException(status_code = 413 , detail = message)

        if "Session not found" in message:
            raise HTTPException(status_code = 404 , detail = message)
        
        raise HTTPException(status_code = 400 , detail = message)