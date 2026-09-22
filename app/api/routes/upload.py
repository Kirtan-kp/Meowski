from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from app.api.dependencies import get_vector_store , get_session_service , get_bm25_index_service, get_retrieval_cache_service
from app.services.upload_service import UploadService
from app.db.databse import get_db
from app.schemas.documents import DocumentResponse

router = APIRouter()

def get_upload_service(vector_store = Depends(get_vector_store) , db = Depends(get_db) ,
                       session_service = Depends(get_session_service) , bm25_index_service = Depends(get_bm25_index_service) ,
                       retrieval_cache_service = Depends(get_retrieval_cache_service)):
    return UploadService(vector_store , db , session_service , bm25_index_service , retrieval_cache_service)

@router.post("/documents")
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

@router.get(
    "/documents",
    response_model=list[DocumentResponse],
)
def list_documents(
    user_id: str,
    session_id: str,
    upload_service: UploadService = Depends(get_upload_service),
):
    try:
        documents = upload_service.list_documents(
            user_id=user_id,
            session_id=session_id,
        )

        return [
            DocumentResponse(
                document_id=document.id,
                filename=document.filename,
                status=document.status,
                scope=document.scope,
                created_at=document.created_at,
                expires_at=document.expires_at,
            )
            for document in documents
        ]

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

@router.delete("/documents/{document_id}")
def delete_document(
    document_id: str,
    user_id: str,
    session_id: str,
    upload_service: UploadService = Depends(get_upload_service),
):
    try:
        deleted = upload_service.delete_document(
            document_id=document_id,
            user_id=user_id,
            session_id=session_id,
        )

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Document not found",
            )

        return {
            "message": "Document deleted successfully"
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )