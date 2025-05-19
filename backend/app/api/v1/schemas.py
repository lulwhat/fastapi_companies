from datetime import datetime
from typing import List, Dict

from geoalchemy2.shape import to_shape
from pydantic import BaseModel, ConfigDict


# Company schemas
class PhoneNumber(BaseModel):
    phone_number: str


class CompanyCreate(BaseModel):
    name: str
    phone_numbers: List
    building_id: int
    categories: List


class CompanyResponse(CompanyCreate):
    id: int


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


class BuildingResponse(BuildingCreate):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: int


class BuildingCompaniesResponse(BuildingResponse):
    companies: List


# Category schemas
class CategoryCreate(BaseModel):
    name: str
    parent_id: int | None = None


class CategoryResponse(CategoryCreate):
    id: int
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
