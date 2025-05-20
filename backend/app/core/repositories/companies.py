from typing import List

from fastapi import HTTPException, status
from geoalchemy2 import Geography, WKTElement
from sqlalchemy import select, cast, func, Select, Sequence, and_
from sqlalchemy.orm import joinedload, selectinload

from database import AsyncSession
from models import Company, Building, Category, PhoneNumber, \
    company_category_association


class CompaniesQuerybuilder:
    @classmethod
    def get_company_query(cls, criteria: str | int) -> Select:
        q = select(Company)
        match criteria:
            case int():
                q = q.where(Company.id == criteria)
            case str():
                q = q.where(Company.name == criteria)
            case _:
                raise ValueError(
                    "Invalid company search parameter, str or int required"
                )
        return q

    @classmethod
    def get_area_filter(cls, lon: float, lat: float, radius: int):
        center_point = cast(
            WKTElement(
                f"POINT({lon} {lat})", srid=4326
            ),
            Geography
        )
        return Company.building.has(
            func.ST_DWithin(
                cast(Building.coordinates, Geography),
                center_point,
                radius
            )
        )

    @classmethod
    def get_companies_in_area_query(
            cls, lon: float, lat: float, radius: int
    ) -> Select:
        preload_options = [
            selectinload(Company.phone_numbers),
            selectinload(Company.categories),
            joinedload(Company.building)
        ]
        area_filter = cls.get_area_filter(lon, lat, radius)

        q = (
            select(Company).where(area_filter).options(*preload_options)
        )
        return q

    @classmethod
    def get_companies_by_category_query(cls, criteria: int | str) -> Select:
        preload_options = [
            selectinload(Category.children).options(
                selectinload(Category.companies),
                selectinload(Category.children).options(
                    selectinload(Category.companies)
                )
            ),
            selectinload(Category.companies)
        ]

        match criteria:
            case int():
                cat_filter = (Category.id == criteria)
            case str():
                cat_filter = (Category.name == criteria)
            case _:
                raise ValueError("Invalid category search parameter, "
                                 "str or int required")

        q = select(Category).where(cat_filter).options(*preload_options)
        return q

    @classmethod
    def get_companies_advanced_search_query(
            cls, name, category_id, category_name, phone_number, building_id,
            location
    ) -> Select:
        """Builds and returns search query based on provided parameters"""
        q = select(Company).options(
            joinedload(Company.phone_numbers),
            joinedload(Company.building),
            selectinload(Company.categories),
        )
        filters = []

        if name:
            filters.append(Company.name.ilike(f"%{name}%"))

        if category_id:
            filters.append(
                Company.categories.any(Category.id == category_id)
            )

        if category_name:
            filters.append(
                Company.categories.any(Category.name == category_name)
            )

        if phone_number:
            filters.append(
                Company.phone_numbers.any(
                    func.regexp_replace(
                        PhoneNumber.phone_number, "[^0-9]", "", "g"
                    ).ilike(f"%{phone_number}%")
                )
            )

        if building_id:
            filters.append(Company.building_id == building_id)

        if location:
            lon, lat, radius = location
            area_filter = CompaniesQuerybuilder.get_area_filter(
                lon, lat, radius
            )
            filters.append(area_filter)

        if filters:
            q = q.where(and_(*filters))

        return q


class CompaniesQueries:
    @staticmethod
    async def create_company(
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
                nums_db.append(
                    PhoneNumber(phone_number=number, company_id=cmp.id)
                )
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
                        detail=f"Categories not found: {missing}"
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
                    [{"company_id": cmp.id, "category_id": c.id} for c in
                     existing_categories]
                )

            await db.commit()
            await db.refresh(cmp)
            return cmp

        except Exception as e:
            await db.rollback()
            raise e

    @staticmethod
    async def get_company(criteria: str | int, db: AsyncSession) -> Company:
        """Get company by search criteria (id or name)"""

        query = CompaniesQuerybuilder.get_company_query(criteria)
        try:
            result = await db.execute(query)
            comp = result.scalar_one_or_none()
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=str(e))

        if comp is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Company not found")

        return comp

    @staticmethod
    async def get_companies_in_area(
            lon: float, lat: float, radius: int, db: AsyncSession
    ) -> Sequence[Company]:
        query = CompaniesQuerybuilder.get_companies_in_area_query(
            lon, lat, radius
        )
        result = await db.execute(query)
        buildings = result.scalars().all()

        if not buildings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No companies found in given area"
            )
        return buildings

    @staticmethod
    async def get_companies_by_category(
            criteria: int | str, db: AsyncSession
    ) -> dict[Category, List[Company]]:
        """Get companies by search criteria (category_id or category_name)"""

        try:
            query = (
                CompaniesQuerybuilder.get_companies_by_category_query(criteria)
            )
            result = await db.execute(query)
            main_cat = result.scalars().first()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        if not main_cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

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

    @staticmethod
    async def run_advanced_search(
            name, category_id, category_name, phone_number, building_id,
            location, db: AsyncSession
    ) -> Sequence[Company]:
        query = CompaniesQuerybuilder.get_companies_advanced_search_query(
            name, category_id, category_name, phone_number, building_id,
            location
        )

        result = await db.execute(query)
        comps = result.scalars().unique().all()

        if not comps:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No companies found"
            )

        return comps
