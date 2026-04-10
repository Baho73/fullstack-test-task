# FILE: backend/src/app.py
# VERSION: 1.1.0
# START_MODULE_CONTRACT
#   PURPOSE: FastAPI application: routes, middleware, DI sessions, pagination via query params.
#   SCOPE: CRUD endpoints for files, alerts listing, file download
#   DEPENDS: M-SERVICE-FILES, M-SERVICE-ALERTS, M-SCHEMAS, M-TASKS, M-DB
#   LINKS: M-APP, V-M-APP
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   app - FastAPI application instance
# END_MODULE_MAP

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas import AlertItem, FileItem, FileUpdate, PaginatedResponse
from src.services import alert_service, file_service
from src.tasks import scan_file_for_threats

from fastapi import File, Form, UploadFile

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# START_BLOCK_FILE_ROUTES
@app.get("/files", response_model=PaginatedResponse[FileItem])
async def list_files_view(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    return await file_service.list_files(session, limit=limit, offset=offset)


@app.post("/files", response_model=FileItem, status_code=201)
async def create_file_view(
    title: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    file_item = await file_service.create_file(session, title=title, upload_file=file)
    await session.commit()
    scan_file_for_threats.delay(file_item.id)
    return file_item


@app.get("/files/{file_id}", response_model=FileItem)
async def get_file_view(
    file_id: str,
    session: AsyncSession = Depends(get_session),
):
    file = await file_service.get_file(session, file_id)
    return FileItem.model_validate(file)


@app.patch("/files/{file_id}", response_model=FileItem)
async def update_file_view(
    file_id: str,
    payload: FileUpdate,
    session: AsyncSession = Depends(get_session),
):
    result = await file_service.update_file(session, file_id, title=payload.title)
    await session.commit()
    return result


@app.get("/files/{file_id}/download")
async def download_file_view(
    file_id: str,
    session: AsyncSession = Depends(get_session),
):
    file_item, stored_path = await file_service.get_download_path(session, file_id)
    return FileResponse(
        path=stored_path,
        media_type=file_item.mime_type,
        filename=file_item.original_name,
    )


@app.delete("/files/{file_id}", status_code=204)
async def delete_file_view(
    file_id: str,
    session: AsyncSession = Depends(get_session),
):
    await file_service.delete_file(session, file_id)
    await session.commit()
# END_BLOCK_FILE_ROUTES


# START_BLOCK_ALERT_ROUTES
@app.get("/alerts", response_model=PaginatedResponse[AlertItem])
async def list_alerts_view(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    return await alert_service.list_alerts(session, limit=limit, offset=offset)
# END_BLOCK_ALERT_ROUTES

# START_CHANGE_SUMMARY
#   LAST_CHANGE: [v1.1.0 - Refactored: DI sessions via Depends(get_session), pagination
#                  query params on GET /files and /alerts, delegates to service layer,
#                  removed direct service.py imports, added GRACE markup]
# END_CHANGE_SUMMARY
