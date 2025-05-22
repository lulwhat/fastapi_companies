from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import AsyncSession
from models import Category


class CategoriesQueries:
    @classmethod
    async def _get_category_depth(
            cls, category_id: int, db: AsyncSession
    ) -> int:
        depth = 1
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )
        current_category = result.scalars().first()
        while current_category and current_category.parent_id:
            depth += 1
            result = await db.execute(
                select(Category).where(
                    Category.id == current_category.parent_id)
            )
            current_category = result.scalars().first()
        return depth

    @classmethod
    async def create_category(
            cls, name: str, parent_id: int | None, db: AsyncSession
    ):
        try:
            # validate Category nesting depth does not exceed level 3
            if parent_id:
                parent_res = await db.execute(
                    select(Category).where(Category.id == parent_id)
                )
                parent = parent_res.scalar_one_or_none()
                if parent is None:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                        detail="Parent category not found")
                depth = await cls._get_category_depth(parent_id, db)
                if depth >= 3:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Maximum categories nesting depth of 3 exceeded"
                    )

            cat = Category(
                name=name,
                parent_id=parent_id if parent_id else None
            )
            db.add(cat)
            await db.commit()
            await db.refresh(cat)
            return cat

        except Exception as e:
            await db.rollback()
            raise e

    @staticmethod
    async def get_category(
            criteria: int | str, db: AsyncSession
    ) -> Category:
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
