import os
import asyncio
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "genai_bot")


async def main():
    print("🚀 Bulk inserting sample data...")

    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]

    # Clear existing data
    await db.resources.delete_many({})
    await db.projects.delete_many({})
    await db.assignments.delete_many({})
    print("🗑️ Cleared existing data")

    # ------------------ RESOURCES ------------------
    resource_types = ["developer", "designer", "project_manager", "devops", "qa", "data_scientist"]
    skill_levels = ["junior", "senior", "lead", "expert"]
    departments = ["Engineering", "Design", "PMO", "Operations", "Data Science"]

    resources_data = []
    resource_id_map = {}

    for i in range(2000):  # adjust as needed
        res_type = random.choice(resource_types)
        skill = random.choice(skill_levels)

        name = f"Resource_{i+1:04d}_{res_type.title()}"
        res_id = f"res_{i:06d}"

        resource_id_map[name] = res_id

        resources_data.append({
            "_id": res_id,
            "name": name,
            "email": f"{name.lower().replace(' ', '.')}@company.com",
            "resource_type": res_type,
            "skill_level": skill,
            "skills": random.sample(
                ["Python", "React", "Node.js", "Java", "AWS", "Docker", "Kubernetes", "Figma", "SQL", "Agile"],
                k=random.randint(3, 5)
            ),
            "department": random.choice(departments),
            "is_active": random.choice([True, False]),
            "hourly_rate": round(random.uniform(50, 150), 1),
            "created_at": datetime.utcnow()
        })

    await db.resources.insert_many(resources_data)
    print(f"✅ Inserted {len(resources_data)} resources")

    # ------------------ PROJECTS ------------------
    project_statuses = ["planning", "in_progress", "on_hold", "completed"]
    clients = ["TechCorp", "DataCorp", "FitLife", "FinTech Inc", "HealthAI", "ShopNow"]

    projects_data = []

    for i in range(1500):
        proj_id = f"proj_{i:06d}"

        projects_data.append({
            "_id": proj_id,
            "name": f"Project_{random.randint(1000,9999)}",
            "created_at": datetime.utcnow(),
            "description": f"Sample project {i+1}",
            "client_name": random.choice(clients),
            "status": random.choice(project_statuses),
            "budget": random.randint(50000, 500000),
            "start_date": datetime.now() - timedelta(days=random.randint(0, 180)),
            "end_date": datetime.now() + timedelta(days=random.randint(30, 365)),
            "manager_id": f"mgr_{i+1}"
        })

    await db.projects.insert_many(projects_data)
    print(f"✅ Inserted {len(projects_data)} projects")

    # ------------------ ASSIGNMENTS ------------------
    assignments_data = []

    for i in range(1500):
        assignments_data.append({
            "resource_id": random.choice(list(resource_id_map.values())),
            "project_id": random.choice([p["_id"] for p in projects_data]),
            "role": random.choice(["Developer", "Designer", "PM", "DevOps"]),
            "allocation_percentage": random.randint(50, 100),
            "start_date": datetime.now() - timedelta(days=random.randint(0, 60)),
            "end_date": datetime.now() + timedelta(days=random.randint(30, 120)),
            "is_active": True
        })

    await db.assignments.insert_many(assignments_data)
    print(f"✅ Inserted {len(assignments_data)} assignments")

    total = len(resources_data) + len(projects_data) + len(assignments_data)
    print(f"\n🎉 Total inserted: {total} documents")

    print("📋 Next: python data/create_vector_embeddings.py")


if __name__ == "__main__":
    asyncio.run(main())