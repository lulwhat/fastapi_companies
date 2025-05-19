from fastapi import APIRouter, status, Depends, HTTPException

from api.v1.schemas import CategoryResponse, CategoryCreate
from database import get_session, AsyncSession, insert_category, \
    select_category

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    responses={404: {"description": "Category not found"}}
)


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
    description="""## Create a new category with:
    
    - name: Category name (required)
    - parent_category: Parent category name (optional)

    Note: Maximum nesting depth is 3 levels
    """
)
async def create_category(
        category_data: CategoryCreate,
        db: AsyncSession = Depends(get_session)
) -> CategoryResponse:
    try:
        category = await insert_category(
            name=category_data.name,
            parent_category=category_data.parent_category,
            db=db
        )
        return CategoryResponse.from_orm(category)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
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
    cat = await select_category(category_id, db)
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
    cat = await select_category(category_name, db)
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
