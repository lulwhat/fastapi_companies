import pytest
import pytest_asyncio
from fastapi import status
from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape

from core.repositories.buildings import BuildingsQueries
from core.repositories.categories import CategoriesQueries
from core.repositories.companies import CompaniesQueries, CompaniesQuerybuilder
from models import Company, Building, Category, PhoneNumber


@pytest_asyncio.fixture
async def test_repo_data(db_session):
    # Create test building
    building = Building(
        address="123 Test St",
        coordinates=WKTElement("POINT (1.0 2.0)", srid=4326),
    )
    db_session.add(building)
    await db_session.commit()

    # Create test categories
    parent_category = Category(name="Parent Category")
    child_category = Category(name="Child Category", parent_id=1)
    db_session.add_all([parent_category, child_category])
    await db_session.commit()

    # Create test company
    company = Company(
        name="Test Company",
        building_id=building.id,
        categories=[parent_category, child_category]
    )
    db_session.add(company)
    await db_session.commit()

    # Add phone numbers
    phone = PhoneNumber(
        company_id=company.id,
        phone_number="1234567890"
    )
    db_session.add(phone)
    await db_session.commit()

    return {
        "building": building,
        "parent_category": parent_category,
        "child_category": child_category,
        "company": company,
        "phone": phone
    }


# Companies Repository Tests
@pytest.mark.asyncio(loop_scope="session")
async def test_create_company(db_session, test_repo_data):
    company = await CompaniesQueries.create_company(
        name="New Company",
        phone_numbers=["9876543210"],
        building_id=test_repo_data["building"].id,
        categories=[test_repo_data["parent_category"].id],
        db=db_session
    )

    assert company.name == "New Company"
    assert len(company.phone_numbers) == 1
    assert company.phone_numbers[0].phone_number == "9876543210"
    assert company.building_id == test_repo_data["building"].id
    assert len(company.categories) == 1
    assert company.categories[0].name == test_repo_data["parent_category"].name


@pytest.mark.asyncio(loop_scope="session")
async def test_get_companies_by_id(db_session, test_repo_data):
    companies = await CompaniesQueries.get_companies(
        test_repo_data["company"].id,
        db_session
    )
    assert companies[0].id == test_repo_data["company"].id
    assert companies[0].name == test_repo_data["company"].name


@pytest.mark.asyncio(loop_scope="session")
async def test_get_companies_by_name(db_session, test_repo_data):
    companies = await CompaniesQueries.get_companies(
        test_repo_data["company"].name,
        db_session
    )
    assert test_repo_data["company"].id in [cmp.id for cmp in companies]
    assert test_repo_data["company"].name in [cmp.name for cmp in companies]


@pytest.mark.asyncio(loop_scope="session")
async def test_get_companies_in_area(db_session, test_repo_data):
    companies = await CompaniesQueries.get_companies_in_area(
        lon=1.0,
        lat=2.0,
        radius=1000,
        db=db_session
    )
    assert len(companies) > 0
    assert any(c.id == test_repo_data["company"].id for c in companies)


@pytest.mark.asyncio(loop_scope="session")
async def test_get_companies_by_category(db_session, test_repo_data):
    result = await CompaniesQueries.get_companies_by_category(
        test_repo_data["parent_category"].id,
        db_session
    )
    assert test_repo_data["parent_category"] in result
    assert len(result[test_repo_data["parent_category"]]) > 0


@pytest.mark.asyncio(loop_scope="session")
async def test_advanced_search_companies(db_session, test_repo_data):
    companies = await CompaniesQueries.run_advanced_search(
        name=test_repo_data["company"].name,
        category_id=test_repo_data["parent_category"].id,
        category_name=None,
        phone_number=test_repo_data["phone"].phone_number,
        building_id=test_repo_data["building"].id,
        location=(1.0, 2.0, 1000),
        db=db_session
    )
    assert len(companies) > 0
    assert any(c.id == test_repo_data["company"].id for c in companies)


# QueryBuilder Tests
def test_company_query_builder():
    # Test ID query
    query = CompaniesQuerybuilder.get_company_query(1)
    assert str(query).find("companies.id = :id_1") > 0

    # Test name query
    query = CompaniesQuerybuilder.get_company_query("Test Company")
    assert str(query).find("companies.name = :name_1") > 0

    # Test area filter
    filter_expr = CompaniesQuerybuilder.get_area_filter(0.0, 0.0, 1000)
    assert str(filter_expr).find("ST_DWithin") > 0


# Error Cases
@pytest.mark.asyncio(loop_scope="session")
async def test_get_nonexistent_company(db_session):
    with pytest.raises(Exception) as exc_info:
        await CompaniesQueries.get_companies(999, db_session)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio(loop_scope="session")
async def test_create_company_with_invalid_category(db_session,
                                                    test_repo_data):
    with pytest.raises(Exception) as exc_info:
        await CompaniesQueries.create_company(
            name="New Company",
            phone_numbers=["9876543210"],
            building_id=test_repo_data["building"].id,
            categories=[999],  # non existent category id
            db=db_session
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio(loop_scope="session")
async def test_get_companies_in_empty_area(db_session):
    with pytest.raises(Exception) as exc_info:
        await CompaniesQueries.get_companies_in_area(
            lon=100.0,  # Far away from any test data
            lat=100.0,
            radius=1000,
            db=db_session
        )
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


# Buildings Repository Tests
@pytest.mark.asyncio(loop_scope="session")
async def test_create_building(db_session):
    longitude = 1.0
    latitude = 2.0
    building = await BuildingsQueries.create_building(
        address="456 New St",
        coordinates=(longitude, latitude),
        db=db_session
    )
    assert building.address == "456 New St"
    result_point = to_shape(building.coordinates)
    assert result_point.x == longitude
    assert result_point.y == latitude


@pytest.mark.asyncio(loop_scope="session")
async def test_get_building_by_id(db_session, test_repo_data):
    building = await BuildingsQueries.get_building(
        test_repo_data["building"].id,
        db_session
    )
    assert building.id == test_repo_data["building"].id


# Categories Repository Tests
@pytest.mark.asyncio(loop_scope="session")
async def test_create_category(db_session):
    category = await CategoriesQueries.create_category(
        name="New Category",
        parent_id=None,
        db=db_session
    )
    assert category.name == "New Category"


@pytest.mark.asyncio(loop_scope="session")
async def test_create_child_category(db_session, test_repo_data):
    category = await CategoriesQueries.create_category(
        name="New Child Category",
        parent_id=test_repo_data["parent_category"].id,
        db=db_session
    )
    assert category.name == "New Child Category"
    assert category.parent_id == test_repo_data["parent_category"].id


@pytest.mark.asyncio(loop_scope="session")
async def test_get_category_by_id(db_session, test_repo_data):
    category = await CategoriesQueries.get_category(
        test_repo_data["parent_category"].id,
        db_session
    )
    assert category.id == test_repo_data["parent_category"].id
    assert category.name == test_repo_data["parent_category"].name
