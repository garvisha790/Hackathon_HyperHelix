import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.dependencies import CurrentUser, TenantId, DB, require_role
from app.models.document import Document
from app.schemas.document import DocumentUploadResponse, DocumentResponse, DocumentListResponse
from app.utils.s3 import generate_presigned_upload_url, ALLOWED_CONTENT_TYPES
from app.services.pipeline_service import process_document
from app.middleware.audit import log_action
from app.database import async_session

router = APIRouter()


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    file_name: str,
    content_type: str,
    document_type: str = "invoice",
    user: CurrentUser = None,
    tenant_id: TenantId = None,
    db: DB = None,
    background_tasks: BackgroundTasks = None,
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

    async def _run_pipeline(doc_id: uuid.UUID, tid: uuid.UUID):
        async with async_session() as session:
            await process_document(session, doc_id, tid)

    background_tasks.add_task(_run_pipeline, doc.id, tenant_id)

    return DocumentUploadResponse(id=str(doc.id), upload_url=upload_url, s3_key=s3_key)


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
