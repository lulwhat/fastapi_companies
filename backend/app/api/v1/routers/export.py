from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import FileResponse

from api.v1.schemas import ExportStatus
from database import get_session, AsyncSession
from rabbitmq.export_service import create_task, check_task, \
    get_export_file_content
from rabbitmq.producer import publish_export_task

router = APIRouter(
    prefix="/export",
    tags=["Export"],
    responses={404: {"description": "Endpoint not found"}}
)


@router.post(
    "/",
    response_model=ExportStatus,
    summary="Export table data to csv",
    description="""## Export tables data to CSV:
    
    - export_table: Table name to export (default: companies)
    """
)
async def create_export(
    bg_tasks: BackgroundTasks,
    export_table: str = "companies",
    db: AsyncSession = Depends(get_session)
) -> ExportStatus:
    task = await create_task(export_table, db)
    bg_tasks.add_task(publish_export_task, task.id)
    return ExportStatus(
        task_id=task.id,
        status=task.status,
        export_table=task.export_table,
        url=task.file_path,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.get(
    "/status/{task_id}",
    response_model=ExportStatus,
    summary="Check export status",
    description="""## Check export task status:
    
    - task_id: ID of the export task
    """
)
async def check_export_status(
    task_id: int,
    db: AsyncSession = Depends(get_session)
) -> ExportStatus:
    task = await check_task(task_id, db)
    return ExportStatus(
        task_id=task.id,
        status=task.status,
        export_table=task.export_table,
        url=task.file_path,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.get(
    "/download/{task_id}",
    summary="Download exported file",
    description="""## Download exported file:
    
    - task_id: ID of the export task
    """
)
async def download_export(
    task_id: int,
    db: AsyncSession = Depends(get_session)
):
    file_path = await get_export_file_content(task_id, db)
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="text/csv"
    )
