"""
Common Data Environment (CDE) - Pydantic Schemas
Request and response models for API validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

# ============================================================================
# Enums (matching database)
# ============================================================================

class ProductStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    OBSOLETE = "OBSOLETE"
    DEVELOPMENT = "DEVELOPMENT"
    
    @classmethod
    def _missing_(cls, value):
        """Allow case-insensitive enum matching"""
        if isinstance(value, str):
            for member in cls:
                if member.value.upper() == value.upper():
                    return member
        return super()._missing_(value)

class RevisionStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    RELEASED = "RELEASED"
    OBSOLETE = "OBSOLETE"
    
    @classmethod
    def _missing_(cls, value):
        """Allow case-insensitive enum matching"""
        if isinstance(value, str):
            for member in cls:
                if member.value.upper() == value.upper():
                    return member
        return super()._missing_(value)

class TransactionTypeEnum(str, Enum):
    RECEIPT = "RECEIPT"
    ISSUE = "ISSUE"
    ADJUSTMENT = "ADJUSTMENT"
    TRANSFER_OUT = "TRANSFER_OUT"
    TRANSFER_IN = "TRANSFER_IN"
    RESERVATION = "RESERVATION"
    RELEASE_RESERVATION = "RELEASE_RESERVATION"
    
    @classmethod
    def _missing_(cls, value):
        """Allow case-insensitive enum matching"""
        if isinstance(value, str):
            for member in cls:
                if member.value.upper() == value.upper():
                    return member
        return super()._missing_(value)

class ShipmentStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    PICKED = "PICKED"
    PACKED = "PACKED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    
    @classmethod
    def _missing_(cls, value):
        """Allow case-insensitive enum matching"""
        if isinstance(value, str):
            for member in cls:
                if member.value.upper() == value.upper():
                    return member
        return super()._missing_(value)

# ============================================================================
# PLM Schemas
# ============================================================================

# Product Schemas
class ProductBase(BaseModel):
    product_code: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    status: ProductStatusEnum = ProductStatusEnum.DEVELOPMENT

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[ProductStatusEnum] = None

class ProductResponse(ProductBase):
    id: int
    current_revision_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# Product Revision Schemas
class ProductRevisionBase(BaseModel):
    revision_number: str = Field(..., max_length=50)
    description: Optional[str] = None

class ProductRevisionCreate(ProductRevisionBase):
    product_id: int

class ProductRevisionRelease(BaseModel):
    pass

class ProductRevisionResponse(ProductRevisionBase):
    id: int
    product_id: int
    status: RevisionStatusEnum
    released_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# BOM Schemas
class BOMItemBase(BaseModel):
    child_product_id: int
    quantity: Decimal = Field(..., ge=0, decimal_places=4)
    unit: str = Field(default="EA", max_length=50)
    position_number: Optional[int] = None
    reference_designator: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

class BOMItemCreate(BOMItemBase):
    pass

class BOMItemUpdate(BaseModel):
    quantity: Optional[Decimal] = Field(None, ge=0, decimal_places=4)
    unit: Optional[str] = Field(None, max_length=50)
    position_number: Optional[int] = None
    reference_designator: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

class BOMItemResponse(BOMItemBase):
    id: int
    parent_product_id: int
    parent_revision_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# ============================================================================
# Logistics Schemas
# ============================================================================

# Inventory Schemas
class InventoryBalanceResponse(BaseModel):
    id: int
    product_id: int
    location_code: str
    quantity_on_hand: Decimal
    quantity_reserved: Decimal
    quantity_available: Optional[Decimal] = None
    unit: str
    last_transaction_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class InventoryTransactionCreate(BaseModel):
    product_id: int
    location_code: str = Field(..., max_length=100)
    transaction_type: TransactionTypeEnum
    quantity: Decimal = Field(..., decimal_places=4)
    unit: str = Field(default="EA", max_length=50)
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[int] = None
    notes: Optional[str] = None

class InventoryTransactionResponse(BaseModel):
    id: int
    product_id: int
    location_code: str
    transaction_type: TransactionTypeEnum
    quantity: Decimal
    unit: str
    reference_type: Optional[str]
    reference_id: Optional[int]
    notes: Optional[str]
    balance_after: Optional[Decimal]
    created_at: datetime
    
    class Config:
        orm_mode = True

# Shipment Schemas
class ShipmentLineCreate(BaseModel):
    product_id: int
    quantity_planned: Decimal = Field(..., gt=0, decimal_places=4)
    unit: str = Field(default="EA", max_length=50)
    notes: Optional[str] = None

class ShipmentLineResponse(BaseModel):
    id: int
    shipment_id: int
    product_id: int
    quantity_planned: Decimal
    quantity_picked: Decimal
    quantity_packed: Decimal
    unit: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ShipmentCreate(BaseModel):
    shipment_number: str = Field(..., max_length=100)
    from_location: str = Field(..., max_length=100)
    to_location: str = Field(..., max_length=100)
    destination_address: Optional[str] = None
    carrier: Optional[str] = Field(None, max_length=100)
    tracking_number: Optional[str] = Field(None, max_length=100)
    planned_ship_date: Optional[date] = None
    notes: Optional[str] = None
    lines: List[ShipmentLineCreate] = []

class ShipmentUpdate(BaseModel):
    from_location: Optional[str] = Field(None, max_length=100)
    to_location: Optional[str] = Field(None, max_length=100)
    destination_address: Optional[str] = None
    carrier: Optional[str] = Field(None, max_length=100)
    tracking_number: Optional[str] = Field(None, max_length=100)
    planned_ship_date: Optional[date] = None
    notes: Optional[str] = None

class ShipmentResponse(BaseModel):
    id: int
    shipment_number: str
    status: ShipmentStatusEnum
    from_location: str
    to_location: str
    destination_address: Optional[str]
    carrier: Optional[str]
    tracking_number: Optional[str]
    planned_ship_date: Optional[date]
    actual_ship_date: Optional[date]
    estimated_delivery_date: Optional[date]
    actual_delivery_date: Optional[date]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    lines: List[ShipmentLineResponse] = []
    
    class Config:
        orm_mode = True

class ShipmentConfirm(BaseModel):
    pass

class ShipmentPick(BaseModel):
    line_quantities: Dict[int, Decimal] = Field(..., description="Map of line_id to quantity_picked")

class ShipmentPack(BaseModel):
    line_quantities: Dict[int, Decimal] = Field(..., description="Map of line_id to quantity_packed")

class ShipmentShip(BaseModel):
    actual_ship_date: date
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None

class ShipmentDeliver(BaseModel):
    actual_delivery_date: date

# ============================================================================
# Analytics Schemas
# ============================================================================

class ProductInventorySummary(BaseModel):
    product_id: int
    product_code: str
    product_name: str
    product_status: str
    total_on_hand: Decimal
    total_reserved: Decimal
    total_available: Decimal
    location_count: int

class BOMExplosion(BaseModel):
    revision_id: int
    parent_code: str
    parent_name: str
    revision_number: str
    child_code: str
    child_name: str
    quantity: Decimal
    unit: str
    position_number: Optional[int]
    reference_designator: Optional[str]

class ShipmentOverview(BaseModel):
    shipment_id: int
    shipment_number: str
    status: str
    from_location: str
    to_location: str
    carrier: Optional[str]
    tracking_number: Optional[str]
    planned_ship_date: Optional[date]
    actual_ship_date: Optional[date]
    line_count: int
    total_quantity_planned: Decimal
    total_quantity_picked: Decimal
    total_quantity_packed: Decimal
    created_at: datetime
    updated_at: datetime

class RecentInventoryActivity(BaseModel):
    id: int
    created_at: datetime
    product_code: str
    product_name: str
    location_code: str
    transaction_type: str
    quantity: Decimal
    unit: str
    balance_after: Optional[Decimal]
    reference_type: Optional[str]
    reference_id: Optional[int]
    notes: Optional[str]

class ProductChangeHistory(BaseModel):
    id: int
    created_at: datetime
    product_code: str
    product_name: str
    event_type: str
    event_data: Dict[str, Any]

# ============================================================================
# Generic Response
# ============================================================================

class MessageResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None
