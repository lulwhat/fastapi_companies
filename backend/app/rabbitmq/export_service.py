import csv
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from config import settings
from database import AsyncSession
from models import Company, ExportTask, PhoneNumber, Building, Category


async def create_task(export_table, db: AsyncSession) -> ExportTask:
    q = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = :table_name
            )
        """)
    result = await db.execute(q, {'table_name': export_table})
    table_exists = result.scalar_one()
    if table_exists is False:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Table not found')

    task = ExportTask(
        status='pending',
        export_table=export_table
    )
    db.add(task)
    await db.commit()
    return task


async def process_task(db: AsyncSession, task_id: int):
    task = await db.execute(
        select(ExportTask).where(ExportTask.id == task_id)
    )
    task = task.scalar_one()

    try:
        task.status = 'processing'
        await db.commit()

        table = task.export_table
        match table:
            case 'companies':
                result = await db.execute(
                    select(Company)
                    .options(
                        selectinload(Company.phone_numbers),
                        selectinload(Company.categories)
                    )
                )
                entries = result.scalars().all()
                first_row = [
                    'id', 'name', 'phone_numbers', 'building_id', 'categories'
                ]
                data_rows = [
                    [
                        ent.id,
                        ent.name,
                        '; '.join(
                            str(p.phone_number)
                            for p in ent.phone_numbers
                        ),
                        ent.building_id,
                        '; '.join(c.name for c in ent.categories)
                    ]
                    for ent in entries
                ]
            case 'phone_numbers':
                result = await db.execute(select(PhoneNumber))
                entries = result.scalars().all()
                first_row = [
                    'id', 'phone_number', 'company_id'
                ]
                data_rows = [
                    [ent.id, ent.phone_number, ent.company_id]
                    for ent in entries
                ]
            case 'buildings':
                result = await db.execute(select(Building))
                entries = result.scalars().all()
                first_row = [
                    'id', 'address', 'coordinates'
                ]
                data_rows = [
                    [ent.id, ent.address, ent.coordinates]
                    for ent in entries
                ]
            case 'categories':
                result = await db.execute(
                    select(Category).options(selectinload(Category.children))
                )
                entries = result.scalars().all()
                first_row = [
                    'id', 'name', 'parent_id', 'parent_name', 'children'
                ]
                data_rows = [
                    [
                        ent.id,
                        ent.name,
                        ent.parent_id,
                        ent.parent.name if ent.parent else None,
                        '; '.join(c.name for c in ent.children)
                    ]
                    for ent in entries
                ]
            case _:
                raise NotImplementedError(f'Export not available for {table}')

        date_now = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'export_{table}_{date_now}.csv'
        filepath = Path(settings.EXPORT_DIR) / filename

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(first_row)
            writer.writerows(data_rows)

        task.status = 'completed'
        task.file_path = str(filepath)
        await db.commit()
    except Exception as e:
        task.status = 'failed'
        await db.commit()
        raise e


async def check_task(task_id: int, db: AsyncSession) -> ExportTask:
    result = await db.execute(
        select(ExportTask).where(ExportTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Task not found')
    return task


async def get_export_file_content(task_id: int, db: AsyncSession) -> Path:
    task = await check_task(task_id, db)

    if task.status != 'completed':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Export not completed yet'
        )

    if not task.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='File not found'
        )

    file_path = Path(task.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='File not found on server'
        )

    return file_path
