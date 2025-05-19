from typing import List, AsyncGenerator

from fastapi import HTTPException, status
from geoalchemy2 import WKTElement, Geography
from sqlalchemy import func, cast
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker, joinedload, selectinload

from config import settings
from models import Building, Company, Category, PhoneNumber, \
    company_category_association


engine = create_async_engine(settings.URL_DATABASE, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def create_session() -> AsyncSession:
    """For usage outside FastAPI (e.g. consumer)"""
    return AsyncSessionLocal()


async def select_building(building_id, db: AsyncSession) -> Building:
    result = await db.execute(
        select(Building).where(Building.id == building_id)
    )
    return result.scalar_one_or_none()


async def select_building_companies(
        building_id: int,
        db: AsyncSession
) -> Building:
    preload_options = [
        joinedload(Building.companies),
        joinedload(Building.companies).joinedload(Company.phone_numbers),
        joinedload(Building.companies).joinedload(Company.categories)
    ]
    q = (
        select(Building)
        .where(Building.id == building_id)
        .options(*preload_options)
    )

    res = await db.execute(q)
    bld = res.scalars().first()

    return bld


async def select_category(criteria: int | str, db: AsyncSession) -> Category:
    """Get category with children by search criteria (id or name)"""
    q = select(Category).options(selectinload(Category.children))
    match criteria:
        case int():
            result = await db.execute(q.where(Category.id == criteria))
            cat = result.scalars().first()
        case str():
            result = await db.execute(q.where(Category.name == criteria))
            cat = result.scalars().first()
        case _:
            cat = None

    return cat


async def select_company(criteria: str | int, db: AsyncSession):
    """Get company/companies by search criteria (id or name)"""
    q = select(Company)
    match criteria:
        case int():
            result = await db.execute(
                q.where(Company.id == criteria)
            )
            comp = result.scalars().first()
        case str():
            result = await db.execute(
                q.where(Company.name == criteria)
            )
            comp = result.scalars().first()
        case _:
            comp = None

    return comp


async def select_companies_in_area(
        coordinates: tuple[float, float], radius: int, db: AsyncSession
):
    center_point = cast(
        WKTElement(
            f'POINT({coordinates[0]} {coordinates[1]})', srid=4326
        ),
        Geography
    )
    preload_options = [
        joinedload(Building.companies),
        joinedload(Building.companies).joinedload(Company.phone_numbers),
        joinedload(Building.companies).joinedload(Company.categories)
    ]
    buildings_res = await db.execute(
        select(Building)
        .where(
            func.ST_DWithin(
                cast(Building.coordinates, Geography),
                center_point,
                radius
            )
        )
        .options(*preload_options)
    )
    buildings = [bld[0] for bld in buildings_res.unique().all()]
    if not buildings:
        return []
    return [comp for bld in buildings for comp in bld.companies]


async def select_companies_by_category(
        criteria: int | str, db: AsyncSession
) -> dict[Category, List[Company]]:
    """Get companies by search criteria (category_id or category_name)"""
    preload_options = [
        selectinload(Category.children).options(
            selectinload(Category.companies),
            selectinload(Category.children).options(
                selectinload(Category.companies)
            )
        ),
        selectinload(Category.companies)
    ]
    q = select(Category)
    match criteria:
        case int():
            result = await db.execute(
                q.where(Category.id == criteria).options(*preload_options)
            )
            main_cat = result.scalars().first()
        case str():
            result = await db.execute(
                q.where(Category.name == criteria).options(*preload_options)
            )
            main_cat = result.scalars().first()
        case _:
            main_cat = None

    if main_cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Category not found')

    main_comps = {main_cat: list(main_cat.companies)}
    child_comps = dict()
    grandchild_comps = dict()
    if main_cat.children:
        child_comps.update(
            (cat, list(cat.companies)) for cat in main_cat.children
        )
    for child_cat in child_comps.keys():
        if child_cat.children:
            grandchild_comps.update(
                (cat, list(cat.companies)) for cat in child_cat.children
            )
    return {**main_comps, **child_comps, **grandchild_comps}


async def insert_building(
        address: str, coordinates: tuple[float, float], db: AsyncSession
):
    try:
        bld = Building(
            address=address,
            coordinates=WKTElement(
                f'POINT({coordinates[0]} {coordinates[1]})', srid=4326
            )
        )
        db.add(bld)
        await db.commit()
        await db.refresh(bld)
        return bld
    except Exception as e:
        await db.rollback()
        raise e


async def insert_company(
        name: str, phone_numbers: list, building_id: int, categories: list,
        db: AsyncSession
):
    cmp = Company(
        name=name, building_id=building_id
    )
    db.add(cmp)
    await db.flush()

    try:
        nums_db = []
        for number in phone_numbers:
            nums_db.append(PhoneNumber(phone_number=number, company_id=cmp.id))
        db.add_all(nums_db)

        if categories:
            categories_res = await db.execute(
                select(Category).where(Category.name.in_(categories))
            )
            existing_categories = categories_res.scalars().all()
            if len(existing_categories) != len(categories):
                found_names = {c.name for c in existing_categories}
                missing = set(categories) - found_names
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Categories not found: {missing}'
                )
            # Clear existing associations
            await db.execute(
                company_category_association.delete().where(
                    company_category_association.c.company_id == cmp.id
                )
            )
            # Add new associations
            await db.execute(
                company_category_association.insert(),
                [{'company_id': cmp.id, 'category_id': c.id} for c in
                 existing_categories]
            )

        await db.commit()
        await db.refresh(cmp)
        return cmp

    except Exception as e:
        await db.rollback()
        raise e


async def _get_category_depth(category_id: int, db: AsyncSession) -> int:
    depth = 1
    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    current_category = result.scalars().first()
    while current_category and current_category.parent_id:
        depth += 1
        result = await db.execute(
            select(Category).where(Category.id == current_category.parent_id)
        )
        current_category = result.scalars().first()
    return depth


async def insert_category(name: str, parent_category: str | None,
                          db: AsyncSession):
    try:
        # validate Category nesting depth does not exceed level 3
        parent_id = None
        if parent_category is not None:
            parent_res = await db.execute(
                select(Category).where(Category.name == parent_category)
            )
            parent = parent_res.scalars().first()
            if parent is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail='Parent category not found')
            parent_id = parent.id
            depth = await _get_category_depth(parent_id, db)
            if depth >= 3:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail='Maximum nesting depth of 3 exceeded'
                )

        cat = Category(name=name,
                       parent_id=parent_id)
        db.add(cat)
        await db.commit()
        await db.refresh(cat)
        return cat
    except Exception as e:
        await db.rollback()
        raise e
