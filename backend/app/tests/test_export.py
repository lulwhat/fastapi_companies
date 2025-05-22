import asyncio
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi import status
from geoalchemy2 import WKTElement

from models import Company, Building, Category, PhoneNumber
from rabbitmq.export_service import process_task


@pytest_asyncio.fixture
async def test_export_data(db_session):
    # Create test building
    building = Building(
        address="123 Test St",
        coordinates=WKTElement("POINT (1.0 2.0)", srid=4326)
    )
    db_session.add(building)
    await db_session.commit()

    # Create test categories
    categories = [
        Category(name="Category 1"),
        Category(name="Category 2")
    ]
    for category in categories:
        db_session.add(category)
    await db_session.commit()

    # Create test companies
    companies = [
        Company(
            name="Company 1",
            building_id=building.id,
            categories=[categories[0]]
        ),
        Company(
            name="Company 2",
            building_id=building.id,
            categories=[categories[1]]
        )
    ]
    for company in companies:
        db_session.add(company)
    await db_session.commit()

    # Add phone numbers
    phones = [
        PhoneNumber(company_id=companies[0].id, phone_number="1111111111"),
        PhoneNumber(company_id=companies[1].id, phone_number="2222222222")
    ]
    for phone in phones:
        db_session.add(phone)
    await db_session.commit()

    return {
        "building": building,
        "categories": categories,
        "companies": companies,
        "phones": phones
    }


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_check_export(client, db_session, test_export_data):
    response = await client.post(
        "/export/", params={"export_table": "companies"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    task_id = data["task_id"]
    assert data["status"] == "pending"

    # imitate bg_task from router and wait for task to be finished
    await process_task(db_session, task_id)
    await asyncio.sleep(0.5)

    response_check = await client.get(f"/export/status/{task_id}")
    assert response_check.status_code == status.HTTP_200_OK
    assert response_check.json()["status"] == "completed"


@pytest.mark.asyncio(loop_scope="session")
async def test_download_export_result(client, db_session, test_export_data):
    response_create = await client.post(
        "/export/",
        params={"export_table": "companies"}
    )
    assert response_create.status_code == status.HTTP_200_OK
    data_create = response_create.json()
    assert "task_id" in data_create

    # imitate bg_task from router and wait for task to be finished
    await process_task(db_session, data_create["task_id"])
    await asyncio.sleep(0.5)

    response_download = await client.get(
        f"/export/download/{data_create['task_id']}"
    )
    assert response_download.status_code == status.HTTP_200_OK
    assert "text/csv" in response_download.headers["content-type"]
