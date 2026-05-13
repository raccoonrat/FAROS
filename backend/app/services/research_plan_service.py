"""
ResearchPlan Service Layer

Scientific Responsibility:
- Orchestrate ResearchPlan lifecycle
- Enforce business rules and invariants
- Coordinate between API and storage layers
- Generate unique identifiers
"""

import uuid
from typing import List, Optional

from app.modules.platform.contracts import ResearchPlan
from app.modules.platform.contracts import ResearchPlanCreate
from app.modules.platform.storage import get_plan_storage as get_storage


class ResearchPlanService:
    """
    Service for ResearchPlan operations.
    
    Enforces:
    - Unique ID generation
    - Immutability guarantees
    - Business rule validation
    """
    
    def __init__(self):
        self.storage = get_storage()
    
    def create_plan(self, plan_data: ResearchPlanCreate) -> ResearchPlan:
        """
        Create a new ResearchPlan.
        
        Args:
            plan_data: Validated plan creation data
            
        Returns:
            Created ResearchPlan
            
        Raises:
            ValueError: If plan creation violates business rules
        """
        # Generate unique ID
        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        
        # Construct domain model
        plan = ResearchPlan(
            id=plan_id,
            research_question=plan_data.research_question,
            hypothesis=plan_data.hypothesis,
            variables=plan_data.variables,
            methodology=plan_data.methodology,
            expected_outcomes=plan_data.expected_outcomes,
            tags=plan_data.tags,
            notes=plan_data.notes
        )
        
        # Persist
        return self.storage.create(plan)
    
    def get_plan(self, plan_id: str) -> Optional[ResearchPlan]:
        """
        Retrieve a ResearchPlan by ID.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            ResearchPlan if found, None otherwise
        """
        return self.storage.get(plan_id)
    
    def list_plans(self) -> List[ResearchPlan]:
        """
        List all ResearchPlans.
        
        Returns:
            List of all plans, sorted by creation time (newest first)
        """
        return self.storage.list_all()
    
    def plan_exists(self, plan_id: str) -> bool:
        """
        Check if a plan exists.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            True if plan exists, False otherwise
        """
        return self.storage.exists(plan_id)


# Global service instance
_service_instance: Optional[ResearchPlanService] = None


def get_service() -> ResearchPlanService:
    """
    Get global service instance (singleton pattern).
    
    Returns:
        ResearchPlanService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = ResearchPlanService()
    return _service_instance
