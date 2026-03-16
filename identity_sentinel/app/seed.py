import json

from sqlalchemy import select

from . import models


def seed_data(db):
    if db.execute(select(models.SignalEvent)).first():
        return

    events = [
        models.SignalEvent(channel='sms', sender='Dad', content='Running late from the office, home in 20 minutes.', country='US', hour=18, amount=0, new_device=False, new_ip=False, ai_voice_flag=False),
        models.SignalEvent(channel='email', sender='Payroll', content='Your salary stub is ready for review.', country='US', hour=9, amount=0, new_device=False, new_ip=False, ai_voice_flag=False),
        models.SignalEvent(channel='voice', sender='Kabir Coach', content='Practice starts at 8am on Saturday.', country='US', hour=17, amount=0, new_device=False, new_ip=False, ai_voice_flag=False),
        models.SignalEvent(channel='login', sender='BankApp', content='Successful login from your usual browser.', country='US', hour=8, amount=0, new_device=False, new_ip=False, ai_voice_flag=False),
        models.SignalEvent(channel='payment', sender='BankApp', content='Card purchase approved at the grocery store.', country='US', hour=14, amount=82, new_device=False, new_ip=False, ai_voice_flag=False),
        models.SignalEvent(channel='sms', sender='Mom', content='Can you pick up fruit on the way home?', country='US', hour=16, amount=0, new_device=False, new_ip=False, ai_voice_flag=False),
        models.SignalEvent(channel='email', sender='alerts@secure-wallet.io', content='Urgent: verify account and send OTP to stop suspension.', country='NL', hour=2, amount=0, new_device=True, new_ip=True, ai_voice_flag=False),
    ]
    db.add_all(events)
    db.flush()

    alert = models.Alert(
        signal_id=events[-1].id,
        severity='critical',
        score=91.0,
        summary='Critical risk email event from alerts@secure-wallet.io scored 91/100.',
        reasons=json.dumps([
            '2 known scam phrases detected',
            'sender is not on the normal trust list',
            'unexpected origin country: NL',
            'activity came from a new device',
            'activity came from a new network location',
        ]),
        action='Freeze sensitive actions, verify through a second trusted channel, and rotate passwords or session tokens now.',
    )
    db.add(alert)
    db.commit()
