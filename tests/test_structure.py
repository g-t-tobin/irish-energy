"""Basic structure tests for Irish Energy Analytics Platform"""

import os
import sys
from pathlib import Path

def test_repository_structure():
    """Test that the repository structure is correctly set up"""
    
    # Test that main directories exist
    expected_dirs = [
        'infrastructure',
        'src',
        'sql',
        'dashboard',
        'tests',
        'scripts',
        '.github/workflows',
        'docs'
    ]
    
    base_path = Path('.')
    
    for directory in expected_dirs:
        assert (base_path / directory).exists(), f"Directory {directory} does not exist"
    
    # Test that source subdirectories exist
    expected_src_dirs = [
        'src/ingestion',
        'src/transformation', 
        'src/quality',
        'src/common'
    ]
    
    for directory in expected_src_dirs:
        assert (base_path / directory).exists(), f"Source directory {directory} does not exist"
    
    # Test that SQL subdirectories exist
    expected_sql_dirs = [
        'sql/schema',
        'sql/analytics',
        'sql/quality'
    ]
    
    for directory in expected_sql_dirs:
        assert (base_path / directory).exists(), f"SQL directory {directory} does not exist"
    
    # Test that requirements file exists
    assert (base_path / 'requirements.txt').exists(), "requirements.txt does not exist"
    
    # Test that README exists
    assert (base_path / 'README.md').exists(), "README.md does not exist"
    
    print("✓ All repository structure tests passed")

if __name__ == "__main__":
    test_repository_structure()
    print("All tests passed!")