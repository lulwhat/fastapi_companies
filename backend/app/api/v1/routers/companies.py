from typing import List

from fastapi import APIRouter, status, Depends, HTTPException

from api.v1.schemas import CompanyResponse, CompanyCreate, \
    CompaniesByCategoriesResponse, CompanyAdvancedSearchParams, \
    CompanyAreaSearchParams
from core.repositories.companies import CompaniesQueries
from database import get_session, AsyncSession

router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Endpoint not found"}
    }
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
    - categories: List of category IDs
    """
)
async def create_company(
        company_data: CompanyCreate, db: AsyncSession = Depends(get_session)
) -> CompanyResponse:
    try:
        cmp = await CompaniesQueries.create_company(
            company_data.name, company_data.phone_numbers,
            company_data.building_id, company_data.categories, db
        )
        return CompanyResponse(
            id=cmp.id,
            name=cmp.name,
            phone_numbers=[str(num.phone_number) for num in cmp.phone_numbers],
            building_id=cmp.building_id,
            categories=[
                {"category_id": cat.id, "category_name": cat.name}
                for cat in cmp.categories
            ]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{company_id}",
    response_model=List[CompanyResponse],
    summary="Get company by ID",
    description="""## Get company details by ID:
    
    - company_id: ID of the company to retrieve
    """
)
async def get_companies_by_id(
        company_id: int,
        db: AsyncSession = Depends(get_session)
) -> List[CompanyResponse]:
    cmps = await CompaniesQueries.get_companies(company_id, db)
    return [
            CompanyResponse(
                id=cmp.id,
                name=cmp.name,
                phone_numbers=[str(num.phone_number) for num in cmp.phone_numbers],
                building_id=cmp.building_id,
                categories=[
                    {"category_id": cat.id, "category_name": cat.name}
                    for cat in cmp.categories
                ]
            ) for cmp in cmps
    ]


@router.get(
    "/search/by-company-name",
    response_model=List[CompanyResponse],
    summary="Search companies by name",
    description="""## Search companies by name:
    
    - company_name: Name of the company to search
    """
)
async def search_companies_by_name(
        company_name: str,
        db: AsyncSession = Depends(get_session)
) -> List[CompanyResponse]:
    cmps = await CompaniesQueries.get_companies(company_name, db)
    return [
        CompanyResponse(
            id=cmp.id,
            name=cmp.name,
            phone_numbers=[str(num.phone_number) for num in cmp.phone_numbers],
            building_id=cmp.building_id,
            categories=[
                {"category_id": cat.id, "category_name": cat.name}
                for cat in cmp.categories
            ]
        ) for cmp in cmps
    ]


@router.post(
    "/search/in-area",
    response_model=List[CompanyResponse],
    summary="Find companies near location",
    response_description="List of companies in the area",
    description="""## Search for companies within radius:
    
    - radius: Search radius in meters
    - longitude: Center point longitude
    - latitude: Center point latitude
    """
)
async def search_companies_in_area(
        search_data: CompanyAreaSearchParams,
        db: AsyncSession = Depends(get_session)
) -> List[CompanyResponse]:
    companies = await CompaniesQueries.get_companies_in_area(
        search_data.longitude, search_data.latitude, search_data.radius, db
    )
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
    result = await CompaniesQueries.get_companies_by_category(category_id, db)
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
    result = await CompaniesQueries.get_companies_by_category(
        category_name, db
    )
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
    "/search/advanced",
    response_model=List[CompanyResponse],
    summary="Advanced company search",
    description="""## Search companies with multiple filters combined:

    - name: Partial company name match
    - category_id: Exact category ID (exclusive with category_name)
    - category_name: Exact category name (exclusive with category_id)
    - phone_number: Partial phone number match
    - building_id: Exact building ID
    - location: Geographic search as "longitude,latitude,radius_meters"
    """,
)
async def advanced_search_companies(
        search_data: CompanyAdvancedSearchParams = Depends(),
        db: AsyncSession = Depends(get_session)
) -> List[CompanyResponse]:
    companies = await CompaniesQueries.run_advanced_search(
        search_data.name,
        search_data.category_id,
        search_data.category_name,
        search_data.phone_number,
        search_data.building_id,
        search_data.location,
        db
    )

    return [
        CompanyResponse(
            id=cmp.id,
            name=cmp.name,
            phone_numbers=[str(num.phone_number) for num in
                           cmp.phone_numbers],
            building_id=cmp.building_id,
            categories=[
                {"category_id": cat.id, "category_name": cat.name}
                for cat in cmp.categories
            ]
        )
        for cmp in companies
    ]
