import pytest
from datetime import datetime, timedelta, UTC
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.database import Base
from app.services.auth_service import AuthService
from app.services.trip_service import TripService
from app.services.city_service import CityService
from app.services.sharing_service import SharingService
from app.services.admin_service import AdminService
from app.schemas.trip import TripCreate, StopCreate, ActivityCreate
from app.schemas.city import CityCreate, CitySearchParams
from app.models.city import City, ActivityCatalog, ActivityType


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for isolated unit testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_auth_flow(db_session: Session):
    auth_service = AuthService(db_session)

    # 1. Signup
    user = auth_service.signup(
        email="traveler@example.com",
        password="securepassword123",
        full_name="Alex Wanderer",
    )
    db_session.commit()

    assert user.id is not None
    assert user.email == "traveler@example.com"
    assert user.full_name == "Alex Wanderer"

    # 2. Login
    logged_in_user = auth_service.login("traveler@example.com", "securepassword123")
    assert logged_in_user.id == user.id

    # 3. Update Profile
    updated_user = auth_service.update_profile(user.id, full_name="Alex Master Wanderer", language_pref="es")
    db_session.commit()
    assert updated_user.full_name == "Alex Master Wanderer"
    assert updated_user.language_pref == "es"


def test_city_and_trip_planning(db_session: Session):
    auth_service = AuthService(db_session)
    city_service = CityService(db_session)
    trip_service = TripService(db_session)

    # Create user
    user = auth_service.signup(email="planner@example.com", password="password123")
    db_session.commit()

    # Create Cities
    paris = city_service.create_city(
        CityCreate(name="Paris", country="France", country_code="FR", region="Europe", cost_index=80)
    )
    rome = city_service.create_city(
        CityCreate(name="Rome", country="Italy", country_code="IT", region="Europe", cost_index=65)
    )
    db_session.commit()

    # Search Cities
    found_cities, count = city_service.search_cities(CitySearchParams(q="Par"))
    assert count == 1
    assert found_cities[0].name == "Paris"

    # Create Trip
    start = datetime(2026, 9, 1, tzinfo=UTC)
    end = datetime(2026, 9, 10, tzinfo=UTC)
    trip = trip_service.create_trip(
        user.id,
        TripCreate(
            name="European Odyssey",
            start_date=start,
            end_date=end,
            total_budget=2000.0,
        ),
    )
    db_session.commit()
    assert trip.id is not None
    assert trip.name == "European Odyssey"

    # Add Stop 1: Paris
    stop1 = trip_service.add_stop(
        trip.id,
        user.id,
        StopCreate(
            city_id=paris.id,
            arrival_date=start,
            departure_date=start + timedelta(days=4),
            stop_order=1,
        ),
    )
    # Add Stop 2: Rome
    stop2 = trip_service.add_stop(
        trip.id,
        user.id,
        StopCreate(
            city_id=rome.id,
            arrival_date=start + timedelta(days=5),
            departure_date=end,
            stop_order=2,
        ),
    )
    db_session.commit()

    # Add Activities to Stop 1
    act1 = trip_service.add_activity(
        trip.id,
        user.id,
        stop1.id,
        ActivityCreate(
            name="Eiffel Tower Tour",
            activity_type="sightseeing",
            start_time=start + timedelta(hours=10),
            end_time=start + timedelta(hours=12),
            estimated_cost=35.0,
        ),
    )
    act2 = trip_service.add_activity(
        trip.id,
        user.id,
        stop1.id,
        ActivityCreate(
            name="Louvre Museum Walk",
            activity_type="culture",
            start_time=start + timedelta(days=1, hours=14),
            end_time=start + timedelta(days=1, hours=17),
            estimated_cost=20.0,
        ),
    )
    db_session.commit()

    # Test Budget Breakdown
    budget_info = trip_service.get_budget_breakdown(trip.id, user.id)
    assert budget_info["activities"] == 55.0
    assert budget_info["accommodation"] > 0
    assert budget_info["meals"] > 0
    assert budget_info["total"] > budget_info["activities"]
    assert budget_info["average_per_day"] > 0

    # Test Calendar Timeline
    calendar_days = trip_service.get_calendar(trip.id, user.id)
    assert len(calendar_days) == 10  # 10 days duration
    day1_activities = calendar_days[0]["activities"]
    assert len(day1_activities) == 1
    assert day1_activities[0].name == "Eiffel Tower Tour"


def test_sharing_and_cloning(db_session: Session):
    auth_service = AuthService(db_session)
    city_service = CityService(db_session)
    trip_service = TripService(db_session)
    sharing_service = SharingService(db_session)

    # Users
    alice = auth_service.signup(email="alice@example.com", password="password123", full_name="Alice")
    bob = auth_service.signup(email="bob@example.com", password="password123", full_name="Bob")
    tokyo = city_service.create_city(CityCreate(name="Tokyo", country="Japan", country_code="JP", region="Asia"))
    db_session.commit()

    # Alice creates a trip
    start = datetime(2026, 10, 1, tzinfo=UTC)
    end = datetime(2026, 10, 5, tzinfo=UTC)
    trip = trip_service.create_trip(
        alice.id,
        TripCreate(name="Tokyo Tech & Food", start_date=start, end_date=end, total_budget=1500.0),
    )
    stop = trip_service.add_stop(
        trip.id,
        alice.id,
        StopCreate(city_id=tokyo.id, arrival_date=start, departure_date=end),
    )
    trip_service.add_activity(
        trip.id,
        alice.id,
        stop.id,
        ActivityCreate(
            name="Shinjuku Food Tour",
            activity_type="food",
            start_time=start + timedelta(hours=18),
            end_time=start + timedelta(hours=21),
            estimated_cost=60.0,
        ),
    )
    db_session.commit()

    # Alice shares the trip
    share = sharing_service.create_share(trip.id, alice.id)
    db_session.commit()
    assert share.share_slug is not None

    # Public View
    public_trip = sharing_service.get_public_trip(share.share_slug)
    assert public_trip.id == trip.id

    # Bob clones the trip
    bob_trip = sharing_service.copy_trip(share.share_slug, bob.id)
    db_session.commit()

    assert bob_trip.user_id == bob.id
    assert "Copy" in bob_trip.name
    assert len(bob_trip.stops) == 1
    assert len(bob_trip.stops[0].activities) == 1
    assert bob_trip.stops[0].activities[0].name == "Shinjuku Food Tour"


def test_admin_metrics(db_session: Session):
    auth_service = AuthService(db_session)
    admin_service = AdminService(db_session)

    # Seed users
    auth_service.signup(email="u1@example.com", password="password123")
    auth_service.signup(email="u2@example.com", password="password123")
    db_session.commit()

    stats = admin_service.get_stats()
    assert stats.total_users >= 2
