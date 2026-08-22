from datetime import datetime, UTC
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.city import City, ActivityCatalog, ActivityType, ActivitySource


SEED_CITIES_DATA = [
    {
        "name": "Paris",
        "country": "France",
        "country_code": "FR",
        "region": "Europe",
        "timezone": "Europe/Paris",
        "cost_index": 78,
        "popularity_score": 98,
        "latitude": 48.8566,
        "longitude": 2.3522,
        "description": "The City of Light, famous for world-class art, culinary wonders, iconic monuments, and romantic river walks.",
        "activities": [
            {
                "name": "Eiffel Tower Sunset Summit Tour",
                "description": "Ascend to the summit of the Eiffel Tower during golden hour for panoramic vistas over Paris.",
                "activity_type": ActivityType.SIGHTSEEING,
                "avg_cost": 38.0,
                "duration_minutes": 120,
                "tags": ["landmark", "romantic", "viewpoint", "iconic"],
            },
            {
                "name": "Louvre Museum Masterpieces Walk",
                "description": "Guided exploration of the Mona Lisa, Venus de Milo, and French Renaissance masterpieces.",
                "activity_type": ActivityType.CULTURE,
                "avg_cost": 22.0,
                "duration_minutes": 180,
                "tags": ["art", "history", "museum"],
            },
            {
                "name": "Montmartre Artisanal Bakery & Pastry Tour",
                "description": "Taste fresh croissants, macarons, and artisanal cheeses in bohemian Montmartre.",
                "activity_type": ActivityType.FOOD,
                "avg_cost": 55.0,
                "duration_minutes": 150,
                "tags": ["foodie", "pastry", "wine", "walking"],
            },
            {
                "name": "Seine River Evening Dinner Cruise",
                "description": "Gourmet 3-course French dining gliding past illuminated bridges and Notre-Dame cathedral.",
                "activity_type": ActivityType.NIGHTLIFE,
                "avg_cost": 95.0,
                "duration_minutes": 120,
                "tags": ["dinner", "cruise", "romantic", "wine"],
            },
        ],
    },
    {
        "name": "Tokyo",
        "country": "Japan",
        "country_code": "JP",
        "region": "Asia",
        "timezone": "Asia/Tokyo",
        "cost_index": 72,
        "popularity_score": 96,
        "latitude": 35.6762,
        "longitude": 139.6503,
        "description": "Futuristic metropolis seamlessly blended with centuries-old temples, neon streetscapes, and unmatched cuisine.",
        "activities": [
            {
                "name": "Shinjuku & Shibuya Neon Night Food Crawl",
                "description": "Explore hidden izakayas in Omoide Yokocho and taste authentic yakitori, ramen, and sake.",
                "activity_type": ActivityType.FOOD,
                "avg_cost": 60.0,
                "duration_minutes": 180,
                "tags": ["izakaya", "ramen", "nightlife", "foodie"],
            },
            {
                "name": "Sensō-ji Temple & Asakusa Old Town Walk",
                "description": "Tokyo's oldest Buddhist temple, vibrant Nakamise shopping street, and historic incense rituals.",
                "activity_type": ActivityType.CULTURE,
                "avg_cost": 10.0,
                "duration_minutes": 120,
                "tags": ["temple", "tradition", "history", "souvenirs"],
            },
            {
                "name": "Mount Fuji & Lake Kawaguchi Day Trip",
                "description": "Scenic excursion to Mt. Fuji 5th station, pagoda viewpoints, and soothing lakeside views.",
                "activity_type": ActivityType.NATURE,
                "avg_cost": 110.0,
                "duration_minutes": 480,
                "tags": ["fuji", "mountain", "nature", "scenic"],
            },
            {
                "name": "Akihabara Tech & Anime Exploration",
                "description": "Dive into futuristic gaming arcades, retro tech bazaars, and vibrant pop culture shops.",
                "activity_type": ActivityType.SHOPPING,
                "avg_cost": 25.0,
                "duration_minutes": 150,
                "tags": ["anime", "gaming", "shopping", "tech"],
            },
        ],
    },
    {
        "name": "New York City",
        "country": "United States",
        "country_code": "US",
        "region": "North America",
        "timezone": "America/New_York",
        "cost_index": 92,
        "popularity_score": 97,
        "latitude": 40.7128,
        "longitude": -74.0060,
        "description": "The dynamic cultural hub featuring legendary skyscrapers, Broadway shows, Central Park, and diverse boroughs.",
        "activities": [
            {
                "name": "Broadway Musical Evening Show",
                "description": "Experience an award-winning theatrical performance in the heart of Times Square.",
                "activity_type": ActivityType.CULTURE,
                "avg_cost": 125.0,
                "duration_minutes": 180,
                "tags": ["theater", "broadway", "entertainment"],
            },
            {
                "name": "Central Park Guided Bike & Picnic Tour",
                "description": "Cycle through Strawberry Fields, Bethesda Terrace, and scenic lakes in Manhattan's crown jewel.",
                "activity_type": ActivityType.NATURE,
                "avg_cost": 35.0,
                "duration_minutes": 120,
                "tags": ["cycling", "park", "nature", "relaxing"],
            },
            {
                "name": "Empire State Building 86th Floor Deck",
                "description": "Gaze over Manhattan's skyline from the historic Art Deco skyscraper observatory.",
                "activity_type": ActivityType.SIGHTSEEING,
                "avg_cost": 44.0,
                "duration_minutes": 90,
                "tags": ["skyline", "viewpoint", "architecture"],
            },
            {
                "name": "Lower East Side & Soho Food Tasting",
                "description": "Sample historic pastrami on rye, New York style pizza slices, and artisanal bagels.",
                "activity_type": ActivityType.FOOD,
                "avg_cost": 65.0,
                "duration_minutes": 150,
                "tags": ["pizza", "bagel", "streetfood", "walking"],
            },
        ],
    },
    {
        "name": "Rome",
        "country": "Italy",
        "country_code": "IT",
        "region": "Europe",
        "timezone": "Europe/Rome",
        "cost_index": 68,
        "popularity_score": 94,
        "latitude": 41.9028,
        "longitude": 12.4964,
        "description": "The Eternal City with magnificent ancient ruins, Renaissance basilicas, and sunlit piazzas.",
        "activities": [
            {
                "name": "Colosseum & Roman Forum VIP Access",
                "description": "Step into the gladiatorial arena and walk the ancient pathways of Roman emperors.",
                "activity_type": ActivityType.CULTURE,
                "avg_cost": 45.0,
                "duration_minutes": 180,
                "tags": ["history", "ancient", "gladiator", "monument"],
            },
            {
                "name": "Trastevere Authentic Pasta & Gelato Masterclass",
                "description": "Learn handmade carbonara, cacio e pepe, and creamy Italian gelato in a rustic villa.",
                "activity_type": ActivityType.FOOD,
                "avg_cost": 75.0,
                "duration_minutes": 210,
                "tags": ["cooking", "pasta", "gelato", "wine"],
            },
            {
                "name": "Trevi Fountain & Spanish Steps Twilight Stroll",
                "description": "Toss a coin into the Trevi Fountain and stroll through Rome's grand baroque squares.",
                "activity_type": ActivityType.SIGHTSEEING,
                "avg_cost": 0.0,
                "duration_minutes": 90,
                "tags": ["fountain", "free", "architecture", "romantic"],
            },
        ],
    },
    {
        "name": "Dubai",
        "country": "United Arab Emirates",
        "country_code": "AE",
        "region": "Middle East",
        "timezone": "Asia/Dubai",
        "cost_index": 82,
        "popularity_score": 91,
        "latitude": 25.2048,
        "longitude": 55.2708,
        "description": "A futuristic desert oasis featuring ultra-modern architecture, luxury shopping, and desert safaris.",
        "activities": [
            {
                "name": "Burj Khalifa At The Top (Levels 124 & 125)",
                "description": "Ride high-speed elevators to the world's tallest building for sweeping skyline views.",
                "activity_type": ActivityType.SIGHTSEEING,
                "avg_cost": 50.0,
                "duration_minutes": 90,
                "tags": ["tallest", "luxury", "viewpoint"],
            },
            {
                "name": "Red Dunes Desert Safari & Bedouin BBQ Dinner",
                "description": "Dune bashing, camel riding, sandboarding, and traditional Tanoura dance show under stars.",
                "activity_type": ActivityType.ADVENTURE,
                "avg_cost": 85.0,
                "duration_minutes": 360,
                "tags": ["desert", "camel", "safari", "bbq"],
            },
            {
                "name": "Dubai Mall & Gold Souk Luxury Shopping",
                "description": "Browse world-renowned fashion boutiques, indoor waterfalls, and sparkling heritage souks.",
                "activity_type": ActivityType.SHOPPING,
                "avg_cost": 30.0,
                "duration_minutes": 180,
                "tags": ["shopping", "gold", "souk", "luxury"],
            },
        ],
    },
    {
        "name": "Barcelona",
        "country": "Spain",
        "country_code": "ES",
        "region": "Europe",
        "timezone": "Europe/Madrid",
        "cost_index": 65,
        "popularity_score": 93,
        "latitude": 41.3879,
        "longitude": 2.1699,
        "description": "Catalan jewel celebrated for Gaudí’s surreal architecture, Mediterranean beaches, and lively tapas bars.",
        "activities": [
            {
                "name": "Sagrada Família Audio Guided Discovery",
                "description": "Explore Antoni Gaudí's monumental basilica with intricate facades and stained glass halls.",
                "activity_type": ActivityType.CULTURE,
                "avg_cost": 32.0,
                "duration_minutes": 120,
                "tags": ["gaudi", "architecture", "church"],
            },
            {
                "name": "Barceloneta Beach Sunset Paddleboarding",
                "description": "Glide along the calm Mediterranean waters with sweeping views of the coastal skyline.",
                "activity_type": ActivityType.ADVENTURE,
                "avg_cost": 40.0,
                "duration_minutes": 90,
                "tags": ["beach", "sea", "paddleboard", "sunset"],
            },
            {
                "name": "Gothic Quarter Tapas & Sangria Tasting",
                "description": "Taste Jamón Ibérico, patatas bravas, and refreshing sangria across medieval alleys.",
                "activity_type": ActivityType.FOOD,
                "avg_cost": 48.0,
                "duration_minutes": 150,
                "tags": ["tapas", "wine", "sangria", "history"],
            },
        ],
    },
    {
        "name": "Sydney",
        "country": "Australia",
        "country_code": "AU",
        "region": "Oceania",
        "timezone": "Australia/Sydney",
        "cost_index": 76,
        "popularity_score": 89,
        "latitude": -33.8688,
        "longitude": 151.2093,
        "description": "Sun-drenched harbour city renowned for Bondi Beach, the Opera House, and coastal adventures.",
        "activities": [
            {
                "name": "Sydney Harbour BridgeClimb Experience",
                "description": "Climb the summits of the iconic bridge for breathtaking 360-degree harbour panoramas.",
                "activity_type": ActivityType.ADVENTURE,
                "avg_cost": 175.0,
                "duration_minutes": 210,
                "tags": ["bridge", "adrenaline", "view", "harbour"],
            },
            {
                "name": "Bondi to Coogee Scenic Coastal Walk",
                "description": "Famous 6km cliffside trail connecting golden beaches, natural rock pools, and ocean cliffs.",
                "activity_type": ActivityType.NATURE,
                "avg_cost": 0.0,
                "duration_minutes": 150,
                "tags": ["beach", "ocean", "walking", "nature"],
            },
            {
                "name": "Sydney Opera House Architectural Tour",
                "description": "Behind-the-scenes look into the history, acoustic design, and venues of the iconic sails.",
                "activity_type": ActivityType.CULTURE,
                "avg_cost": 30.0,
                "duration_minutes": 60,
                "tags": ["opera", "landmark", "architecture"],
            },
        ],
    },
    {
        "name": "Kyoto",
        "country": "Japan",
        "country_code": "JP",
        "region": "Asia",
        "timezone": "Asia/Tokyo",
        "cost_index": 62,
        "popularity_score": 92,
        "latitude": 35.0116,
        "longitude": 135.7681,
        "description": "Japan's imperial heart with thousands of classical Buddhist temples, gardens, and imperial palaces.",
        "activities": [
            {
                "name": "Fushimi Inari 10,000 Torii Gates Hike",
                "description": "Trek through mystical vermilion torii gates winding up the sacred mountain slopes.",
                "activity_type": ActivityType.CULTURE,
                "avg_cost": 0.0,
                "duration_minutes": 150,
                "tags": ["torii", "shrine", "hiking", "tradition"],
            },
            {
                "name": "Arashiyama Bamboo Forest & Monkey Park",
                "description": "Wander towering bamboo groves and encounter wild macaque monkeys with hilltop views.",
                "activity_type": ActivityType.NATURE,
                "avg_cost": 12.0,
                "duration_minutes": 180,
                "tags": ["bamboo", "nature", "animals", "scenic"],
            },
            {
                "name": "Traditional Matcha Tea Ceremony in Gion",
                "description": "Participate in an authentic Zen tea preparation ritual hosted by an expert tea master.",
                "activity_type": ActivityType.RELAXATION,
                "avg_cost": 45.0,
                "duration_minutes": 90,
                "tags": ["tea", "matcha", "zen", "relax"],
            },
        ],
    },
]


