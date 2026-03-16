from datetime import date, timedelta

from sqlalchemy import select

from . import models


def seed_data(db):
    if db.execute(select(models.Supplier)).first():
        return

    suppliers = [
        models.Supplier(name='Forge Components', category='electronics', lead_time_days=10, on_time_rate=0.94, quality_score=0.91, risk_score=0.18, certifications='ISO9001, ITAR', preferred=1),
        models.Supplier(name='Northwind Circuits', category='electronics', lead_time_days=7, on_time_rate=0.89, quality_score=0.88, risk_score=0.24, certifications='ISO9001', preferred=0),
        models.Supplier(name='Atlas Fabrication', category='metal', lead_time_days=12, on_time_rate=0.96, quality_score=0.93, risk_score=0.16, certifications='ISO9001, AS9100', preferred=1),
        models.Supplier(name='RapidMach', category='metal', lead_time_days=6, on_time_rate=0.84, quality_score=0.82, risk_score=0.36, certifications='ISO9001', preferred=0),
    ]
    db.add_all(suppliers)
    db.flush()

    requisitions = [
        models.Requisition(title='Rugged sensor boards for drone line', category='electronics', quantity=180, needed_by=date.today() + timedelta(days=18), priority='high', required_certifications='ISO9001, ITAR'),
        models.Requisition(title='Precision mounting brackets', category='metal', quantity=260, needed_by=date.today() + timedelta(days=24), priority='medium', required_certifications='ISO9001'),
    ]
    db.add_all(requisitions)
    db.flush()

    quotes = [
        models.Quote(requisition_id=requisitions[0].id, supplier_id=suppliers[0].id, unit_price=74, available_qty=180, lead_time_days=9, note='Can reserve full batch this week.'),
        models.Quote(requisition_id=requisitions[0].id, supplier_id=suppliers[1].id, unit_price=69, available_qty=150, lead_time_days=7, note='Partial batch now, remainder next cycle.'),
        models.Quote(requisition_id=requisitions[1].id, supplier_id=suppliers[2].id, unit_price=31, available_qty=260, lead_time_days=11, note='Stable quality with aerospace line capacity.'),
        models.Quote(requisition_id=requisitions[1].id, supplier_id=suppliers[3].id, unit_price=44, available_qty=260, lead_time_days=6, note='Fast delivery but material source recently changed.'),
    ]
    signals = [
        models.DemandSignal(category='electronics', week_index=1, units=120),
        models.DemandSignal(category='electronics', week_index=2, units=126),
        models.DemandSignal(category='electronics', week_index=3, units=141),
        models.DemandSignal(category='electronics', week_index=4, units=155),
        models.DemandSignal(category='metal', week_index=1, units=190),
        models.DemandSignal(category='metal', week_index=2, units=188),
        models.DemandSignal(category='metal', week_index=3, units=196),
        models.DemandSignal(category='metal', week_index=4, units=205),
    ]
    db.add_all(quotes + signals)
    db.commit()
