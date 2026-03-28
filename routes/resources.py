"""
Resource Management API Routes with Aggregation Pipelines (Joins)
"""
from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timedelta
from pymongo import DESCENDING
from utils.db import mongodb
from typing import List, Optional

router = APIRouter()

# ==================== Resource Endpoints ====================

@router.get("/resources")
async def list_resources(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    resource_type: Optional[str] = None,
    department: Optional[str] = None
):
    """List all resources with optional filtering"""
    try:
        db = await mongodb
        query = {}
        
        if resource_type:
            query["resource_type"] = resource_type
        if department:
            query["department"] = department
        
        resources = list(db.resources.find(query).skip(skip).limit(limit))
        total = db.resources.count_documents(query)
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": resources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/resources/{resource_id}")
async def get_resource(resource_id: str):
    """Get a specific resource"""
    try:
        db = await mongodb
        resource = db.resources.find_one({"_id": resource_id})
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        return resource
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Project Endpoints ====================

@router.get("/projects")
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    client_name: Optional[str] = None
):
    """List all projects with optional filtering"""
    try:
        db = await mongodb
        query = {}
        
        if status:
            query["status"] = status
        if client_name:
            query["client_name"] = {"$regex": client_name, "$options": "i"}
        
        projects = list(db.projects.find(query).skip(skip).limit(limit))
        total = db.projects.count_documents(query)
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": projects
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Get a specific project"""
    try:
        db = await mongodb
        project = db.projects.find_one({"_id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== AGGREGATION PIPELINES (JOINS) ====================

@router.get("/project-details/{project_id}")
async def get_project_with_resources(project_id: str):
    """
    Get project details with assigned resources (JOIN operation)
    Aggregation: projects -> assignments -> resources
    """
    try:
        db = await mongodb
        
        pipeline = [
            # Match the specific project
            {"$match": {"_id": project_id}},
            
            # Lookup assignments for this project
            {
                "$lookup": {
                    "from": "assignments",
                    "localField": "_id",
                    "foreignField": "project_id",
                    "as": "assignments"
                }
            },
            
            # Unwind assignments to access individual resources
            {"$unwind": {"path": "$assignments", "preserveNullAndEmptyArrays": True}},
            
            # Lookup resource details for each assignment
            {
                "$lookup": {
                    "from": "resources",
                    "localField": "assignments.resource_id",
                    "foreignField": "_id",
                    "as": "resource_details"
                }
            },
            
            # Unwind resource details (should be only 1)
            {"$unwind": {"path": "$resource_details", "preserveNullAndEmptyArrays": True}},
            
            # Group back to project structure
            {
                "$group": {
                    "_id": "$_id",
                    "name": {"$first": "$name"},
                    "description": {"$first": "$description"},
                    "client_name": {"$first": "$client_name"},
                    "status": {"$first": "$status"},
                    "budget": {"$first": "$budget"},
                    "start_date": {"$first": "$start_date"},
                    "end_date": {"$first": "$end_date"},
                    "team_members": {
                        "$push": {
                            "$cond": [
                                {"$ne": ["$resource_details", {}]},
                                {
                                    "assignment_id": "$assignments._id",
                                    "resource_id": "$resource_details._id",
                                    "resource_name": "$resource_details.name",
                                    "resource_email": "$resource_details.email",
                                    "resource_type": "$resource_details.resource_type",
                                    "skill_level": "$resource_details.skill_level",
                                    "role": "$assignments.role",
                                    "allocation_percentage": "$assignments.allocation_percentage",
                                    "assignment_start": "$assignments.start_date",
                                    "assignment_end": "$assignments.end_date"
                                },
                                None
                            ]
                        }
                    }
                }
            },
            
            # Clean up null entries
            {
                "$project": {
                    "team_members": {
                        "$filter": {
                            "input": "$team_members",
                            "as": "member",
                            "cond": {"$ne": ["$$member", None]}
                        }
                    },
                    "name": 1,
                    "description": 1,
                    "client_name": 1,
                    "status": 1,
                    "budget": 1,
                    "start_date": 1,
                    "end_date": 1
                }
            }
        ]
        
        result = list(db.projects.aggregate(pipeline))
        
        if not result:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return result[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/resource-assignments/{resource_id}")
async def get_resource_assignments(resource_id: str):
    """
    Get resource details with all assigned projects (JOIN operation)
    Aggregation: resources -> assignments -> projects
    """
    try:
        db = await mongodb
        
        pipeline = [
            # Match the specific resource
            {"$match": {"_id": resource_id}},
            
            # Lookup assignments for this resource
            {
                "$lookup": {
                    "from": "assignments",
                    "localField": "_id",
                    "foreignField": "resource_id",
                    "as": "assignments"
                }
            },
            
            # Unwind assignments
            {"$unwind": {"path": "$assignments", "preserveNullAndEmptyArrays": True}},
            
            # Lookup project details
            {
                "$lookup": {
                    "from": "projects",
                    "localField": "assignments.project_id",
                    "foreignField": "_id",
                    "as": "project_details"
                }
            },
            
            # Unwind project details
            {"$unwind": {"path": "$project_details", "preserveNullAndEmptyArrays": True}},
            
            # Group back to resource structure
            {
                "$group": {
                    "_id": "$_id",
                    "name": {"$first": "$name"},
                    "email": {"$first": "$email"},
                    "resource_type": {"$first": "$resource_type"},
                    "skill_level": {"$first": "$skill_level"},
                    "skills": {"$first": "$skills"},
                    "department": {"$first": "$department"},
                    "hourly_rate": {"$first": "$hourly_rate"},
                    "is_active": {"$first": "$is_active"},
                    "projects": {
                        "$push": {
                            "$cond": [
                                {"$ne": ["$project_details", {}]},
                                {
                                    "assignment_id": "$assignments._id",
                                    "project_id": "$project_details._id",
                                    "project_name": "$project_details.name",
                                    "client_name": "$project_details.client_name",
                                    "project_status": "$project_details.status",
                                    "role": "$assignments.role",
                                    "allocation_percentage": "$assignments.allocation_percentage",
                                    "assignment_start": "$assignments.start_date",
                                    "assignment_end": "$assignments.end_date",
                                    "is_active": "$assignments.is_active"
                                },
                                None
                            ]
                        }
                    }
                }
            },
            
            # Clean up null entries
            {
                "$project": {
                    "projects": {
                        "$filter": {
                            "input": "$projects",
                            "as": "proj",
                            "cond": {"$ne": ["$$proj", None]}
                        }
                    },
                    "name": 1,
                    "email": 1,
                    "resource_type": 1,
                    "skill_level": 1,
                    "skills": 1,
                    "department": 1,
                    "hourly_rate": 1,
                    "is_active": 1
                }
            }
        ]
        
        result = list(db.resources.aggregate(pipeline))
        
        if not result:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        return result[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/project-team-summary")
async def get_project_team_summary(limit: int = Query(10, ge=1, le=100)):
    """
    Get summary of all projects with team size and allocation stats
    Complex aggregation with grouping
    """
    try:
        db = await mongodb
        
        pipeline = [
            # Lookup assignments for each project
            {
                "$lookup": {
                    "from": "assignments",
                    "localField": "_id",
                    "foreignField": "project_id",
                    "as": "assignments"
                }
            },
            
            # Unwind to process each assignment
            {"$unwind": {"path": "$assignments", "preserveNullAndEmptyArrays": True}},
            
            # Lookup resource details
            {
                "$lookup": {
                    "from": "resources",
                    "localField": "assignments.resource_id",
                    "foreignField": "_id",
                    "as": "resource_info"
                }
            },
            
            # Unwind resource info
            {"$unwind": {"path": "$resource_info", "preserveNullAndEmptyArrays": True}},
            
            # Group by project
            {
                "$group": {
                    "_id": "$_id",
                    "project_name": {"$first": "$name"},
                    "client": {"$first": "$client_name"},
                    "status": {"$first": "$status"},
                    "budget": {"$first": "$budget"},
                    "team_count": {"$sum": 1},
                    "total_allocation": {"$sum": "$assignments.allocation_percentage"},
                    "avg_hourly_rate": {"$avg": "$resource_info.hourly_rate"},
                    "resource_types": {"$push": "$resource_info.resource_type"}
                }
            },
            
            # Sort by team count
            {"$sort": {"team_count": -1}},
            
            # Limit results
            {"$limit": limit}
        ]
        
        results = list(db.projects.aggregate(pipeline))
        
        return {
            "count": len(results),
            "data": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/skills-availability")
async def get_skills_availability(
    skill: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get availability of resources by skills
    Aggregation with array operations
    """
    try:
        db = await mongodb
        
        pipeline = [
            # Unwind skills array
            {"$unwind": "$skills"},
            
            # Filter by skill if provided
            *([{"$match": {"skills": {"$regex": skill, "$options": "i"}}}] if skill else []),
            
            # Group by skill
            {
                "$group": {
                    "_id": "$skills",
                    "total_resources": {"$sum": 1},
                    "senior_count": {
                        "$sum": {"$cond": [{"$eq": ["$skill_level", "senior"]}, 1, 0]}
                    },
                    "junior_count": {
                        "$sum": {"$cond": [{"$eq": ["$skill_level", "junior"]}, 1, 0]}
                    },
                    "lead_count": {
                        "$sum": {"$cond": [{"$eq": ["$skill_level", "lead"]}, 1, 0]}
                    },
                    "expert_count": {
                        "$sum": {"$cond": [{"$eq": ["$skill_level", "expert"]}, 1, 0]}
                    },
                    "avg_rate": {"$avg": "$hourly_rate"},
                    "active_count": {
                        "$sum": {"$cond": [{"$eq": ["$is_active", True]}, 1, 0]}
                    }
                }
            },
            
            # Sort by total resources
            {"$sort": {"total_resources": -1}},
            
            # Limit
            {"$limit": limit}
        ]
        
        results = list(db.resources.aggregate(pipeline))
        
        return {
            "count": len(results),
            "data": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/overview")
async def get_statistics_overview():
    """Get overall statistics"""
    try:
        db = await mongodb
        
        resources = db.resources.count_documents({})
        projects = db.projects.count_documents({})
        assignments = db.assignments.count_documents({})
        
        active_resources = db.resources.count_documents({"is_active": True})
        in_progress_projects = db.projects.count_documents({"status": "in_progress"})
        active_assignments = db.assignments.count_documents({"is_active": True})
        
        # Average allocation per resource
        pipeline = [
            {
                "$group": {
                    "_id": "$resource_id",
                    "total_allocation": {"$sum": "$allocation_percentage"}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_allocation": {"$avg": "$total_allocation"}
                }
            }
        ]
        avg_result = list(db.assignments.aggregate(pipeline))
        avg_allocation = avg_result[0]["avg_allocation"] if avg_result else 0
        
        return {
            "resources": {
                "total": resources,
                "active": active_resources,
                "inactive": resources - active_resources
            },
            "projects": {
                "total": projects,
                "in_progress": in_progress_projects
            },
            "assignments": {
                "total": assignments,
                "active": active_assignments,
                "average_allocation_per_resource": round(avg_allocation, 2)
            },
            "total_records": resources + projects + assignments
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
