from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.schemas import BuildingCreate, BuildingResponse, \
    BuildingCompaniesResponse, Coordinates
from core.repositories.buildings import BuildingsQueries
from database import get_session

router = APIRouter(
    prefix="/buildings",
    tags=["Buildings"],
    responses={404: {"description": "Endpoint not found"}}
)


@router.post(
    "/",
    response_model=BuildingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new building",
    response_description="The created building record",
    description="""Create a new building with address and coordinates:
    
    - address: Full postal address
    - coordinates: Tuple of (longitude, latitude)
    """
)
async def create_building(
        building_data: BuildingCreate,
        db: AsyncSession = Depends(get_session)
) -> BuildingResponse:
    try:
        coordinates_tuple = (
            building_data.coordinates.longitude,
            building_data.coordinates.latitude
        )
        bld = await BuildingsQueries.create_building(
            building_data.address, coordinates_tuple, db
        )
        return BuildingResponse(
            id=bld.id,
            address=bld.address,
            coordinates=Coordinates.from_wkb(bld.coordinates)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{building_id}",
    response_model=BuildingResponse,
    summary="Get building by ID",
    response_description="Building details",
    description="""Retrieve building information by its ID:
    
    - building_id: ID of the building to retrieve
    """
)
async def get_building(
        building_id: int,
        db: AsyncSession = Depends(get_session)
) -> BuildingResponse:
    bld = await BuildingsQueries.get_building(building_id, db)
    if not bld:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Building not found"
        )
    return BuildingResponse(
        id=bld.id,
        address=bld.address,
        coordinates=Coordinates.from_wkb(bld.coordinates)
    )


@router.get(
    "/{building_id}/companies",
    response_model=BuildingCompaniesResponse,
    summary="Get companies in a building",
    response_description="List of companies in the building",
    description="""Get all companies located in the specified building:
    
    - building_id: ID of the building to query
    """
)
async def get_companies_in_building(
        building_id: int,
        db: AsyncSession = Depends(get_session)
) -> BuildingCompaniesResponse:
    bld = await BuildingsQueries.get_building_companies(building_id, db)

    if bld is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Building not found"
        )

    return BuildingCompaniesResponse(
        id=bld.id,
        address=bld.address,
        coordinates=Coordinates.from_wkb(bld.coordinates),
        companies=[
            {
                "company_id": cmp.id,
                "company_name": cmp.name,
                "categories": [
                    {"category_id": cat.id, "category_name": cat.name}
                    for cat in cmp.categories
                ],
                "phone_numbers": [
                    str(num.phone_number) for num in cmp.phone_numbers
                ]
            } for cmp in bld.companies
        ]
    )
