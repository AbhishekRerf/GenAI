from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ==================== RESOURCE MANAGEMENT SCHEMAS ====================

class ResourceType(str, Enum):
    """Types of resources"""
    DEVELOPER = "developer"
    DESIGNER = "designer"
    PROJECT_MANAGER = "project_manager"
    DEVOPS = "devops"
    QA = "qa"
    DATA_SCIENTIST = "data_scientist"

class SkillLevel(str, Enum):
    """Skill levels for resources"""
    JUNIOR = "junior"
    SENIOR = "senior"
    LEAD = "lead"
    EXPERT = "expert"

class ProjectStatus(str, Enum):
    """Project statuses"""
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"

class Resource(BaseModel):
    """Resource Schema"""
    name: str
    email: str
    resource_type: ResourceType
    skill_level: SkillLevel
    skills: List[str] = []
    department: str
    is_active: bool = True
    hourly_rate: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "resource_type": "developer",
                "skill_level": "senior",
                "skills": ["Python", "React", "AWS"],
                "department": "Engineering",
                "hourly_rate": 75.0
            }
        }

class Project(BaseModel):
    """Project Schema"""
    name: str
    description: str
    client_name: str
    status: ProjectStatus = ProjectStatus.PLANNING
    budget: float
    start_date: datetime
    end_date: datetime
    manager_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "E-Commerce Platform",
                "description": "Build scalable e-commerce platform",
                "client_name": "TechCorp Inc",
                "status": "in_progress",
                "budget": 150000.0,
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-06-30T00:00:00"
            }
        }

class Assignment(BaseModel):
    """Resource Assignment to Project"""
    resource_id: str
    project_id: str
    role: str
    allocation_percentage: float  # 0-100
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "resource_id": "res_001",
                "project_id": "proj_001",
                "role": "Backend Developer",
                "allocation_percentage": 80.0,
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-06-30T00:00:00"
            }
        }

# ==================== LEGACY SCHEMAS ====================

class Document(BaseModel):
    """MongoDB Document Schema"""
    title: str
    content: str
    category: str
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Python Best Practices",
                "content": "Always follow PEP 8 guidelines...",
                "category": "programming",
                "tags": ["python", "best-practices"]
            }
        }

class ChatQuery(BaseModel):
    """User Chat Query"""
    message: str
    session_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "How to learn Python?",
                "session_id": "user123"
            }
        }

class StructuredResponse(BaseModel):
    """Structured LLM response for table/chart"""
    IS_TABLEVIEW: Optional[bool] = None
    IS_CHARTVIEW: Optional[bool] = None
    columns: Optional[List[str]] = None
    data: Optional[List[List[str]]] = None
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    chart_type: Optional[str] = "bar"
    summary: Optional[str] = None

class ChatResponse(BaseModel):
    """API Response - structured answer only (sources removed)"""
    answer: dict  # Structured table/chart JSON
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": {
                    "IS_TABLEVIEW": True,
                    "columns": ["Name", "Skills"],
                    "data": [["John", "Python"]]
                },
                "sources": [],
                "session_id": "user123"
            }
        }
