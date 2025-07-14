from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, joinedload
import random
import uuid

from .app import App

Base = declarative_base()


class Animal(Base):
    __tablename__ = 'animals'

    # Columns
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    logo_path = Column(String, nullable=False)
    pin_path = Column(String, nullable=False)

    # Relationships
    sightings = relationship('Sighting', back_populates='animal')

    def __repr__(self):
        return (
            f"<Animal(id={self.id}, "
            f"name={self.name}, "
            f"logo_path={self.logo_path}, "
            f"pin_path={self.pin_path})>"
        )

    @classmethod
    def all(cls):
        Session = App.get_persistent_store_database('primary_db', as_sessionmaker=True)
        with Session() as session:
            return session.query(cls).options(joinedload(cls.sightings)).all()

    @classmethod
    def get_by_id(cls, animal_id):
        Session = App.get_persistent_store_database('primary_db', as_sessionmaker=True)
        with Session() as session:
            stmt = select(cls).options(joinedload(cls.sightings)).filter_by(id=animal_id)
            result = session.execute(stmt).scalars().first()
            return result


class Sighting(Base):
    __tablename__ = 'sightings'

    # Columns
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date_time = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    animal_id = Column(Integer, ForeignKey('animals.id'), nullable=False)

    # Relationships
    animal = relationship('Animal', back_populates='sightings')

    def __repr__(self):
        return (
            f"<Sighting(id={self.id}, "
            f"date_time={self.date_time}, "
            f"latitude={self.latitude}, "
            f"longitude={self.longitude}, "
            f"animal={self.animal})>")

    @classmethod
    def add(cls, animal_id, date_time, latitude, longitude):
        if not isinstance(date_time, datetime):
            raise ValueError("date_time must be a datetime object")

        new_sighting = Sighting(
            animal_id=animal_id,
            date_time=date_time,
            latitude=latitude,
            longitude=longitude
        )

        Session = App.get_persistent_store_database('primary_db', as_sessionmaker=True)
        with Session() as session:
            session.add(new_sighting)
            session.commit()

    @classmethod
    def delete(cls, sighting_id):
        Session = App.get_persistent_store_database('primary_db', as_sessionmaker=True)
        with Session() as session:
            sighting = session.query(Sighting).filter(Sighting.id == sighting_id).first()
            if sighting:
                session.delete(sighting)
                session.commit()
                return True
        return False

    @classmethod
    def all(cls):
        Session = App.get_persistent_store_database('primary_db', as_sessionmaker=True)
        with Session() as session:
            return session.query(cls).options(joinedload(cls.animal)).all()


def _register_valid_animals():
    images_path = '/static/wildatlas/images'
    registered_animals = [
        Animal(name='Bear', logo_path=f'{images_path}/bear_logo.svg', pin_path=f'{images_path}/bear_pin.svg'),
        Animal(name='Beaver', logo_path=f'{images_path}/beaver_logo.svg', pin_path=f'{images_path}/beaver_pin.svg'),
        Animal(name='Bison', logo_path=f'{images_path}/bison_logo.svg', pin_path=f'{images_path}/bison_pin.svg'),
        Animal(name='Bobcat', logo_path=f'{images_path}/bobcat_logo.svg', pin_path=f'{images_path}/bobcat_pin.svg'),
        Animal(name='Cougar', logo_path=f'{images_path}/cougar_logo.svg', pin_path=f'{images_path}/cougar_pin.svg'),
        Animal(name='Elk', logo_path=f'{images_path}/elk_logo.svg', pin_path=f'{images_path}/elk_pin.svg'),
        Animal(name='Lynx', logo_path=f'{images_path}/lynx_logo.svg', pin_path=f'{images_path}/lynx_pin.svg'),
        Animal(name='Moose', logo_path=f'{images_path}/moose_logo.svg', pin_path=f'{images_path}/moose_pin.svg'),
        Animal(name='Otter', logo_path=f'{images_path}/otter_logo.svg', pin_path=f'{images_path}/otter_pin.svg'),
        Animal(name='Red Fox', logo_path=f'{images_path}/redfox_logo.svg', pin_path=f'{images_path}/redfox_pin.svg'),
        Animal(name='Wolf', logo_path=f'{images_path}/wolf_logo.svg', pin_path=f'{images_path}/wolf_pin.svg')
    ]

    Session = App.get_persistent_store_database('primary_db', as_sessionmaker=True)
    with Session() as session:
        # Ensure no duplicate animals are registered here. From this point on animal ID's can and should be used.
        for animal_to_add in registered_animals:
            if not session.query(Animal).filter(Animal.name == animal_to_add.name).first():
                session.add(animal_to_add)
                print(f"Registered animal: {animal_to_add}")

        session.commit()


def _generate_random_sightings():
    registered_animals = Animal.all()

    # Approximate bounding box for Yellowstone National Park
    max_lat, max_lon = 45.05, -110.25
    min_lat, min_lon = 44.15, -110.75

    for animal in registered_animals:
        days_ago = random.randint(0, 15)
        starting_date = datetime.now()
        # starting_date = datetime(2025, 7, 14, 14, 30, 0)
        start_date = starting_date - timedelta(days=30)
        sighting_date = start_date - timedelta(days=days_ago)
        latitude = round(random.uniform(min_lat, max_lat), 6)
        longitude = round(random.uniform(min_lon, max_lon), 6)
        Sighting.add(
            animal.id,
            date_time=sighting_date,
            latitude=latitude,
            longitude=longitude
        )
    print(f'Generated {len(registered_animals)} random sightings.')


def init_primary_db(engine, first_time):
    """
    Initialize the primary database.
    """
    Base.metadata.create_all(engine)
    _register_valid_animals()

    if first_time:
        _generate_random_sightings()
