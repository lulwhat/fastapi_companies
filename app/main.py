from typing import List

from fastapi import FastAPI, Depends

import schemas
from database import AsyncSession, get_session, select_building, \
    select_category, select_company, select_companies_in_area, \
    select_companies_by_category, insert_building, insert_company, \
    insert_category, select_building_companies

app = FastAPI()


@app.post(
    '/building/create/',
    response_model=schemas.Building,
    description="""## Create building with provided parameters:
    
    - str: address
    - tuple (float, float): coordinates (lon, lat)
    """
)
async def create_building(
    address: str,
    coordinates: tuple[float, float],
    db: AsyncSession = Depends(get_session)
):
    bld = await insert_building(address, coordinates, db)
    return {
        'id': bld.id,
        'address': bld.address,
        'coordinates': schemas.Coordinates.from_wkb(bld.coordinates)
    }


@app.post(
    '/company/create/',
    response_model=schemas.Company,
    description="""## Create company with provided parameters:
    
        - str: name
        - list: phone_numbers, e.g. [9023456789, 2023456]
        (phone code +7 is added automatically)
        - int: building_id
        - list: categories names. categories should be created beforehand,
        otherwise they will be skipped during company creation
        """
)
async def create_company(
        name: str, phone_numbers: List[str], building_id: int,
        categories: List[str], db: AsyncSession = Depends(get_session)
):
    cmp = await insert_company(
        name, phone_numbers, building_id, categories, db
    )
    return {
        'id': cmp.id,
        'name': cmp.name,
        'phone_numbers': [str(num.phone_number) for num in cmp.phone_numbers],
        'building_id': cmp.building_id,
        'categories': [cat.name for cat in cmp.categories]
    }


@app.post(
    '/category/create/',
    response_model=schemas.Category,
    description="""## Create category with provided parameters:
    
    - str: name
    - str | None: parent_category, nesting depth of categories is limited by 3,
        otherwise 422 error is raised. 
        leave empty if the category doesn't have a parent
    """
)
async def create_category(
        name: str, parent_category: str | None = None,
        db: AsyncSession = Depends(get_session)
):
    return await insert_category(name, parent_category, db)


@app.get(
    '/building/search-by-id/',
    response_model=schemas.Building,
    description="""## Search building by id:

    - int: building_id
    """
)
async def get_building_by_id(
        building_id: int,
        db: AsyncSession = Depends(get_session)
):
    bld = await select_building(building_id, db)
    return {
        'id': bld.id,
        'address': bld.address,
        'coordinates': schemas.Coordinates.from_wkb(bld.coordinates)
    }


@app.get(
    '/building/companies/',
    response_model=schemas.BuildingCompanies,
    description="""## Get companies in the building:

    - int: building_id
    """
)
async def get_building_companies(
        building_id: int,
        db: AsyncSession = Depends(get_session)
):
    bld = await select_building_companies(building_id, db)
    return {
        'id': bld.id,
        'address': bld.address,
        'companies': [
            {
                'company_id': cmp.id,
                'company_name': cmp.name,
                'categories': [
                    {'category_id': cat.id, 'category_name': cat.name}
                    for cat in cmp.categories
                ],
                'phone_numbers': [
                    str(num.phone_number) for num in cmp.phone_numbers
                ]
            } for cmp in bld.companies
        ]
    }


@app.get(
    '/category/search-by-id/',
    response_model=schemas.Category,
    description="""## Search for a category by id:

    - int: category_id
    """
)
async def get_category_by_id(
        category_id: int,
        db: AsyncSession = Depends(get_session)
):
    cat = await select_category(category_id, db)
    return {
        'id': cat.id,
        'name': cat.name,
        'parent_id': cat.parent_id,
        'children': [
            {'id': child.id, 'name': child.name} for child in cat.children
        ]
    }


@app.get(
    '/category/search-by-name/',
    response_model=schemas.Category,
    description="""## Search for a category by name:

    - str: category_name
    """
)
async def get_category_by_name(
        category_name: str,
        db: AsyncSession = Depends(get_session)
):
    cat = await select_category(category_name, db)
    return {
        'id': cat.id,
        'name': cat.name,
        'parent_id': cat.parent_id,
        'children': [
            {'id': child.id, 'name': child.name} for child in cat.children
        ]
    }


@app.post(
    '/company/list/in-area/',
    response_model=List[schemas.Company],
    description="""## Search for companies in given area:
    
    - tuple (float, float): coordinates (lon, lat) - center point of search
    - int: radius - in meters 
    """
)
async def get_companies_in_area(
        radius: int,
        coordinates: tuple[float, float],
        db: AsyncSession = Depends(get_session)
):
    comps = await select_companies_in_area(coordinates, radius, db)
    return [
        {
            'id': cmp.id,
            'name': cmp.name,
            'phone_numbers': [
                str(num.phone_number) for num in cmp.phone_numbers
            ],
            'building_id': cmp.building_id,
            'categories': [
                {'category_id': cat.id, 'category_name': cat.name}
                for cat in cmp.categories
            ]
        } for cmp in comps
    ]


@app.get(
    '/company/list/by-category-id/',
    response_model=List[schemas.CompaniesByCategories],
    description="""## Search for companies by category id:

    - int: category_id
    """
)
async def get_companies_by_category_id(
        category_id: int,
        db: AsyncSession = Depends(get_session)
):
    result = await select_companies_by_category(category_id, db)
    response = [
        {
            'category_id': cat.id,
            'category_name': cat.name,
            'companies': {
                'company_id': comp.id,
                'company_name': comp.name
            }
        } for cat, comps in result.items() for comp in comps
    ]
    return response


@app.get(
    '/company/list/by-category-name/',
    response_model=List[schemas.CompaniesByCategories],
    description="""## Search for companies by category name:

    - str: category_name
    """
)
async def get_companies_by_category_name(
        category_name: str,
        db: AsyncSession = Depends(get_session)
):
    result = await select_companies_by_category(category_name, db)
    response = [
        {
            'category_id': cat.id,
            'category_name': cat.name,
            'companies': {
                'company_id': comp.id,
                'company_name': comp.name
            }
        } for cat, comps in result.items() for comp in comps
    ]
    return response


@app.get(
    '/company/search-by-name/',
    response_model=schemas.Company,
    description="""## Search for company by name:
    
    - str: company_name
    """
)
async def get_company_by_name(
        company_name: str,
        db: AsyncSession = Depends(get_session)
):
    cmp = await select_company(company_name, db)
    return {
        'id': cmp.id,
        'name': cmp.name,
        'phone_numbers': [str(num.phone_number) for num in cmp.phone_numbers],
        'building_id': cmp.building_id,
        'categories': [cat.name for cat in cmp.categories]
    }


@app.get(
    '/company/search-by-id/',
    response_model=schemas.Company,
    description="""## Search for company by id:

    - int: company_id
    """
)
async def get_company_by_id(
        company_id: int,
        db: AsyncSession = Depends(get_session)
):
    cmp = await select_company(company_id, db)
    return {
        'id': cmp.id,
        'name': cmp.name,
        'phone_numbers': [str(num.phone_number) for num in cmp.phone_numbers],
        'building_id': cmp.building_id,
        'categories': [cat.name for cat in cmp.categories]
    }
