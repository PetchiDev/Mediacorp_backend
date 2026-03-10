from fastapi import APIRouter, Depends
from src.core.security import RoleChecker
from typing import List

router = APIRouter()

# Group restriction definitions
allow_admin = RoleChecker(["mdm-admins"])
allow_editor_admin = RoleChecker(["mdm-admins", "mdm-editors"])
allow_all = RoleChecker(["mdm-admins", "mdm-editors", "mdm-viewers"])

@router.get("/admin-only", dependencies=[Depends(allow_admin)])
async def admin_only_endpoint():
    return {"message": "Welcome, Admin!", "status": "Success"}

@router.get("/editor-admin", dependencies=[Depends(allow_editor_admin)])
async def editor_admin_endpoint():
    return {"message": "Welcome, Editor or Admin!", "status": "Success"}

@router.get("/public-to-groups", dependencies=[Depends(allow_all)])
async def public_to_groups_endpoint():
    return {"message": "Welcome, anyone in MDM groups!", "status": "Success"}
