"""Module for generating initial test data"""
import asyncio
import logging
import random

from sqlalchemy import text

from app.database import get_session
from app.models import Building, Company, PhoneNumber, Category


async def load_initial_data():
    async for db in get_session():
        await db.execute(text(
            "TRUNCATE TABLE phone_numbers, companies, buildings, categories, "
            "company_category_association RESTART IDENTITY CASCADE"
        ))
        await db.commit()

        # create categories
        categories = [
            # level 1
            Category(name="Food & Beverage", parent_id=None),
            Category(name="Retail", parent_id=None),
            Category(name="Services", parent_id=None),

            # level 2
            Category(name="Restaurants", parent_id=1),
            Category(name="Cafes", parent_id=1),
            Category(name="Supermarkets", parent_id=2),
            Category(name="Clothing Stores", parent_id=2),
            Category(name="Banks", parent_id=3),
            Category(name="Beauty Salons", parent_id=3),

            # level 3
            Category(name="Italian Restaurants", parent_id=4),
            Category(name="Sushi Bars", parent_id=4),
            Category(name="Coffee Shops", parent_id=5),
        ]
        db.add_all(categories)
        await db.commit()

        # create buildings
        buildings_data = [
            {"address": "Tverskaya St, 10",
             "coordinates": "POINT(37.6119 55.7616)"},
            {"address": "Arbat St, 25",
             "coordinates": "POINT(37.5902 55.7496)"},
            {"address": "Kutuzovsky Prospekt, 30",
             "coordinates": "POINT(37.5416 55.7407)"},
            {"address": "Leninsky Prospekt, 50",
             "coordinates": "POINT(37.5739 55.6974)"},
            {"address": "Novy Arbat, 15",
             "coordinates": "POINT(37.5831 55.7522)"},
            {"address": "Pokrovka St, 22",
             "coordinates": "POINT(37.6394 55.7612)"},
            {"address": "Smolenskaya St, 8",
             "coordinates": "POINT(37.5827 55.7473)"},
            {"address": "Manezhnaya Sq, 1",
             "coordinates": "POINT(37.6138 55.7558)"},
            {"address": "Gorky Park, 9",
             "coordinates": "POINT(37.6047 55.7296)"},
            {"address": "Bolshaya Dmitrovka, 7",
             "coordinates": "POINT(37.6156 55.7611)"},
        ]
        buildings = [
            Building(
                address=b["address"],
                coordinates=b["coordinates"]
            ) for b in buildings_data
        ]
        db.add_all(buildings)
        await db.commit()

        # create companies
        company_names = [
            "Delicious Bistro", "Urban Cafe", "MegaMarket", "Fashion Boutique",
            "QuickBank", "Glamour Salon", "Pasta Place", "Sushi Express",
            "Java Coffee", "Trendy Outfitters", "Fresh Grocery",
            "Elegant Nails", "Pizza Heaven", "Burger Spot", "Tech Store",
            "Luxury Watches", "Healthy Pharmacy", "Book Haven", "Sports Gear",
            "Pet Paradise"
        ]
        phone_codes = ["495", "499", "800", "812"]

        for i in range(1, 101):
            building = random.choice(buildings)
            name = f"{random.choice(company_names)} #{i}"
            phone_code = random.choice(phone_codes)
            spare_numbers = random.randint(1000000, 9999999)
            phone_numbers = [
                f"+7{phone_code}{spare_numbers}"
                for _ in range(random.randint(1, 3))
            ]

            # choose 1-3 random categories
            selected_categories = random.sample(
                categories, k=random.randint(1, 3)
            )

            company = Company(
                name=name,
                building_id=building.id,
                categories=selected_categories
            )
            db.add(company)
            await db.flush()

            for num in phone_numbers:
                db.add(PhoneNumber(
                    phone_number=num,
                    company_id=company.id
                ))

        await db.commit()
        print("Initial data is loaded")


if __name__ == "__main__":
    print("Loading initial data")
    # silent stdout for this script
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    asyncio.run(load_initial_data())
