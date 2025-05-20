from fastapi import APIRouter, status, Depends, HTTPException

from api.v1.schemas import CategoryResponse
from core.repositories.categories import CategoriesQueries
from database import get_session, AsyncSession

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    responses={404: {"description": "Endpoint not found"}}
)


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
    description="""## Create a new category with:
    
    - name: Category name (required)
    - parent_id: Parent category id (optional)

    Note: Maximum nesting depth is 3 levels
    """
)
async def create_category(
        name: str,
        parent_id: int | None = None,
        db: AsyncSession = Depends(get_session)
) -> CategoryResponse:
    category = await CategoriesQueries.create_category(name, parent_id, db)
    return CategoryResponse(
        id=category.id,
        name=category.name,
        parent_id=category.parent_id,
        children=[]
    )


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get category by ID",
    description="""## Get category details by ID with parent and children:
    
    - category_id: ID of the category to retrieve
    """
)
async def get_category_by_id(
        category_id: int,
        db: AsyncSession = Depends(get_session)
) -> CategoryResponse:
    cat = await CategoriesQueries.get_category(category_id, db)
    if cat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return CategoryResponse(
        id=cat.id,
        name=cat.name,
        parent_id=cat.parent_id,
        children=[
            {"id": child.id, "name": child.name} for child in cat.children
        ]
    )


@router.get(
    "/by-name/{category_name}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get category by name",
    description="""## Get category details by name with parent and children:
    
    - category_name: Name of the category to retrieve
    """
)
async def get_category_by_name(
        category_name: str,
        db: AsyncSession = Depends(get_session)
) -> CategoryResponse:
    cat = await CategoriesQueries.get_category(category_name, db)
    if cat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return CategoryResponse(
        id=cat.id,
        name=cat.name,
        parent_id=cat.parent_id,
        children=[
            {'id': child.id, 'name': child.name} for child in cat.children
        ]
    )
