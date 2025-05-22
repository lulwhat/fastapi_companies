import asyncio

import pytest
import pytest_asyncio
from fastapi import status
from geoalchemy2 import WKTElement

from models import Building, Category
from rabbitmq.consumer import consume
from rabbitmq.export_service import process_task


@pytest_asyncio.fixture
async def test_integration_data(db_session):
    # Create test building
    building = Building(
        address="123 Integration St",
        coordinates=WKTElement("POINT (1.0 2.0)", srid=4326)
    )
    db_session.add(building)
    await db_session.commit()

    # Create parent category
    parent_category = Category(name="Parent Category")
    db_session.add(parent_category)
    await db_session.commit()

    # Create child categories
    child_categories = [
        Category(name="Child Category 1", parent_id=parent_category.id),
        Category(name="Child Category 2", parent_id=parent_category.id)
    ]
    for category in child_categories:
        db_session.add(category)
    await db_session.commit()

    return {
        "building": building,
        "parent_category": parent_category,
        "child_categories": child_categories
    }


@pytest.fixture(scope="session")
async def rabbitmq_consumer():
    consumer_task = asyncio.create_task(consume())
    yield
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio(loop_scope="session")
async def test_company_creation_with_category_hierarchy(
        client, test_integration_data
):
    """Test creating a company with categories
    from different levels of hierarchy"""
    # Create company with parent and child categories
    response = await client.post(
        "/companies/",
        json={
            "name": "Integration Test Company",
            "phone_numbers": ["1234567890"],
            "building_id": test_integration_data["building"].id,
            "categories": [
                test_integration_data["parent_category"].id,
                test_integration_data["child_categories"][0].id
            ]
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    company_data = response.json()

    # Verify company was created with correct categories
    assert len(company_data["categories"]) == 2
    cat_ids = [cat["category_id"] for cat in company_data["categories"]]
    assert (
            test_integration_data["parent_category"].id in cat_ids
    )
    assert (
            test_integration_data["child_categories"][0].id in cat_ids
    )

    # Test searching company by parent category
    response = await client.get(
        f"/companies/search/by-category-id",
        params={"category_id": test_integration_data['parent_category'].id}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0
    assert any(
        cat["category_name"] == test_integration_data["parent_category"].name
        for cat in data
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_company_search_and_export_flow(
        client, db_session, test_integration_data
):
    """Test the complete flow of searching companies and exporting results"""
    # Create multiple companies in the same building
    companies = []
    for i in range(3):
        response = await client.post(
            "/companies/",
            json={
                "name": f"Company {i}",
                "phone_numbers": [f"123456789{i}"],
                "building_id": test_integration_data["building"].id,
                "categories": [
                    test_integration_data["child_categories"][i % 2].id]
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        companies.append(response.json())

    # Search companies in area
    response = await client.post(
        "/companies/search/in-area",
        json={
            "radius": 1000,
            "longitude": 1.0,
            "latitude": 2.0
        }
    )
    assert response.status_code == status.HTTP_200_OK
    area_companies = response.json()
    assert len(area_companies) > 0

    # Export companies from the area and check data for download
    response_create = await client.post(
        "/export/", params={"export_table": "companies"}
    )
    assert response_create.status_code == status.HTTP_200_OK
    data_create = response_create.json()
    assert data_create["status"] == "pending"
    assert "task_id" in data_create
    await process_task(db_session, data_create["task_id"])
    await asyncio.sleep(0.5)  # wait for task to be finished

    response_check = await client.get(
        f"/export/status/{data_create['task_id']}"
    )
    assert response_check.status_code == status.HTTP_200_OK
    data_check = response_check.json()
    assert data_check["status"] == "completed"

    response_download = await client.get(
        f"/export/download/{data_create['task_id']}"
    )
    assert response_download.status_code == status.HTTP_200_OK

    assert (
            "text/csv" in response_download.headers["content-type"]
    )
    assert response_download.headers["content-disposition"].startswith(
        "attachment; filename="
    )
    content = response_download.text
    assert "Company 0" in content
    assert "1234567890" in content


@pytest.mark.asyncio(loop_scope="session")
async def test_building_company_category_integration(
        client, test_integration_data
):
    """Test integration between buildings, companies, and categories"""
    # Create a new building
    building_response = await client.post(
        "/buildings/",
        json={
            "address": "456 Integration Ave",
            "coordinates": {"longitude": 1.1,
                            "latitude": 2.1}
        }
    )
    assert building_response.status_code == status.HTTP_201_CREATED
    new_building = building_response.json()

    # Create companies in the new building
    for category in test_integration_data["child_categories"]:
        response = await client.post(
            "/companies/",
            json={
                "name": f"Company in New Building - {category.name}",
                "phone_numbers": ["9876543210"],
                "building_id": new_building["id"],
                "categories": [category.id]
            }
        )
        assert response.status_code == status.HTTP_201_CREATED

    # Search for companies in both buildings
    response = await client.post(
        "/companies/search/in-area",
        json={
            "radius": 10000,
            "longitude": 1.05,
            "latitude": 2.05
        }
    )
    assert response.status_code == status.HTTP_200_OK
    area_companies = response.json()
    assert len(area_companies) > 0

    # Export companies from the area
    response = await client.post(
        "/export/", params={"export_table": "companies"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "pending"
    assert "task_id" in data
