#!/usr/bin/env python3
"""
Test file to verify that direct imports work.
"""
# First import the src package to set up the path
import src

# Now try the direct import
from models.factory import create_model

print("Import successful!")
print(f"create_model function: {create_model}") 