def seed_database(session: Session) -> None:
    """Seed initial cities, activity catalogs, and default demo accounts if not present."""
    # 1. Check or seed demo users
    admin_user = session.query(User).filter_by(email="admin@globetrotter.com").first()
    if not admin_user:
        admin_user = User(
            email="admin@globetrotter.com",
            password_hash=hash_password("admin123"),
            full_name="Admin Traveler",
            language_pref="en",
            role=UserRole.ADMIN,
        )
        session.add(admin_user)

    demo_user = session.query(User).filter_by(email="demo@globetrotter.com").first()
    if not demo_user:
        demo_user = User(
            email="demo@globetrotter.com",
            password_hash=hash_password("traveler123"),
            full_name="Alex Traveler",
            language_pref="en",
            role=UserRole.USER,
        )
        session.add(demo_user)

    session.flush()

    # 2. Seed cities and activities
    for city_data in SEED_CITIES_DATA:
        existing_city = session.query(City).filter_by(name=city_data["name"]).first()
        if not existing_city:
            city = City(
                name=city_data["name"],
                country=city_data["country"],
                country_code=city_data["country_code"],
                region=city_data["region"],
                timezone=city_data["timezone"],
                cost_index=city_data["cost_index"],
                popularity_score=city_data["popularity_score"],
                latitude=city_data["latitude"],
                longitude=city_data["longitude"],
                description=city_data["description"],
            )
            session.add(city)
            session.flush()

            for act in city_data.get("activities", []):
                catalog_item = ActivityCatalog(
                    city_id=city.id,
                    name=act["name"],
                    description=act["description"],
                    activity_type=act["activity_type"],
                    avg_cost=act["avg_cost"],
                    duration_minutes=act["duration_minutes"],
                    tags=act["tags"],
                    source=ActivitySource.SEED,
                )
                session.add(catalog_item)

    session.commit()
    print("Database seeding completed successfully.")


if __name__ == "__main__":
    init_db()
    with SessionLocal() as session:
        seed_database(session)
