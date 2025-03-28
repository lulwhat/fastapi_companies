from typing import List

from geoalchemy2.shape import to_shape
from pydantic import BaseModel, ConfigDict


class PhoneNumber(BaseModel):
    phone_number: str


class Company(BaseModel):
    id: int
    name: str
    phone_numbers: List
    building_id: int
    categories: List


class Coordinates(BaseModel):
    longitude: float
    latitude: float

    @classmethod
    def from_wkb(cls, wkb_element):
        point = to_shape(wkb_element)
        return cls(longitude=point.x, latitude=point.y)


class Building(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int
    address: str
    coordinates: Coordinates


class BuildingCompanies(BaseModel):
    id: int
    address: str
    companies: List


class Category(BaseModel):
    id: int
    name: str
    parent_id: int | None = None
    children: List


class CompaniesByCategories(BaseModel):
    category_id: int
    category_name: str
    companies: dict
