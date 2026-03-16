from sqlalchemy import select

from . import models


def seed_data(db):
    if db.execute(select(models.Person)).first():
        return

    people = [
        models.Person(name='Aarav', role='Dad', love_language='Acts of service', focus='Training for a charity run'),
        models.Person(name='Mira', role='Mom', love_language='Quality time', focus='Balancing work travel and home routines'),
        models.Person(name='Nia', role='Daughter', love_language='Words of affirmation', focus='Preparing for a school art fair'),
        models.Person(name='Kabir', role='Son', love_language='Play', focus='Obsessed with weekend soccer games'),
    ]
    db.add_all(people)
    db.flush()

    updates = [
        models.Update(person_id=people[0].id, category='fitness', text='I am tired after long training but excited about the charity run next month.', mood='tired'),
        models.Update(person_id=people[1].id, category='travel', text='Work trip got moved, so I can do dinner on Thursday if everyone is free.', mood='hopeful'),
        models.Update(person_id=people[2].id, category='school', text='My teacher loved the art fair draft and I want help framing it this weekend.', mood='proud'),
        models.Update(person_id=people[3].id, category='soccer', text='We won our soccer game and I want the family at practice on Saturday.', mood='excited'),
    ]
    memories = [
        models.Memory(title='Saturday pancake ritual', detail='The family cooked breakfast together before heading to the park.', people='Aarav, Mira, Nia, Kabir', importance=4),
        models.Memory(title='Art fair setup night', detail='Nia stayed up late with Mira cutting labels and arranging prints.', people='Mira, Nia', importance=3),
    ]
    db.add_all(updates + memories)
    db.commit()
