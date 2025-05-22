import pytest
import pytest_asyncio
from fastapi import status
from geoalchemy2 import WKTElement

from models import Company, Building, Category, PhoneNumber


@pytest_asyncio.fixture
async def test_data(db_session):
    # Create test building
    building = Building(
        address="123 Test St",
        coordinates=WKTElement("POINT (1.0 2.0)", srid=4326),
    )
    db_session.add(building)
    await db_session.commit()

    # Create test category
    category = Category(name="Test Category")
    db_session.add(category)
    await db_session.commit()

    # Create test company
    company = Company(
        name="Test Company",
        building_id=building.id,
        categories=[category]
    )
    db_session.add(company)
    await db_session.commit()

    # Add phone number
    phone = PhoneNumber(
        company_id=company.id,
        phone_number="1234567890"
    )
    db_session.add(phone)
    await db_session.commit()

    return {
        "building": building,
        "category": category,
        "company": company,
        "phone": phone
    }


@pytest.mark.asyncio(loop_scope="session")
async def test_create_company(client, test_data):
    response = await client.post(
        "/companies/",
        json={
            "name": "New Company",
            "phone_numbers": ["9876543210"],
            "building_id": test_data["building"].id,
            "categories": [test_data["category"].id]
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "New Company"
    assert data["phone_numbers"] == ["9876543210"]
    assert data["building_id"] == test_data["building"].id
    assert data["categories"][0]["category_id"] == test_data["category"].id


@pytest.mark.asyncio(loop_scope="session")
async def test_get_company_by_id(client, test_data):
    response = await client.get(f"/companies/{test_data['company'].id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data[0]["name"] == test_data["company"].name
    assert data[0]["building_id"] == test_data["building"].id
    assert data[0]["categories"][0]["category_id"] == test_data["category"].id


@pytest.mark.asyncio(loop_scope="session")
async def test_get_nonexistent_company(client):
    response = await client.get("/companies/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio(loop_scope="session")
async def test_search_companies_by_name(client, test_data):
    comp_name = test_data['company'].name
    response = await client.get(
        f"/companies/search/by-company-name",
        params={"company_name": comp_name}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data[0]["name"] == comp_name


@pytest.mark.asyncio(loop_scope="session")
async def test_search_companies_in_area(client, test_data):
    response = await client.post(
        "/companies/search/in-area",
        json={
            "radius": 1000,
            "longitude": 1.0,
            "latitude": 2.0
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0
    assert data[0]["name"] == test_data["company"].name


@pytest.mark.asyncio(loop_scope="session")
async def test_get_companies_by_category_id(client, test_data):
    cat_id = test_data['category'].id
    response = await client.get(
        f"/companies/search/by-category-id?category_id={cat_id}"
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0
    assert data[0]["category_id"] == cat_id
    assert data[0]["category_name"] == test_data["category"].name


@pytest.mark.asyncio(loop_scope="session")
async def test_advanced_search_companies(client, test_data):
    response = await client.get(
        "/companies/search/advanced",
        params={
            "name": test_data["company"].name,
            "category_id": test_data["category"].id,
            "phone_number": "890",
            "building_id": test_data["building"].id
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0
    assert data[0]["name"] == test_data["company"].name
