#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for database migration - simulates bot startup
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from models.database import init_db
    print("✅ Starting database initialization and migration...")
    init_db()
    print("✅ Database initialization completed successfully!")
    
except Exception as e:
    print(f"❌ Error during database initialization: {e}")
    import traceback
    traceback.print_exc()