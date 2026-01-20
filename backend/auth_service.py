"""
CDE SaaS - Authentication & Authorization Service
Python 3.7 Compatible Version
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import jwt
import secrets
import hashlib
from fastapi import HTTPException, status

# Python 3.7 compatible imports
try:
    from passlib.hash import bcrypt
except ImportError:
    import bcrypt as bcrypt_lib
    
    class bcrypt:
        @staticmethod
        def hash(password):
            return bcrypt_lib.hashpw(password.encode(), bcrypt_lib.gensalt()).decode()
        
        @staticmethod
        def verify(password, hashed):
            return bcrypt_lib.checkpw(password.encode(), hashed.encode())

from database.saas_models_py37 import (
    User, Organization, UserSession, ApiKey, AuditLog,
    UserRole, AuditAction, SubscriptionStatus, SubscriptionTier
)

# Configuration
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30


class AuthService:
    """Authentication and authorization service"""
    
    @staticmethod
    def create_user(
        db,
        organization_id,
        email,
        password,
        first_name,
        last_name,
        role=UserRole.USER
    ):
        """Create new user"""
        
        # Check if email already exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise ValueError("Email already registered")
        
        # Check organization exists and is active
        org = db.query(Organization).filter(
            Organization.id == organization_id,
            Organization.is_active == True
        ).first()
        if not org:
            raise ValueError("Organization not found or inactive")
        
        # Check user limit
        user_count = db.query(User).filter(
            User.organization_id == organization_id,
            User.is_active == True
        ).count()
        if user_count >= org.max_users:
            raise ValueError("User limit reached ({})".format(org.max_users))
        
        # Create user
        user = User(
            organization_id=organization_id,
            email=email.lower(),
            first_name=first_name,
            last_name=last_name,
            role=role
        )
        user.set_password(password)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def authenticate(db, email, password, ip_address=None, user_agent=None):
        """Authenticate user and create session"""
        
        # Find user
        user = db.query(User).filter(
            User.email == email.lower(),
            User.is_active == True
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account temporarily locked. Try again later."
            )
        
        # Verify password
        if not user.verify_password(password):
            # Increment failed attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check organization status
        org = db.query(Organization).filter(
            Organization.id == user.organization_id
        ).first()
        
        if not org.is_active or org.subscription_status == SubscriptionStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization account suspended"
            )
        
        # Reset failed attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        
        # Create tokens
        access_token = AuthService._create_access_token(user)
        refresh_token = AuthService._create_refresh_token(user)
        
        # Create session
        session = UserSession(
            user_id=user.id,
            token=access_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            refresh_expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(session)
        
        # Audit log
        audit = AuditLog(
            organization_id=user.organization_id,
            user_id=user.id,
            action=AuditAction.LOGIN,
            resource_type="user",
            resource_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(audit)
        
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "organization_id": user.organization_id
            }
        }
    
    @staticmethod
    def _create_access_token(user):
        """Create JWT access token"""
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "org_id": user.organization_id,
            "role": user.role.value,
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def _create_refresh_token(user):
        """Create JWT refresh token"""
        payload = {
            "sub": str(user.id),
            "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token):
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    @staticmethod
    def get_current_user(db, token):
        """Get current user from token"""
        payload = AuthService.verify_token(token)
        
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(
            User.id == user_id,
            User.is_active == True
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    
    @staticmethod
    def logout(db, token):
        """Logout user and revoke session"""
        session = db.query(UserSession).filter(
            UserSession.token == token,
            UserSession.revoked_at.is_(None)
        ).first()
        
        if session:
            session.revoked_at = datetime.utcnow()
            
            # Audit log
            audit = AuditLog(
                organization_id=session.user.organization_id,
                user_id=session.user_id,
                action=AuditAction.LOGOUT,
                resource_type="user",
                resource_id=session.user_id
            )
            db.add(audit)
            
            db.commit()
    
    @staticmethod
    def check_permission(user, resource, action):
        """Check if user has permission for action on resource"""
        
        # Super admin has all permissions
        if user.role == UserRole.SUPER_ADMIN or user.role == "super_admin":
            return True
        
        # Define role-based permissions
        permissions = {
            "org_admin": {
                "product": ["create", "read", "update", "delete"],
                "revision": ["create", "read", "update", "delete", "release"],
                "bom": ["create", "read", "update", "delete"],
                "inventory": ["create", "read", "update", "delete"],
                "shipment": ["create", "read", "update", "delete"],
                "user": ["create", "read", "update", "delete"],
                "organization": ["read", "update"],
                "analytics": ["read"]
            },
            "manager": {
                "product": ["create", "read", "update"],
                "revision": ["create", "read", "update"],
                "bom": ["create", "read", "update"],
                "inventory": ["create", "read", "update"],
                "shipment": ["create", "read", "update"],
                "analytics": ["read"]
            },
            "user": {
                "product": ["read"],
                "revision": ["read"],
                "bom": ["read"],
                "inventory": ["read", "update"],
                "shipment": ["create", "read", "update"],
                "analytics": ["read"]
            },
            "viewer": {
                "product": ["read"],
                "revision": ["read"],
                "bom": ["read"],
                "inventory": ["read"],
                "shipment": ["read"],
                "analytics": ["read"]
            }
        }
        
        # Normalize role to string for comparison
        role_str = str(user.role).lower() if user.role else "viewer"
        if hasattr(user.role, 'value'):
            role_str = user.role.value
        
        # Check custom permissions
        if user.permissions and resource in user.permissions:
            if action in user.permissions[resource]:
                return True
        
        # Check role-based permissions
        role_perms = permissions.get(role_str, {})
        resource_perms = role_perms.get(resource, [])
        
        return action in resource_perms
    
    @staticmethod
    def require_permission(user, resource, action):
        """Raise exception if user doesn't have permission"""
        if not AuthService.check_permission(user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: {} on {}".format(action, resource)
            )
    
    @staticmethod
    def create_api_key(db, user, name, scopes=None, expires_in_days=None):
        """Create API key"""
        
        # Generate key
        tier = user.organization.subscription_tier.value if hasattr(user, 'organization') else 'test'
        raw_key = "sk_{}_{}" .format('live' if tier != 'free' else 'test', secrets.token_urlsafe(32))
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        prefix = raw_key[:15]
        
        # Create API key record
        api_key = ApiKey(
            user_id=user.id,
            organization_id=user.organization_id,
            name=name,
            key_hash=key_hash,
            prefix=prefix,
            scopes=scopes or [],
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days) if expires_in_days else None
        )
        
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        return api_key, raw_key
    
    @staticmethod
    def verify_api_key(db, raw_key):
        """Verify API key and return user"""
        
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        api_key = db.query(ApiKey).filter(
            ApiKey.key_hash == key_hash,
            ApiKey.revoked_at.is_(None)
        ).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key expired"
            )
        
        # Update last used
        api_key.last_used_at = datetime.utcnow()
        db.commit()
        
        # Get user
        user = db.query(User).filter(User.id == api_key.user_id).first()
        
        return user, api_key


