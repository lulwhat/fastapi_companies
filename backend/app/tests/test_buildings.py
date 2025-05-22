import pytest
import pytest_asyncio
from fastapi import status
from geoalchemy2 import WKTElement

from models import Building


@pytest_asyncio.fixture
async def test_building(db_session):
    building = Building(
        address="123 Test St",
        coordinates=WKTElement("POINT (1.0 2.0)", srid=4326),
    )
    db_session.add(building)
    await db_session.commit()
    return building


@pytest.mark.asyncio(loop_scope="session")
async def test_create_building(client):
    response = await client.post(
        "/buildings/",
        json={
            "address": "456 New St",
            "coordinates": {"longitude": 1.0,
                            "latitude": 2.0}
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["address"] == "456 New St"
    assert data["coordinates"]["longitude"] == 1.0
    assert data["coordinates"]["latitude"] == 2.0


@pytest.mark.asyncio(loop_scope="session")
async def test_get_building_by_id(client, test_building):
    response = await client.get(f"/buildings/{test_building.id}")
    assert response.status_code == status.HTTP_200_OK, response
    data = response.json()
    assert data["address"] == test_building.address
    wkt_str = (f"POINT ({data["coordinates"]["longitude"]} "
               f"{data["coordinates"]["latitude"]})")
    expected_point = WKTElement(wkt_str, srid=4326)
    assert expected_point == test_building.coordinates


@pytest.mark.asyncio(loop_scope="session")
async def test_get_nonexistent_building(client):
    response = await client.get("/buildings/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
