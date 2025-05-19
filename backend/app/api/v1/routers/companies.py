from typing import List

from fastapi import APIRouter, status, Depends, HTTPException

from api.v1.schemas import CompanyResponse, CompanyCreate, \
    CompaniesByCategoriesResponse
from database import insert_company, get_session, AsyncSession, \
    select_companies_in_area, select_company, select_companies_by_category

router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
    responses={404: {"description": "Not found"}}
)


@router.post(
    "/",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new company",
    response_description="The created company record",
    description="""Create a new company with:
    
    - name: Company name
    - phone_numbers: List of phone numbers (e.g. ["9023456789"])
    - building_id: ID of the building where company is located
    - categories: List of category names
    """
)
async def create_company(
        company_data: CompanyCreate, db: AsyncSession = Depends(get_session)
) -> CompanyResponse:
    try:
        cmp = await insert_company(
            company_data.name, company_data.phone_numbers,
            company_data.building_id, company_data.categories, db
        )
        return CompanyResponse(
            id=cmp.id,
            name=cmp.name,
            phone_numbers=[str(num.phone_number) for num in cmp.phone_numbers],
            building_id=cmp.building_id,
            categories=[cat.name for cat in cmp.categories]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Get company by ID",
    description="""## Get company details by ID:
    
    - company_id: ID of the company to retrieve
    """
)
async def get_company_by_id(
    company_id: int,
    db: AsyncSession = Depends(get_session)
) -> CompanyResponse:
    cmp = await select_company(company_id, db)
    if cmp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return CompanyResponse(
        id=cmp.id,
        name=cmp.name,
        phone_numbers=[str(num.phone_number) for num in cmp.phone_numbers],
        building_id=cmp.building_id,
        categories=[cat.name for cat in cmp.categories]
    )


@router.get(
    "/search/by-company-name",
    response_model=CompanyResponse,
    summary="Search company by name",
    description="""## Search company by name:
    
    - company_name: Name of the company to search
    """
)
async def search_company_by_name(
    company_name: str,
    db: AsyncSession = Depends(get_session)
) -> CompanyResponse:
    cmp = await select_company(company_name, db)
    if cmp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return CompanyResponse(
        id=cmp.id,
        name=cmp.name,
        phone_numbers=[str(num.phone_number) for num in cmp.phone_numbers],
        building_id=cmp.building_id,
        categories=[cat.name for cat in cmp.categories]
    )


@router.post(
    "/search/in-area",
    response_model=List[CompanyResponse],
    summary="Find companies near location",
    response_description="List of companies in the area",
    description="""## Search for companies within radius:
    
    - radius: Search radius in meters
    - coordinates: Center point (longitude, latitude)
    """
)
async def search_companies_in_area(
        radius: int,
        coordinates: tuple[float, float],
        db: AsyncSession = Depends(get_session)
) -> List[CompanyResponse]:
    try:
        companies = await select_companies_in_area(coordinates, radius, db)
        return [
            CompanyResponse(
                id=cmp.id,
                name=cmp.name,
                phone_numbers=[
                    str(num.phone_number) for num in cmp.phone_numbers
                ],
                building_id=cmp.building_id,
                categories=[
                    {"category_id": cat.id, "category_name": cat.name}
                    for cat in cmp.categories
                ]
            ) for cmp in companies
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid search parameters: {str(e)}"
        )


@router.get(
    "/search/by-category-id",
    response_model=List[CompaniesByCategoriesResponse],
    summary="Get companies by category ID",
    description="""## Get companies by category ID including category children:

    - category_id: ID of the category to filter by
    """
)
async def get_companies_by_category_id(
    category_id: int,
    db: AsyncSession = Depends(get_session)
) -> List[CompaniesByCategoriesResponse]:
    result = await select_companies_by_category(category_id, db)
    return [
        CompaniesByCategoriesResponse(
            category_id=cat.id,
            category_name=cat.name,
            companies=[
                {"company_id": comp.id, "company_name": comp.name}
                for comp in comps
            ]
        )
        for cat, comps in result.items()
    ]


@router.get(
    "/search/by-category-name",
    response_model=List[CompaniesByCategoriesResponse],
    summary="Get companies by category name",
    description="""## Get companies by category ID including category children:

    - category_name: name of the category to filter by
    """
)
async def get_companies_by_category_name(
    category_name: str,
    db: AsyncSession = Depends(get_session)
) -> List[CompaniesByCategoriesResponse]:
    result = await select_companies_by_category(category_name, db)
    return [
        CompaniesByCategoriesResponse(
            category_id=cat.id,
            category_name=cat.name,
            companies=[
                {"company_id": comp.id, "company_name": comp.name}
                for comp in comps
            ]
        )
        for cat, comps in result.items()
    ]
