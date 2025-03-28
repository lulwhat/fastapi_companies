from geoalchemy2 import Geometry
from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy_utils import PhoneNumberType


Base = declarative_base()

company_category_association = Table(
    'company_category_association',
    Base.metadata,
    Column(
        'company_id', Integer, ForeignKey('companies.id'), primary_key=True
    ),
    Column(
        'category_id', Integer, ForeignKey('categories.id'), primary_key=True
    )
)


class PhoneNumber(Base):
    __tablename__ = 'phone_numbers'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    phone_number = Column(PhoneNumberType(region='RU'))
    company_id = Column(Integer, ForeignKey('companies.id'))
    company = relationship('Company', back_populates='phone_numbers')

    def __repr__(self):
        return (f'<PhoneNumber(id={self.id}, '
                f'phone_number={self.phone_number}, '
                f'company_id={self.company_id})>')


class Company(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String)
    phone_numbers = relationship(
        'PhoneNumber', back_populates='company', cascade='all',
        lazy='selectin'
    )
    building_id = Column(Integer, ForeignKey('buildings.id'))
    building = relationship('Building', back_populates='companies')
    categories = relationship(
        'Category',
        back_populates='companies',
        secondary=company_category_association,
        cascade='all',
        lazy='selectin'
    )

    def __repr__(self):
        return f'<Company(id={self.id}, name={self.name})>'


class   Building(Base):
    __tablename__ = 'buildings'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    address = Column(String)
    coordinates = Column(Geometry('POINT'))
    companies = relationship('Company', back_populates='building')

    def __repr__(self):
        return f'<Building(id={self.id}, address={self.address})>'


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    parent_id = Column(Integer, ForeignKey('categories.id'))
    name = Column(String, nullable=False)
    parent = relationship(
        'Category',
        remote_side=[id],
        back_populates='children'
    )
    children = relationship(
        'Category',
        back_populates='parent',
        lazy='selectin'
    )
    companies = relationship(
        'Company',
        back_populates='categories',
        secondary=company_category_association,
        cascade='all'
    )

    def __repr__(self):
        return (f'<Category(id={self.id}, name={self.name}, '
                f'parent_id={self.parent_id})>')
