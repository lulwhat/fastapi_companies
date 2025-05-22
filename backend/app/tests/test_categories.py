import pytest
import pytest_asyncio
from fastapi import status

from models import Category


@pytest_asyncio.fixture
async def test_category(db_session):
    category = Category(name="Test Category", parent_id=None)
    db_session.add(category)
    await db_session.commit()
    return category


@pytest_asyncio.fixture
async def test_categories(db_session):
    categories = [
        Category(name="Parent Category"),
        Category(name="Child Category 1", parent_id=1),
        Category(name="Child Category 2", parent_id=1)
    ]
    for category in categories:
        db_session.add(category)
    await db_session.commit()
    return categories


@pytest.mark.asyncio(loop_scope="session")
async def test_create_category(client):
    response = await client.post(
        "/categories/",
        json={"name": "New Category", "parent_id": 0}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "New Category"


@pytest.mark.asyncio(loop_scope="session")
async def test_create_child_category(client, test_category):
    response = await client.post(
        "/categories/",
        json={
            "name": "Child Category",
            "parent_id": test_category.id
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Child Category"
    assert data["parent_id"] == test_category.id


@pytest.mark.asyncio(loop_scope="session")
async def test_get_category_by_id(client, test_category):
    response = await client.get(f"/categories/{test_category.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == test_category.name


@pytest.mark.asyncio(loop_scope="session")
async def test_get_nonexistent_category(client):
    response = await client.get("/categories/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio(loop_scope="session")
async def test_search_categories_by_name(client, test_category):
    response = await client.get(
        f"/categories/by-name/{test_category.name}"
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0
    assert data["name"] == test_category.name
