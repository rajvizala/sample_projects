"""
Seed the database with realistic procurement data for demonstration.

Usage:
    python -m app.ml.seed_data
"""

import random
from datetime import date, timedelta

from app.core.database import init_db, SessionLocal
from app.models.procurement import Supplier, PurchaseOrder, SpendRecord

random.seed(42)

SUPPLIERS = [
    {"name": "Apex Manufacturing Co.", "category": "Raw Materials", "country": "US", "years": 12},
    {"name": "GlobalTech Components", "category": "Electronics", "country": "TW", "years": 8},
    {"name": "Pacific Shipping Lines", "category": "Logistics", "country": "SG", "years": 15},
    {"name": "Rhine Chemical GmbH", "category": "Chemicals", "country": "DE", "years": 20},
    {"name": "Midwest Steel Corp", "category": "Raw Materials", "country": "US", "years": 10},
    {"name": "ShenZhen Microelectronics", "category": "Electronics", "country": "CN", "years": 5},
    {"name": "Nordic Paper AB", "category": "Packaging", "country": "SE", "years": 18},
    {"name": "Delta Logistics Inc", "category": "Logistics", "country": "US", "years": 7},
    {"name": "Iberian Plastics SA", "category": "Raw Materials", "country": "ES", "years": 9},
    {"name": "Yamato Precision Ltd", "category": "Electronics", "country": "JP", "years": 25},
    {"name": "Green Valley Organics", "category": "Raw Materials", "country": "US", "years": 3},
    {"name": "Atlas IT Services", "category": "Services", "country": "IN", "years": 6},
]

ITEMS_BY_CATEGORY = {
    "Raw Materials": [
        ("Steel Plates (Grade A)", 150, 250),
        ("Aluminum Ingots", 80, 140),
        ("Copper Wire (1mm)", 200, 350),
        ("Industrial Rubber Sheets", 45, 90),
        ("Carbon Fiber Rolls", 500, 900),
    ],
    "Electronics": [
        ("Microcontroller MCU-7200", 12, 25),
        ("PCB Assembly Kit", 35, 65),
        ("LED Display Module", 22, 45),
        ("Power Supply Unit 500W", 40, 80),
        ("Sensor Array Module", 55, 110),
    ],
    "Logistics": [
        ("Container Shipping (20ft)", 2000, 4500),
        ("Air Freight (per kg)", 5, 15),
        ("Warehousing (monthly)", 3000, 6000),
        ("Last Mile Delivery", 15, 45),
    ],
    "Chemicals": [
        ("Industrial Solvent (L)", 25, 55),
        ("Adhesive Compound (kg)", 35, 75),
        ("Coating Agent (L)", 60, 120),
        ("Cleaning Solution (L)", 10, 25),
    ],
    "Packaging": [
        ("Corrugated Box (Large)", 2, 5),
        ("Shrink Wrap Roll", 15, 35),
        ("Foam Insert Custom", 3, 8),
        ("Pallet (Standard)", 12, 25),
    ],
    "Services": [
        ("IT Support (hourly)", 75, 150),
        ("Cloud Hosting (monthly)", 500, 2000),
        ("Security Audit", 5000, 15000),
        ("Data Migration", 3000, 10000),
    ],
}


def seed_database():
    """Populate database with 2 years of realistic procurement data."""
    init_db()
    db = SessionLocal()

    try:
        if db.query(Supplier).count() > 0:
            print("Database already seeded. Skipping.")
            return

        print("Seeding suppliers...")
        supplier_objs = []
        for s in SUPPLIERS:
            on_time = round(random.uniform(0.70, 0.99), 2)
            defect = round(random.uniform(0.005, 0.08), 3)
            avg_del = round(random.uniform(3, 21), 1)
            supplier = Supplier(
                name=s["name"],
                category=s["category"],
                country=s["country"],
                contact_email=f"sales@{s['name'].lower().replace(' ', '').replace('.', '')}.com",
                on_time_rate=on_time,
                defect_rate=defect,
                avg_delivery_days=avg_del,
                metadata_json={"years_in_business": s["years"]},
            )
            db.add(supplier)
            supplier_objs.append(supplier)
        db.flush()

        print("Generating purchase orders and spend records...")
        start_date = date.today() - timedelta(days=730)
        po_counter = 1000

        for supplier in supplier_objs:
            items = ITEMS_BY_CATEGORY.get(supplier.category, ITEMS_BY_CATEGORY["Raw Materials"])
            orders_per_month = random.randint(2, 6)
            total_spend = 0.0
            order_count = 0

            current_date = start_date
            while current_date < date.today():
                for _ in range(orders_per_month):
                    item_name, price_low, price_high = random.choice(items)
                    quantity = random.randint(5, 200)
                    unit_price = round(random.uniform(price_low, price_high), 2)

                    trend_factor = 1 + (current_date - start_date).days / 730 * random.uniform(-0.1, 0.15)
                    unit_price *= trend_factor

                    if random.random() < 0.03:
                        unit_price *= random.uniform(2.0, 4.0)

                    total = round(quantity * unit_price, 2)
                    order_date = current_date + timedelta(days=random.randint(0, 28))
                    if order_date >= date.today():
                        break

                    po_counter += 1
                    delivery_days = int(supplier.avg_delivery_days + random.gauss(0, 3))
                    delivery_date = order_date + timedelta(days=max(delivery_days, 1))

                    status = "delivered"
                    if delivery_date > date.today():
                        status = "in_transit" if random.random() > 0.3 else "pending"

                    po = PurchaseOrder(
                        po_number=f"PO-{po_counter:05d}",
                        supplier_id=supplier.id,
                        status=status,
                        order_date=order_date,
                        delivery_date=delivery_date if status == "delivered" else None,
                        total_amount=total,
                        category=supplier.category,
                        payment_terms=random.choice(["Net 30", "Net 45", "Net 60", "Due on Receipt"]),
                        line_items_json=[{
                            "item": item_name,
                            "qty": quantity,
                            "unit_price": round(unit_price, 2),
                            "total": total,
                        }],
                    )
                    db.add(po)

                    is_anomaly = unit_price > price_high * 1.8
                    spend = SpendRecord(
                        supplier_id=supplier.id,
                        category=supplier.category,
                        amount=total,
                        quantity=quantity,
                        unit_price=round(unit_price, 2),
                        spend_date=order_date,
                        item_name=item_name,
                        is_anomaly=int(is_anomaly),
                        anomaly_reason="Price spike" if is_anomaly else None,
                    )
                    db.add(spend)

                    total_spend += total
                    order_count += 1

                current_date += timedelta(days=30)

            supplier.total_spend = round(total_spend, 2)
            supplier.order_count = order_count

        db.commit()
        print(f"Seeded {len(supplier_objs)} suppliers with ~{po_counter - 1000} purchase orders.")
        print("Seed complete.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
