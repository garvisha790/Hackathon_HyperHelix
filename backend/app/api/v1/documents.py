import asyncio
import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy import select, func

from app.dependencies import CurrentUser, TenantId, DB, require_role
from app.models.document import Document
from app.schemas.document import DocumentUploadResponse, DocumentResponse, DocumentListResponse
from app.utils.s3 import generate_presigned_upload_url, upload_to_s3, ALLOWED_CONTENT_TYPES
from app.services.pipeline_service import process_document
from app.middleware.audit import log_action
from app.database import async_session

logger = logging.getLogger(__name__)
router = APIRouter()

_LOG_FILE = __import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "pipeline.log"

def _log(msg: str):
    logger.info(msg)
    try:
        from datetime import datetime as _dt
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{_dt.now().strftime('%H:%M:%S')} {msg}\n")
    except Exception:
        pass

ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}


def _content_type_for(filename: str) -> tuple[str, str]:
    """Derive content_type and extension from filename."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    mapping = {"pdf": "application/pdf", "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}
    ct = mapping.get(ext)
    return ct, ext


@router.post("/upload")
async def upload_document_file(
    file: UploadFile = File(...),
    document_type: str = Form("invoice"),
    user: CurrentUser = None,
    tenant_id: TenantId = None,
    db: DB = None,
):
    """Single-step upload: receive file, push to S3, start processing."""
    content_type, ext = _content_type_for(file.filename or "file.pdf")
    if not content_type or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type. Allowed: {list(ALLOWED_EXTENSIONS)}")

    s3_key = f"tenants/{tenant_id}/documents/{uuid.uuid4()}.{ext}"
    file_bytes = await file.read()

    _log(f"[UPLOAD] Uploading {len(file_bytes)} bytes to S3 key={s3_key} ...")
    await asyncio.to_thread(upload_to_s3, s3_key, file_bytes, content_type)
    _log(f"[UPLOAD] S3 upload done: {s3_key} ({len(file_bytes)} bytes)")

    doc = Document(
        tenant_id=tenant_id,
        uploaded_by=user.id,
        file_name=file.filename,
        s3_key=s3_key,
        file_type=ext,
        document_type=document_type,
        status="UPLOADED",
    )
    db.add(doc)
    await db.flush()
    await log_action(db, tenant_id, user.id, "document.upload", "document", doc.id, {"file_name": file.filename})
    await db.commit()

    doc_id = doc.id
    doc_name = file.filename

    _log(f"[UPLOAD] Document {doc_id} created, running pipeline INLINE for {doc_name}")
    try:
        async with async_session() as pipeline_session:
            await process_document(pipeline_session, doc_id, tenant_id)
        _log(f"[UPLOAD] Pipeline finished for {doc_id}")
    except Exception as e:
        _log(f"[UPLOAD] Pipeline error for {doc_id}: {type(e).__name__}: {e}")

    async with async_session() as fresh:
        result = await fresh.execute(select(Document).where(Document.id == doc_id))
        final_doc = result.scalar_one()
        final_status = final_doc.status

    _log(f"[UPLOAD] Final status for {doc_id}: {final_status}")
    return {"id": str(doc_id), "status": final_status, "file_name": doc_name}


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    file_name: str,
    content_type: str,
    document_type: str = "invoice",
    user: CurrentUser = None,
    tenant_id: TenantId = None,
    db: DB = None,
):
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, f"Unsupported file type. Allowed: {list(ALLOWED_CONTENT_TYPES.keys())}")

    upload_url, s3_key = generate_presigned_upload_url(str(tenant_id), file_name, content_type)

    doc = Document(
        tenant_id=tenant_id,
        uploaded_by=user.id,
        file_name=file_name,
        s3_key=s3_key,
        file_type=ALLOWED_CONTENT_TYPES[content_type],
        document_type=document_type,
        status="UPLOADED",
    )
    db.add(doc)
    await db.flush()

    await log_action(db, tenant_id, user.id, "document.upload", "document", doc.id, {"file_name": file_name})
    return DocumentUploadResponse(id=str(doc.id), upload_url=upload_url, s3_key=s3_key)


@router.post("/{document_id}/process")
async def trigger_processing(
    document_id: uuid.UUID,
    user: CurrentUser = None,
    tenant_id: TenantId = None,
    db: DB = None,
):
    """Called by the frontend after the file has been uploaded to S3."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
            Document.deleted_at.is_(None),
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.status not in ("UPLOADED", "FAILED", "PROCESSING"):
        raise HTTPException(400, f"Document already in status {doc.status}")

    _log(f"[PROCESS] Running pipeline for {document_id} ({doc.file_name})")
    async with async_session() as pipeline_session:
        await process_document(pipeline_session, doc.id, tenant_id)
    _log(f"[PROCESS] Pipeline finished for {document_id}")

    await db.refresh(doc)
    return {"status": doc.status, "document_id": str(document_id)}


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    status: str | None = None,
    document_type: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    tenant_id: TenantId = None,
    db: DB = None,
):
    query = select(Document).where(Document.tenant_id == tenant_id, Document.deleted_at.is_(None))
    count_query = select(func.count(Document.id)).where(Document.tenant_id == tenant_id, Document.deleted_at.is_(None))

    if status:
        query = query.where(Document.status == status)
        count_query = count_query.where(Document.status == status)
    if document_type:
        query = query.where(Document.document_type == document_type)
        count_query = count_query.where(Document.document_type == document_type)

    query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    total = await db.execute(count_query)

    docs = [
        DocumentResponse(
            id=str(d.id), file_name=d.file_name, file_type=d.file_type,
            document_type=d.document_type, status=d.status,
            uploaded_by=str(d.uploaded_by), created_at=d.created_at, updated_at=d.updated_at,
        )
        for d in result.scalars().all()
    ]

    return DocumentListResponse(documents=docs, total=total.scalar() or 0)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: uuid.UUID, tenant_id: TenantId = None, db: DB = None):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.tenant_id == tenant_id, Document.deleted_at.is_(None)
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    return DocumentResponse(
        id=str(doc.id), file_name=doc.file_name, file_type=doc.file_type,
        document_type=doc.document_type, status=doc.status,
        uploaded_by=str(doc.uploaded_by), created_at=doc.created_at, updated_at=doc.updated_at,
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    user=Depends(require_role("owner")),
    db: DB = None,
):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.tenant_id == user.tenant_id, Document.deleted_at.is_(None)
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    doc.deleted_at = datetime.utcnow()
    await log_action(db, user.tenant_id, user.id, "document.delete", "document", doc.id)
    return {"status": "deleted"}
