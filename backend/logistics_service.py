"""
Common Data Environment (CDE) - Logistics Service
Business logic for Logistics domain (Inventory & Shipments)
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal

from database.saas_models_py37 import (
    Product, InventoryBalance, InventoryTransaction, Shipment, ShipmentLine, ShipmentEvent,
    TransactionType, ShipmentStatus, ShipmentEventType
)
from database import schemas


class LogisticsService:
    """Service layer for Logistics operations with event sourcing"""
    
    # ========================================================================
    # Inventory Operations
    # ========================================================================
    
    @staticmethod
    def get_or_create_balance(db: Session, product_id: int, location_code: str) -> InventoryBalance:
        """Get existing balance or create new one"""
        balance = db.query(InventoryBalance).filter(
            InventoryBalance.product_id == product_id,
            InventoryBalance.location_code == location_code
        ).first()
        
        if not balance:
            # Verify product exists
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise ValueError(f"Product {product_id} not found")
            
            balance = InventoryBalance(
                product_id=product_id,
                location_code=location_code,
                quantity_on_hand=Decimal('0'),
                quantity_reserved=Decimal('0')
            )
            db.add(balance)
            db.flush()
        
        return balance
    
    @staticmethod
    def create_transaction(db: Session, txn_data: schemas.InventoryTransactionCreate) -> InventoryTransaction:
        """
        Create inventory transaction with balance update
        Transaction: Insert event + Update state
        """
        try:
            # Get or create balance
            balance = LogisticsService.get_or_create_balance(
                db, txn_data.product_id, txn_data.location_code
            )
            
            # Calculate new balance based on transaction type
            old_on_hand = balance.quantity_on_hand
            old_reserved = balance.quantity_reserved
            
            if txn_data.transaction_type == TransactionType.RECEIPT:
                balance.quantity_on_hand += txn_data.quantity
            elif txn_data.transaction_type == TransactionType.ISSUE:
                if balance.quantity_on_hand < txn_data.quantity:
                    raise ValueError(f"Insufficient quantity. Available: {balance.quantity_on_hand}, Requested: {txn_data.quantity}")
                balance.quantity_on_hand -= txn_data.quantity
            elif txn_data.transaction_type == TransactionType.ADJUSTMENT:
                balance.quantity_on_hand = txn_data.quantity
            elif txn_data.transaction_type == TransactionType.TRANSFER_OUT:
                if balance.quantity_on_hand < txn_data.quantity:
                    raise ValueError(f"Insufficient quantity for transfer")
                balance.quantity_on_hand -= txn_data.quantity
            elif txn_data.transaction_type == TransactionType.TRANSFER_IN:
                balance.quantity_on_hand += txn_data.quantity
            elif txn_data.transaction_type == TransactionType.RESERVATION:
                available = balance.quantity_on_hand - balance.quantity_reserved
                if available < txn_data.quantity:
                    raise ValueError(f"Insufficient available quantity. Available: {available}, Requested: {txn_data.quantity}")
                balance.quantity_reserved += txn_data.quantity
            elif txn_data.transaction_type == TransactionType.RELEASE_RESERVATION:
                if balance.quantity_reserved < txn_data.quantity:
                    raise ValueError(f"Cannot release more than reserved")
                balance.quantity_reserved -= txn_data.quantity
            
            balance.last_transaction_at = datetime.utcnow()
            
            # Create transaction event
            transaction = InventoryTransaction(
                product_id=txn_data.product_id,
                location_code=txn_data.location_code,
                transaction_type=txn_data.transaction_type,
                quantity=txn_data.quantity,
                unit=txn_data.unit,
                reference_type=txn_data.reference_type,
                reference_id=txn_data.reference_id,
                notes=txn_data.notes,
                balance_after=balance.quantity_on_hand
            )
            db.add(transaction)
            
            db.commit()
            db.refresh(transaction)
            db.refresh(balance)
            return transaction
            
        except Exception as e:
            db.rollback()
            raise
    
    @staticmethod
    def get_balance(db: Session, product_id: int, location_code: str) -> Optional[InventoryBalance]:
        """Get inventory balance for product at location"""
        return db.query(InventoryBalance).filter(
            InventoryBalance.product_id == product_id,
            InventoryBalance.location_code == location_code
        ).first()
    
    @staticmethod
    def list_balances(db: Session, product_id: Optional[int] = None, 
                     location_code: Optional[str] = None,
                     skip: int = 0, limit: int = 100) -> List[InventoryBalance]:
        """List inventory balances with optional filtering"""
        query = db.query(InventoryBalance)
        if product_id:
            query = query.filter(InventoryBalance.product_id == product_id)
        if location_code:
            query = query.filter(InventoryBalance.location_code == location_code)
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_transactions(db: Session, product_id: Optional[int] = None,
                        location_code: Optional[str] = None,
                        skip: int = 0, limit: int = 100) -> List[InventoryTransaction]:
        """Get transaction history with optional filtering"""
        query = db.query(InventoryTransaction)
        if product_id:
            query = query.filter(InventoryTransaction.product_id == product_id)
        if location_code:
            query = query.filter(InventoryTransaction.location_code == location_code)
        return query.order_by(InventoryTransaction.created_at.desc()).offset(skip).limit(limit).all()
    
    # ========================================================================
    # Shipment Operations
    # ========================================================================
    
    @staticmethod
    def create_shipment(db: Session, shipment_data: schemas.ShipmentCreate) -> Shipment:
        """
        Create shipment with lines and event
        Transaction: Insert event + Insert state (shipment + lines)
        """
        try:
            # Create shipment state
            shipment = Shipment(
                shipment_number=shipment_data.shipment_number,
                status=ShipmentStatus.DRAFT,
                from_location=shipment_data.from_location,
                to_location=shipment_data.to_location,
                destination_address=shipment_data.destination_address,
                carrier=shipment_data.carrier,
                tracking_number=shipment_data.tracking_number,
                planned_ship_date=shipment_data.planned_ship_date,
                notes=shipment_data.notes
            )
            db.add(shipment)
            db.flush()
            
            # Create shipment lines
            for line_data in shipment_data.lines:
                # Verify product exists
                product = db.query(Product).filter(Product.id == line_data.product_id).first()
                if not product:
                    raise ValueError(f"Product {line_data.product_id} not found")
                
                line = ShipmentLine(
                    shipment_id=shipment.id,
                    product_id=line_data.product_id,
                    quantity_planned=line_data.quantity_planned,
                    unit=line_data.unit,
                    notes=line_data.notes
                )
                db.add(line)
            
            # Create shipment event
            event = ShipmentEvent(
                shipment_id=shipment.id,
                event_type=ShipmentEventType.CREATED,
                event_data={
                    "shipment_number": shipment_data.shipment_number,
                    "from_location": shipment_data.from_location,
                    "to_location": shipment_data.to_location,
                    "line_count": len(shipment_data.lines)
                }
            )
            db.add(event)
            
            db.commit()
            db.refresh(shipment)
            return shipment
            
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Shipment {shipment_data.shipment_number} already exists")
        except Exception as e:
            db.rollback()
            raise
    
    @staticmethod
    def confirm_shipment(db: Session, shipment_id: int) -> Shipment:
        """
        Confirm shipment and reserve inventory
        Transaction: Insert event + Update state + Create inventory reservations
        """
        try:
            shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
            if not shipment:
                raise ValueError(f"Shipment {shipment_id} not found")
            
            if shipment.status != ShipmentStatus.DRAFT:
                raise ValueError(f"Can only confirm draft shipments. Current status: {shipment.status}")
            
            # Reserve inventory for each line
            lines = db.query(ShipmentLine).filter(ShipmentLine.shipment_id == shipment_id).all()
            for line in lines:
                # Create reservation transaction
                reservation_txn = schemas.InventoryTransactionCreate(
                    product_id=line.product_id,
                    location_code=shipment.from_location,
                    transaction_type=TransactionType.RESERVATION,
                    quantity=line.quantity_planned,
                    unit=line.unit,
                    reference_type="shipment",
                    reference_id=shipment.id,
                    notes=f"Reserved for shipment {shipment.shipment_number}"
                )
                LogisticsService.create_transaction(db, reservation_txn)
            
            # Update shipment status
            shipment.status = ShipmentStatus.CONFIRMED
            
            # Create event
            event = ShipmentEvent(
                shipment_id=shipment.id,
                event_type=ShipmentEventType.CONFIRMED,
                event_data={
                    "confirmed_at": datetime.utcnow().isoformat(),
                    "line_count": len(lines)
                }
            )
            db.add(event)
            
            db.commit()
            db.refresh(shipment)
            return shipment
            
        except Exception as e:
            db.rollback()
            raise
    
    @staticmethod
    def pick_shipment(db: Session, shipment_id: int, pick_data: schemas.ShipmentPick) -> Shipment:
        """
        Record picking quantities for shipment
        Transaction: Insert event + Update state (shipment + lines)
        """
        try:
            shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
            if not shipment:
                raise ValueError(f"Shipment {shipment_id} not found")
            
            if shipment.status != ShipmentStatus.CONFIRMED:
                raise ValueError(f"Can only pick confirmed shipments. Current status: {shipment.status}")
            
            # Update line quantities
            for line_id, quantity in pick_data.line_quantities.items():
                line = db.query(ShipmentLine).filter(ShipmentLine.id == line_id).first()
                if not line or line.shipment_id != shipment_id:
                    raise ValueError(f"Line {line_id} not found in shipment")
                
                if quantity > line.quantity_planned:
                    raise ValueError(f"Cannot pick more than planned quantity for line {line_id}")
                
                line.quantity_picked = quantity
            
            # Update shipment status
            shipment.status = ShipmentStatus.PICKED
            
            # Create event
            event = ShipmentEvent(
                shipment_id=shipment.id,
                event_type=ShipmentEventType.PICKED,
                event_data={
                    "picked_at": datetime.utcnow().isoformat(),
                    "quantities": {str(k): str(v) for k, v in pick_data.line_quantities.items()}
                }
            )
            db.add(event)
            
            db.commit()
            db.refresh(shipment)
            return shipment
            
        except Exception as e:
            db.rollback()
            raise
    
    @staticmethod
    def pack_shipment(db: Session, shipment_id: int, pack_data: schemas.ShipmentPack) -> Shipment:
        """
        Record packing quantities for shipment
        Transaction: Insert event + Update state (shipment + lines)
        """
        try:
            shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
            if not shipment:
                raise ValueError(f"Shipment {shipment_id} not found")
            
            if shipment.status != ShipmentStatus.PICKED:
                raise ValueError(f"Can only pack picked shipments. Current status: {shipment.status}")
            
            # Update line quantities
            for line_id, quantity in pack_data.line_quantities.items():
                line = db.query(ShipmentLine).filter(ShipmentLine.id == line_id).first()
                if not line or line.shipment_id != shipment_id:
                    raise ValueError(f"Line {line_id} not found in shipment")
                
                if quantity > line.quantity_picked:
                    raise ValueError(f"Cannot pack more than picked quantity for line {line_id}")
                
                line.quantity_packed = quantity
            
            # Update shipment status
            shipment.status = ShipmentStatus.PACKED
            
            # Create event
            event = ShipmentEvent(
                shipment_id=shipment.id,
                event_type=ShipmentEventType.PACKED,
                event_data={
                    "packed_at": datetime.utcnow().isoformat(),
                    "quantities": {str(k): str(v) for k, v in pack_data.line_quantities.items()}
                }
            )
            db.add(event)
            
            db.commit()
            db.refresh(shipment)
            return shipment
            
        except Exception as e:
            db.rollback()
            raise
    
    @staticmethod
    def ship_shipment(db: Session, shipment_id: int, ship_data: schemas.ShipmentShip) -> Shipment:
        """
        Mark shipment as shipped and issue inventory
        Transaction: Insert event + Update state + Create inventory issues + Release reservations
        """
        try:
            shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
            if not shipment:
                raise ValueError(f"Shipment {shipment_id} not found")
            
            if shipment.status != ShipmentStatus.PACKED:
                raise ValueError(f"Can only ship packed shipments. Current status: {shipment.status}")
            
            # Issue inventory and release reservations for each line
            lines = db.query(ShipmentLine).filter(ShipmentLine.shipment_id == shipment_id).all()
            for line in lines:
                # Issue the packed quantity
                if line.quantity_packed > 0:
                    issue_txn = schemas.InventoryTransactionCreate(
                        product_id=line.product_id,
                        location_code=shipment.from_location,
                        transaction_type=TransactionType.ISSUE,
                        quantity=line.quantity_packed,
                        unit=line.unit,
                        reference_type="shipment",
                        reference_id=shipment.id,
                        notes=f"Issued for shipment {shipment.shipment_number}"
                    )
                    LogisticsService.create_transaction(db, issue_txn)
                
                # Release reservation
                release_txn = schemas.InventoryTransactionCreate(
                    product_id=line.product_id,
                    location_code=shipment.from_location,
                    transaction_type=TransactionType.RELEASE_RESERVATION,
                    quantity=line.quantity_planned,
                    unit=line.unit,
                    reference_type="shipment",
                    reference_id=shipment.id,
                    notes=f"Released reservation for shipment {shipment.shipment_number}"
                )
                LogisticsService.create_transaction(db, release_txn)
            
            # Update shipment
            shipment.status = ShipmentStatus.SHIPPED
            shipment.actual_ship_date = ship_data.actual_ship_date
            if ship_data.carrier:
                shipment.carrier = ship_data.carrier
            if ship_data.tracking_number:
                shipment.tracking_number = ship_data.tracking_number
            
            # Create event
            event = ShipmentEvent(
                shipment_id=shipment.id,
                event_type=ShipmentEventType.SHIPPED,
                event_data={
                    "shipped_at": datetime.utcnow().isoformat(),
                    "actual_ship_date": ship_data.actual_ship_date.isoformat(),
                    "carrier": ship_data.carrier,
                    "tracking_number": ship_data.tracking_number
                }
            )
            db.add(event)
            
            db.commit()
            db.refresh(shipment)
            return shipment
            
        except Exception as e:
            db.rollback()
            raise
    
    @staticmethod
    def get_shipment(db: Session, shipment_id: int) -> Optional[Shipment]:
        """Get shipment by ID with lines"""
        return db.query(Shipment).filter(Shipment.id == shipment_id).first()
    
    @staticmethod
    def get_shipment_by_number(db: Session, shipment_number: str) -> Optional[Shipment]:
        """Get shipment by number"""
        return db.query(Shipment).filter(Shipment.shipment_number == shipment_number).first()
    
    @staticmethod
    def list_shipments(db: Session, status: Optional[ShipmentStatus] = None,
                      from_location: Optional[str] = None,
                      skip: int = 0, limit: int = 100) -> List[Shipment]:
        """List shipments with optional filtering"""
        query = db.query(Shipment)
        if status:
            query = query.filter(Shipment.status == status)
        if from_location:
            query = query.filter(Shipment.from_location == from_location)
        return query.order_by(Shipment.created_at.desc()).offset(skip).limit(limit).all()
