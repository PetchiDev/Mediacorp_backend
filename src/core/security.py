from fastapi import Header, HTTPException, status, Depends
from typing import List, Optional
from src.core.config import settings

class RoleChecker:
    def __init__(self, allowed_groups: List[str]):
        self.allowed_groups = allowed_groups

    def __call__(self, x_user_groups: Optional[str] = Header(None, alias=settings.COGNITO_GROUPS_HEADER)):
        if not x_user_groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User groups not found in request headers"
            )
        
        # API Gateway extracts groups from Cognito token and sends them as a comma-separated string or list
        # Examples: "mdm-admins,mdm-editors" or "mdm-admins"
        user_groups = [g.strip() for g in x_user_groups.split(",")]
        
        # Check if user has at least one of the allowed groups
        has_permission = any(group in self.allowed_groups for group in user_groups)
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required permissions. Allowed groups: {self.allowed_groups}"
            )
        
        return user_groups

def get_user_groups(x_user_groups: Optional[str] = Header(None, alias=settings.COGNITO_GROUPS_HEADER)) -> List[str]:
    """
    Simple dependency to just extract and return the user's groups.
    """
    if not x_user_groups:
        return []
    return [g.strip() for g in x_user_groups.split(",")]