class OrganizationService:
    """Organization management service"""
    
    @staticmethod
    def create_organization(
        db,
        slug,
        name,
        admin_email,
        admin_password,
        admin_first_name,
        admin_last_name
    ):
        """Create new organization with admin user"""
        
        # Check slug availability
        existing = db.query(Organization).filter(Organization.slug == slug).first()
        if existing:
            raise ValueError("Organization slug already taken")
        
        # Create organization
        org = Organization(
            slug=slug,
            name=name,
            subscription_tier=SubscriptionTier.FREE,
            subscription_status=SubscriptionStatus.TRIAL,
            trial_ends_at=datetime.utcnow() + timedelta(days=14)
        )
        db.add(org)
        db.flush()
        
        # Create admin user
        admin = User(
            organization_id=org.id,
            email=admin_email.lower(),
            first_name=admin_first_name,
            last_name=admin_last_name,
            role=UserRole.ORG_ADMIN,
            is_verified=True
        )
        admin.set_password(admin_password)
        db.add(admin)
        
        db.commit()
        db.refresh(org)
        db.refresh(admin)
        
        return org, admin
    
    @staticmethod
    def check_resource_limit(db, organization_id, resource_type, count=1):
        """Check if organization can create more resources"""
        
        org = db.query(Organization).filter(Organization.id == organization_id).first()
        if not org:
            return False
        
        if resource_type == "product":
            from models import Product
            current = db.query(Product).filter(Product.organization_id == organization_id).count()
            return (current + count) <= org.max_products
        
        elif resource_type == "user":
            current = db.query(User).filter(
                User.organization_id == organization_id,
                User.is_active == True
            ).count()
            return (current + count) <= org.max_users
        
        return True