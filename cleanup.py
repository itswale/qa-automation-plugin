"""
Cleanup script for QA Automation Plugin.
Removes generated reports, temporary files, and database.
"""

import os
import shutil
from pathlib import Path

def cleanup():
    """Clean up generated files and directories."""
    # Directories to clean
    dirs_to_clean = [
        "allure-results",
        "allure-report",
        "reports",
        "__pycache__",
        ".pytest_cache"
    ]
    
    # Files to clean
    files_to_clean = [
        "qa_results.db",
        ".coverage",
        "coverage.xml"
    ]
    
    # Clean directories
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Removing directory: {dir_name}")
            shutil.rmtree(dir_name)
    
    # Clean files
    for file_name in files_to_clean:
        if os.path.exists(file_name):
            print(f"Removing file: {file_name}")
            os.remove(file_name)
    
    # Clean __pycache__ directories recursively
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            cache_dir = os.path.join(root, "__pycache__")
            print(f"Removing directory: {cache_dir}")
            shutil.rmtree(cache_dir)
    
    # Clean .pytest_cache directories recursively
    for root, dirs, files in os.walk("."):
        if ".pytest_cache" in dirs:
            cache_dir = os.path.join(root, ".pytest_cache")
            print(f"Removing directory: {cache_dir}")
            shutil.rmtree(cache_dir)
    
    print("\nCleanup completed successfully!")

if __name__ == "__main__":
    cleanup() 