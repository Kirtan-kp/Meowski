from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from app.api.dependencies import get_vector_store , get_session_service , get_bm25_index_service, get_retrieval_cache_service, get_rate_limit_service
from app.services.upload_service import UploadService
from app.db.databse import get_db
from app.schemas.documents import DocumentResponse
from app.core.config import settings
from app.services.rate_limit_service import RateLimitService
from app.services.session_service import SessionError, SessionNotFoundError
from app.ingestion.validators import FileTooLargeError

router = APIRouter()

def get_upload_service(vector_store = Depends(get_vector_store) , db = Depends(get_db) ,
                       session_service = Depends(get_session_service) , bm25_index_service = Depends(get_bm25_index_service) ,
                       retrieval_cache_service = Depends(get_retrieval_cache_service)):
    return UploadService(vector_store , db , session_service , bm25_index_service , retrieval_cache_service)

@router.post("/documents")
def upload(file : UploadFile = File(...) , user_id : str = Form(...) ,
           session_id : str = Form(...) , upload_service : UploadService = Depends(get_upload_service),
           rate_limits: RateLimitService = Depends(get_rate_limit_service)):
    session_allowed = rate_limits.is_allowed(
        key=f"session:upload:{rate_limits.scoped_key(user_id, session_id)}",
        limit=settings.session_rate_limit_requests,
        window_seconds=settings.session_rate_limit_window_seconds,
    )
    if not session_allowed:
        raise HTTPException(status_code=429, detail="Session rate limit exceeded")

    try:
        chunks = upload_service.upload(file = file , user_id = user_id , session_id = session_id)

        return {"message" : "File uploaded successfully" , "chunks" : len(chunks)}

    except FileTooLargeError as exc:
        raise HTTPException(status_code = 413 , detail = str(exc))

    except SessionError as exc:
        raise HTTPException(
            status_code = 404 if isinstance(exc, SessionNotFoundError) else 410,
            detail = str(exc),
        )

    except ValueError as exc:
        raise HTTPException(status_code = 400 , detail = str(exc))

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