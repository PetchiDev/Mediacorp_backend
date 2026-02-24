from sqlalchemy.orm import Session
from src.models.upload_model import ContentInventory, ComponentStatus
from src.core.logging import logger
from typing import List, Optional
import uuid

class UploadRepository:
    """Rule 3.3: Pure database operations for Upload."""
    def __init__(self, db: Session):
        self.db = db

    def create_content_record(self, **kwargs) -> ContentInventory:
        """Create a new record in content_inventory."""
        try:
            db_item = ContentInventory(**kwargs)
            self.db.add(db_item)
            self.db.commit()
            self.db.refresh(db_item)
            return db_item
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create content record: {e}", exc_info=True)
            raise

    def get_content_by_id(self, content_id: uuid.UUID) -> Optional[ContentInventory]:
        """Fetch content record by ID."""
        return self.db.query(ContentInventory).filter(ContentInventory.content_id == content_id).first()

    def create_component_status(self, content_id: uuid.UUID, component: str, status: str = "pending") -> ComponentStatus:
        """Initialize status for a processing component."""
        try:
            db_item = ComponentStatus(
                content_id=content_id,
                component=component,
                status=status
            )
            self.db.add(db_item)
            self.db.commit()
            self.db.refresh(db_item)
            return db_item
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create component status for {component}: {e}", exc_info=True)
            raise

    def update_status(self, content_id: uuid.UUID, status: str):
        """Update the overall status of a content record."""
        db_item = self.get_content_by_id(content_id)
        if db_item:
            db_item.status = status
            self.db.commit()
            self.db.refresh(db_item)
        return db_item
