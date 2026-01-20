"""
Common Data Environment (CDE) - PLM Service
Business logic for Product Lifecycle Management domain
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from database.saas_models_py37 import (
    Product, ProductRevision, ProductChangeEvent, BOMCurrent, BOMChangeEvent,
    ProductStatus, RevisionStatus, ProductEventType, BOMEventType
)
from database import schemas


class PLMService:
    """Service layer for PLM operations with event sourcing"""
    
    # ========================================================================
    # Product Operations
    # ========================================================================
    
    @staticmethod
    def create_product(db: Session, product_data: schemas.ProductCreate) -> Product:
        """
        Create a new product with event tracking
        Transaction: Insert event + Insert state
        """
        try:
            # Create product state
            product = Product(
                product_code=product_data.product_code,
                name=product_data.name,
                description=product_data.description,
                status=product_data.status
            )
            db.add(product)
            db.flush()  # Get product.id
            
            # Create event
            event = ProductChangeEvent(
                product_id=product.id,
                event_type=ProductEventType.CREATED,
                event_data={
                    "product_code": product_data.product_code,
                    "name": product_data.name,
                    "description": product_data.description,
                    "status": product_data.status.value
                }
            )
            db.add(event)
            
            # Commit transaction
            db.commit()
            db.refresh(product)
            return product
            
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Product with code {product_data.product_code} already exists")
        except Exception as e:
            db.rollback()
            raise
    
    @staticmethod
    def update_product(db: Session, product_id: int, product_data: schemas.ProductUpdate) -> Product:
        """
        Update product with event tracking
        Transaction: Insert event + Update state
        """
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise ValueError(f"Product {product_id} not found")
            
            # Track changes
            changes = {}
            if product_data.name is not None:
                changes['name'] = {'old': product.name, 'new': product_data.name}
                product.name = product_data.name
            if product_data.description is not None:
                changes['description'] = {'old': product.description, 'new': product_data.description}
                product.description = product_data.description
            if product_data.status is not None:
                changes['status'] = {'old': product.status.value, 'new': product_data.status.value}
                product.status = product_data.status
            
            # Create event if there were changes
            if changes:
                event_type = ProductEventType.STATUS_CHANGED if 'status' in changes else ProductEventType.UPDATED
                event = ProductChangeEvent(
                    product_id=product.id,
                    event_type=event_type,
                    event_data={"changes": changes}
                )
                db.add(event)
            
            db.commit()
            db.refresh(product)
            return product
            
        except Exception as e:
            db.rollback()
            raise
    
    @staticmethod
    def get_product(db: Session, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        return db.query(Product).filter(Product.id == product_id).first()
    
    @staticmethod
    def get_product_by_code(db: Session, product_code: str) -> Optional[Product]:
        """Get product by code"""
        return db.query(Product).filter(Product.product_code == product_code).first()
    
    @staticmethod
    def list_products(db: Session, status: Optional[ProductStatus] = None, 
                     skip: int = 0, limit: int = 100) -> List[Product]:
        """List products with optional filtering"""
        query = db.query(Product)
        if status:
            query = query.filter(Product.status == status)
        return query.offset(skip).limit(limit).all()
    
    # ========================================================================
    # Product Revision Operations
    # ========================================================================
    
    @staticmethod
    def create_revision(db: Session, revision_data: schemas.ProductRevisionCreate) -> ProductRevision:
        """
        Create a new product revision with event tracking
        Transaction: Insert event + Insert state
        """
        try:
            # Verify product exists
            product = db.query(Product).filter(Product.id == revision_data.product_id).first()
            if not product:
                raise ValueError(f"Product {revision_data.product_id} not found")
            
            # Create revision state
            revision = ProductRevision(
                product_id=revision_data.product_id,
                revision_number=revision_data.revision_number,
                description=revision_data.description,
                status=RevisionStatus.DRAFT
            )
            db.add(revision)
            db.flush()
            
            # Create product event
            event = ProductChangeEvent(
                product_id=revision_data.product_id,
                event_type=ProductEventType.REVISION_CREATED,
                event_data={
                    "revision_id": revision.id,
                    "revision_number": revision_data.revision_number,
                    "description": revision_data.description
                }
            )
            db.add(event)
            
            db.commit()
            db.refresh(revision)
            return revision
            
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Revision {revision_data.revision_number} already exists for this product")
        except Exception as e:
            db.rollback()
            raise
    
    @staticmethod
    def release_revision(db: Session, revision_id: int) -> ProductRevision:
        """
        Release a product revision
        Transaction: Insert event + Update state + Update product
        """
        try:
            revision = db.query(ProductRevision).filter(ProductRevision.id == revision_id).first()
            if not revision:
                raise ValueError(f"Revision {revision_id} not found")
            
            if revision.status == RevisionStatus.RELEASED:
                raise ValueError("Revision already released")
            
            # Update revision state
            revision.status = RevisionStatus.RELEASED
            revision.released_at = datetime.utcnow()
            
            # Update product to point to this revision
            product = db.query(Product).filter(Product.id == revision.product_id).first()
            product.current_revision_id = revision.id
            
            # Create event
            event = ProductChangeEvent(
                product_id=revision.product_id,
                event_type=ProductEventType.REVISION_RELEASED,
                event_data={
                    "revision_id": revision.id,
                    "revision_number": revision.revision_number,
                    "released_at": revision.released_at.isoformat()
                }
            )
            db.add(event)
            
            db.commit()
            db.refresh(revision)
            return revision
            
        except Exception as e:
            db.rollback()
            raise
    
    @staticmethod
    def get_revision(db: Session, revision_id: int) -> Optional[ProductRevision]:
        """Get revision by ID"""
        return db.query(ProductRevision).filter(ProductRevision.id == revision_id).first()
    
    @staticmethod
    def list_revisions(db: Session, product_id: int) -> List[ProductRevision]:
        """List all revisions for a product"""
        return db.query(ProductRevision).filter(
            ProductRevision.product_id == product_id
        ).order_by(ProductRevision.created_at.desc()).all()
    
    # ========================================================================
    # BOM Operations
    # ========================================================================
    
    @staticmethod
    def add_bom_item(db: Session, revision_id: int, bom_data: schemas.BOMItemCreate) -> BOMCurrent:
        """
        Add item to BOM with event tracking
        Transaction: Insert event + Insert state
        """
        try:
            revision = db.query(ProductRevision).filter(ProductRevision.id == revision_id).first()
            if not revision:
                raise ValueError(f"Revision {revision_id} not found")
            
            if revision.status == RevisionStatus.RELEASED:
                raise ValueError("Cannot modify BOM of released revision")
            
            # Verify child product exists
            child = db.query(Product).filter(Product.id == bom_data.child_product_id).first()
            if not child:
                raise ValueError(f"Child product {bom_data.child_product_id} not found")
            
            # Create BOM item state
            bom_item = BOMCurrent(
                parent_product_id=revision.product_id,
                parent_revision_id=revision_id,
                child_product_id=bom_data.child_product_id,
                quantity=bom_data.quantity,
                unit=bom_data.unit,
                position_number=bom_data.position_number,
                reference_designator=bom_data.reference_designator,
                notes=bom_data.notes
            )
            db.add(bom_item)
            db.flush()
            
            # Create BOM event
            event = BOMChangeEvent(
                parent_revision_id=revision_id,
                event_type=BOMEventType.ITEM_ADDED,
                bom_item_id=bom_item.id,
                event_data={
                    "bom_item_id": bom_item.id,
                    "child_product_id": bom_data.child_product_id,
                    "child_product_code": child.product_code,
                    "quantity": str(bom_data.quantity),
                    "unit": bom_data.unit,
                    "position_number": bom_data.position_number
                }
            )
            db.add(event)
            
            db.commit()
            db.refresh(bom_item)
            return bom_item
            
        except IntegrityError:
            db.rollback()
            raise ValueError("BOM item already exists at this position")
        except Exception as e:
            db.rollback()
            raise
    
    @staticmethod
    def update_bom_item(db: Session, bom_item_id: int, bom_data: schemas.BOMItemUpdate) -> BOMCurrent:
        """
        Update BOM item with event tracking
        Transaction: Insert event + Update state
        """
        try:
            bom_item = db.query(BOMCurrent).filter(BOMCurrent.id == bom_item_id).first()
            if not bom_item:
                raise ValueError(f"BOM item {bom_item_id} not found")
            
            revision = db.query(ProductRevision).filter(
                ProductRevision.id == bom_item.parent_revision_id
            ).first()
            if revision.status == RevisionStatus.RELEASED:
                raise ValueError("Cannot modify BOM of released revision")
            
            # Track changes
            changes = {}
            if bom_data.quantity is not None:
                changes['quantity'] = {'old': str(bom_item.quantity), 'new': str(bom_data.quantity)}
                bom_item.quantity = bom_data.quantity
            if bom_data.unit is not None:
                changes['unit'] = {'old': bom_item.unit, 'new': bom_data.unit}
                bom_item.unit = bom_data.unit
            if bom_data.position_number is not None:
                changes['position_number'] = {'old': bom_item.position_number, 'new': bom_data.position_number}
                bom_item.position_number = bom_data.position_number
            if bom_data.reference_designator is not None:
                changes['reference_designator'] = {'old': bom_item.reference_designator, 'new': bom_data.reference_designator}
                bom_item.reference_designator = bom_data.reference_designator
            if bom_data.notes is not None:
                changes['notes'] = {'old': bom_item.notes, 'new': bom_data.notes}
                bom_item.notes = bom_data.notes
            
            # Create event if there were changes
            if changes:
                event = BOMChangeEvent(
                    parent_revision_id=bom_item.parent_revision_id,
                    event_type=BOMEventType.ITEM_UPDATED,
                    bom_item_id=bom_item.id,
                    event_data={"changes": changes}
                )
                db.add(event)
            
            db.commit()
            db.refresh(bom_item)
            return bom_item
            
        except Exception as e:
            db.rollback()
            raise
    
    @staticmethod
    def remove_bom_item(db: Session, bom_item_id: int) -> bool:
        """
        Remove BOM item with event tracking
        Transaction: Insert event + Delete state
        """
        try:
            bom_item = db.query(BOMCurrent).filter(BOMCurrent.id == bom_item_id).first()
            if not bom_item:
                raise ValueError(f"BOM item {bom_item_id} not found")
            
            revision = db.query(ProductRevision).filter(
                ProductRevision.id == bom_item.parent_revision_id
            ).first()
            if revision.status == RevisionStatus.RELEASED:
                raise ValueError("Cannot modify BOM of released revision")
            
            # Create event before deletion
            event = BOMChangeEvent(
                parent_revision_id=bom_item.parent_revision_id,
                event_type=BOMEventType.ITEM_REMOVED,
                bom_item_id=bom_item.id,
                event_data={
                    "bom_item_id": bom_item.id,
                    "child_product_id": bom_item.child_product_id,
                    "quantity": str(bom_item.quantity),
                    "position_number": bom_item.position_number
                }
            )
            db.add(event)
            
            # Delete state
            db.delete(bom_item)
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise
    
    @staticmethod
    def get_bom(db: Session, revision_id: int) -> List[BOMCurrent]:
        """Get complete BOM for a revision"""
        return db.query(BOMCurrent).filter(
            BOMCurrent.parent_revision_id == revision_id
        ).order_by(BOMCurrent.position_number).all()
    
    @staticmethod
    def get_product_change_events(db: Session, product_id: int, limit: int = 50) -> List[ProductChangeEvent]:
        """Get change history for a product"""
        return db.query(ProductChangeEvent).filter(
            ProductChangeEvent.product_id == product_id
        ).order_by(ProductChangeEvent.created_at.desc()).limit(limit).all()
