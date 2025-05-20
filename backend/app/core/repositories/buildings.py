from geoalchemy2 import WKTElement
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import AsyncSession
from models import Building, Company


class BuildingsQueries:
    @staticmethod
    async def create_building(
            address: str, coordinates: tuple[float, float], db: AsyncSession
    ):
        try:
            bld = Building(
                address=address,
                coordinates=WKTElement(
                    f"POINT({coordinates[0]} {coordinates[1]})", srid=4326
                )
            )
            db.add(bld)
            await db.commit()
            await db.refresh(bld)
            return bld
        except Exception as e:
            await db.rollback()
            raise e

    @staticmethod
    async def get_building(building_id: int, db: AsyncSession) -> Building:
        result = await db.execute(
            select(Building).where(Building.id == building_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_building_companies(
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
