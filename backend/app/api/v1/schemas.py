from datetime import datetime
from typing import List, Dict

from fastapi import HTTPException, status
from fastapi.params import Query
from geoalchemy2.shape import to_shape
from pydantic import BaseModel, ConfigDict


# Company schemas
class CompanyCreate(BaseModel):
    name: str
    phone_numbers: List
    building_id: int
    categories: List


class CompanyResponse(BaseModel):
    id: int
    name: str
    phone_numbers: List
    building_id: int
    categories: List


class CompanyAdvancedSearchParams:
    def __init__(
        self,
        name: str | None = Query(
            None, description="Partial company name match"
        ),
        category_id: int | None = Query(
            None,
            description="Exact category ID (exclusive with category_name)"
        ),
        category_name: str | None = Query(
            None,
            description="Exact category name (exclusive with category_id)"
        ),
        phone_number: str | None = Query(
            None, description="Partial phone match"
        ),
        building_id: int | None = Query(
            None, description="Exact building ID"
        ),
        location: str | None = Query(
            None,
            description="Geographic search in format: "
                        "'longitude,latitude,radius_meters'"
        ),
    ):
        self.name = name
        self.category_id, self.category_name = self._validate_category(
            category_id, category_name
        )
        self.category_name = category_name
        self.phone_number = phone_number
        self.building_id = building_id
        self.location = self._validate_location(location)

    def _validate_location(self, location: str):
        if location is None:
            return None

        parts = location.split(",")
        if len(parts) != 3:
            raise HTTPException(
                detail="Location must be in format 'lon,lat,radius'",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        try:
            return float(parts[0]), float(parts[1]), int(parts[2])
        except ValueError:
            raise HTTPException(
                detail="Invalid location values",
                status_code=status.HTTP_400_BAD_REQUEST
            )

    def _validate_category(self, category_id, category_name):
        if category_id and category_name:
            raise HTTPException(
                detail="Use only one field at a time: "
                       "category_id or category_name",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        return category_id, category_name


# Building schemas
class Coordinates(BaseModel):
    longitude: float
    latitude: float

    @classmethod
    def from_wkb(cls, wkb_element):
        point = to_shape(wkb_element)
        return cls(longitude=point.x, latitude=point.y)


class BuildingCreate(BaseModel):
    address: str
    coordinates: Coordinates


class BuildingResponse(BaseModel):
    id: int
    address: str
    coordinates: Coordinates

    model_config = ConfigDict(arbitrary_types_allowed=True)


class BuildingCompaniesResponse(BaseModel):
    id: int
    address: str
    coordinates: Coordinates
    companies: List

    model_config = ConfigDict(arbitrary_types_allowed=True)


# Category schemas
class CategoryResponse(BaseModel):
    id: int
    name: str
    parent_id: int | None = None
    children: List


class CompaniesByCategoriesResponse(BaseModel):
    category_id: int
    category_name: str
    companies: List[Dict]


# Export schemas
class ExportStatus(BaseModel):
    task_id: int
    status: str
    export_table: str
    url: str | None
    created_at: datetime | None
    updated_at: datetime | None
