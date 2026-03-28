# MongoDB Schema for LLM Context
**Database**: genai_bot
**Collections**: resources, projects, assignments

---

## 📋 Collection Selection Guide
Use this to determine which collection to query:
- **resources**: "Find developers", "Get team members", "List senior staff", "Who has Python skills"
- **projects**: "Show all active projects", "Get project budgets", "Find completed projects", "Project timeline"
- **assignments**: "Who is assigned to project X", "Resource allocation", "Team allocation percentage"
- **Multiple collections**: "Get project details with team", "Show resources on each project", "Team and project info"

---

## 1. resources Collection
**Purpose**: Employee/resource profiles

| Column | Datatype | Required | Example | Notes |
|--------|----------|----------|---------|-------|
| _id | string | Yes | "res_000000" | Padded ID format |
| name | string | Yes | "John Doe" | Full name |
| email | string | Yes | "john@company.com" | Unique email |
| resource_type | string | Yes | "developer" \| "designer" \| "project_manager" \| "devops" \| "qa" \| "data_scientist" | Enum |
| skill_level | string | Yes | "junior" \| "senior" \| "lead" \| "expert" | Enum |
| skills | array[string] | No | ["Python", "React", "AWS"] | Skill list |
| department | string | Yes | "Engineering" \| "Design" \| "PMO" \| "Operations" \| "Data Science" | Category |
| is_active | boolean | No | true \| false | Availability status |
| hourly_rate | number (float) | No | 85.0 | Rate per hour USD |
| created_at | date | No | ISODate("2024-11-18T14:53:16Z") | Creation timestamp |

**Indexes** (from utils/db.py):
- title (text)
- category (text)
- tags (text)

## 2. project Collection
**Purpose**: Project tracking

| Column | Datatype | Required | Example | Notes |
|--------|----------|----------|---------|-------|
| _id | string | Yes | "proj_004084" | Padded ID format |
| name | string | Yes | "E-Commerce Platform - 4084" | Project title |
| description | string | Yes | "Strategic initiative..." | Details |
| client_name | string | Yes | "Innovation Labs" | Client |
| status | string | Yes | "planning" \| "in_progress" \| "on_hold" \| "completed" | Enum |
| budget | number (float) | No | 130750.96 | Total budget USD |
| start_date | date | Yes | ISODate("2025-07-25T14:53:16Z") | Start timestamp |
| end_date | date | Yes | ISODate("2025-12-26T14:53:16Z") | End timestamp |
| manager_id | string | No | "res_001069" | FK to resource._id |
| created_at | date | No | ISODate("2025-07-25T14:53:16Z") | Creation |

## 3. assignment Collection
**Purpose**: Resource-to-project allocations

| Column | Datatype | Required | Example | Notes |
|--------|----------|----------|---------|-------|
| _id | string | Yes | "assign_0000000" | Padded ID |
| resource_id | string | Yes | "res_006847" | FK → resource._id |
| project_id | string | Yes | "proj_003560" | FK → project._id |
| role | string | Yes | "DevOps" | Assignment role |
| allocation_percentage | number (int) | Yes | 25 | 0-100 % time |
| start_date | date | Yes | ISODate("2025-11-18T14:53:16Z") | Assignment start |
| end_date | date | Yes | ISODate("2026-03-08T14:53:16Z") | Assignment end |
| is_active | boolean | No | false | Current status |
| created_at | date | No | ISODate("2025-11-18T14:53:16Z") | Creation |

## 🔗 Relationships & Joins
```
resource 1 --- * assignment * --- 1 project
  (_id)          (resource_id)      (_id)
               (project_id)
```

**Key Joins** (from routes/resources.py aggregations):
1. **Project + Team**: project → $lookup assignments → $lookup resources
2. **Resource + Projects**: resource → $lookup assignments → $lookup projects
3. **Team Summary**: projects + assignments + resources (group by project)

**Example Aggregation** (project_details):
```javascript
db.projects.aggregate([
  {$match: {"_id": "proj_id"}},
  {$lookup: {from: "assignments", localField: "_id", foreignField: "project_id", as: "assignments"}},
  {$lookup: {from: "resources", localField: "assignments.resource_id", foreignField: "_id", as: "resource_details"}}
])
```

## 📊 Sample Counts (after bulk_insert)
- resource: ~25 docs
- project: ~15 docs
- assignment: ~10 docs

## 💡 Query Tips for LLM
- Filter active: `{"is_active": true}`
- Skill search: `{"skills": {"$in": ["Python"]}}`
- Date range: `{"start_date": {"$gte": ISODate("2024-01-01")}}`
- Allocation >50%: `{"allocation_percentage": {"$gt": 50}}`
- Join team: Use $lookup as above

**Send this entire file to LLM for accurate RAG responses about your resource management system!**
