#!/usr/bin/env python
"""
CDE SaaS Platform - Quick Start Script
Handles database setup and server startup
"""
import subprocess
import sys
import time
import os

def run_command(cmd, description):
    """Run a command and display status"""
    print(f"\n{'='*60}")
    print(f"[*] {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout[:500])
        if result.returncode == 0:
            print(f"✓ {description} - OK")
            return True
        else:
            print(f"✗ {description} - FAILED")
            if result.stderr:
                print(f"Error: {result.stderr[:500]}")
            return False
    except Exception as e:
        print(f"✗ {description} - ERROR: {e}")
        return False

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("\n" + "="*60)
    print("CDE SaaS Platform - Startup Check")
    print("="*60)
    
    # Check Python
    print("\n[1] Checking Python...")
    try:
        import sys
        version = sys.version_info
        if version.major == 3 and version.minor >= 7:
            print(f"✓ Python {version.major}.{version.minor} OK")
        else:
            print(f"✗ Python {version.major}.{version.minor} - Need 3.7+")
            return False
    except Exception as e:
        print(f"✗ Python check failed: {e}")
        return False
    
    # Check MySQL
    print("\n[2] Checking MySQL...")
    result = subprocess.run("mysql --version", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ {result.stdout.strip()}")
    else:
        print("✗ MySQL not found - install MySQL 8.x")
        return False
    
    # Check required packages
    print("\n[3] Checking Python packages...")
    try:
        import fastapi
        import sqlalchemy
        import pydantic
        import requests
        print("✓ All required packages installed")
    except ImportError as e:
        print(f"✗ Missing package: {e}")
        print("  Run: pip install -r requirements.txt")
        return False
    
    return True

def setup_database():
    """Setup or reset database"""
    print("\n" + "="*60)
    print("Database Setup")
    print("="*60)
    
    # Check if database exists
    print("\n[1] Checking database...")
    result = subprocess.run(
        'mysql -u root -p -e "USE cde_saas; SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=\'cde_saas\';"',
        shell=True,
        capture_output=True,
        text=True,
        input="\n"  # empty password
    )
    
    if "0" not in result.stdout:
        print("✓ Database cde_saas already exists")
        response = input("\nReset database? (y/n): ").strip().lower()
        if response != 'y':
            print("Keeping existing database")
            return True
    
    # Create/reset database
    print("\n[2] Creating/resetting database...")
    commands = [
        'mysql -u root -p -e "DROP DATABASE IF EXISTS cde_saas;"',
        'mysql -u root -p -e "CREATE DATABASE cde_saas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"',
        'mysql -u root -p cde_saas < schema_saas.sql'
    ]
    
    for cmd in commands:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, input="\n")
        if result.returncode != 0:
            print(f"✗ Failed: {cmd}")
            if result.stderr:
                print(f"Error: {result.stderr[:200]}")
            return False
    
    print("✓ Database setup complete")
    return True

def start_server():
    """Start the FastAPI server"""
    print("\n" + "="*60)
    print("Starting CDE SaaS Platform")
    print("="*60)
    
    os.chdir(r"c:\Users\prajw\Desktop\CDE-MVP")
    print("\nStarting server on http://0.0.0.0:8000")
    print("Press Ctrl+C to stop\n")
    
    try:
        subprocess.run("python main_saas.py", shell=True)
    except KeyboardInterrupt:
        print("\n\nServer stopped")

def main():
    """Main startup flow"""
    try:
        # Check prerequisites
        if not check_prerequisites():
            print("\n✗ Prerequisites not met. Please install missing components.")
            sys.exit(1)
        
        # Setup database
        if not setup_database():
            print("\n✗ Database setup failed")
            sys.exit(1)
        
        # Start server
        start_server()
        
    except KeyboardInterrupt:
        print("\n\nShutdown initiated")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
