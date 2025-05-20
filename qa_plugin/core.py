"""
Core QA functionality for running tests and managing plugins.
"""
import pytest
from playwright.sync_api import sync_playwright
import yaml
import os
from abc import ABC, abstractmethod
import importlib
from .database import QADatabase
import sys
import logging
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BasePlugin(ABC):
    @abstractmethod
    def run(self, config):
        pass

class CustomPlugin(BasePlugin):
    """Example custom plugin implementation."""
    def run(self, config):
        print("Running custom plugin logic!")
        return {"type": "custom", "status": "pass", "name": "custom_test"}

class QACore:
    """Core functionality for QA Automation Plugin."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize QA core with configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_environment()
        self.plugins = self.load_plugins()
        self.db = QADatabase()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config or {}
            else:
                logger.warning(f"Configuration file {self.config_path} not found, using defaults")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "test_dirs": {
                "unit": "tests/unit",
                "e2e": "tests/e2e",
                "sample": "tests/sample"
            },
            "reporting": {
                "json": True,
                "html": True
            },
            "database": {
                "path": "qa_results.db"
            },
            "cloud": {
                "enabled": os.environ.get('STREAMLIT_CLOUD', 'false').lower() == 'true',
                "temp_dir": os.environ.get('STREAMLIT_TEMP_DIR', tempfile.gettempdir())
            }
        }
    
    def _setup_environment(self) -> None:
        """Setup environment for test execution."""
        try:
            # Add test directories to Python path
            for test_dir in self.config.get("test_dirs", {}).values():
                if os.path.exists(test_dir):
                    sys.path.append(os.path.abspath(test_dir))
            
            # Create necessary directories
            self._create_directories()
            
            # Setup cloud environment if needed
            if self.is_cloud_environment():
                self._setup_cloud_environment()
            
            logger.info("Environment setup completed")
        except Exception as e:
            logger.error(f"Error setting up environment: {e}")
            raise
    
    def _create_directories(self) -> None:
        """Create necessary directories for test execution."""
        try:
            # Create test directories if they don't exist
            for test_dir in self.config.get("test_dirs", {}).values():
                os.makedirs(test_dir, exist_ok=True)
            
            # Create report directories
            if self.config.get("reporting", {}).get("json"):
                os.makedirs("reports", exist_ok=True)
            
            logger.info("Created necessary directories")
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            raise
    
    def _setup_cloud_environment(self) -> None:
        """Setup cloud-specific environment."""
        try:
            # Update paths for cloud environment
            cloud_config = self.config.get("cloud", {})
            temp_dir = cloud_config.get("temp_dir", tempfile.gettempdir())
            
            # Update database path
            if "database" in self.config:
                self.config["database"]["path"] = os.path.join(temp_dir, "qa_results.db")
            
            # Update report paths
            if "reporting" in self.config:
                reporting = self.config["reporting"]
                if reporting.get("json"):
                    reporting["json_report_dir"] = os.path.join(temp_dir, "reports")
            
            logger.info("Cloud environment setup completed")
        except Exception as e:
            logger.error(f"Error setting up cloud environment: {e}")
            raise
    
    def is_cloud_environment(self) -> bool:
        """Check if running in cloud environment."""
        return self.config.get("cloud", {}).get("enabled", False)
    
    def get_test_directories(self) -> Dict[str, str]:
        """Get test directory paths."""
        return self.config.get("test_dirs", {})
    
    def get_reporting_config(self) -> Dict[str, Any]:
        """Get reporting configuration."""
        return self.config.get("reporting", {})
    
    def get_database_path(self) -> str:
        """Get database path."""
        return self.config.get("database", {}).get("path", "qa_results.db")
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        try:
            # Deep update configuration
            def deep_update(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
                for k, v in u.items():
                    if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                        d[k] = deep_update(d[k], v)
                    else:
                        d[k] = v
                return d
            
            self.config = deep_update(self.config, updates)
            self.save_config()
            logger.info("Configuration updated successfully")
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            raise
    
    def get_test_files(self, test_type: str) -> List[str]:
        """Get list of test files for a specific test type."""
        try:
            test_dir = self.config.get("test_dirs", {}).get(test_type)
            if not test_dir or not os.path.exists(test_dir):
                logger.warning(f"Test directory not found for type: {test_type}")
                return []
            
            test_files = []
            for root, _, files in os.walk(test_dir):
                for file in files:
                    if file.endswith(("_test.py", "test_.py", "test.py")):
                        test_files.append(os.path.join(root, file))
            
            logger.info(f"Found {len(test_files)} test files for type: {test_type}")
            return test_files
        except Exception as e:
            logger.error(f"Error getting test files: {e}")
            return []
    
    def get_test_types(self) -> List[str]:
        """Get list of available test types."""
        return list(self.config.get("test_dirs", {}).keys())
    
    def validate_test_type(self, test_type: str) -> bool:
        """Validate if a test type exists."""
        return test_type in self.get_test_types()
    
    def get_report_paths(self, test_type: str, test_name: str) -> Dict[str, str]:
        """Get paths for different report types."""
        try:
            reporting = self.config.get("reporting", {})
            base_dir = self.config.get("cloud", {}).get("temp_dir", ".") if self.is_cloud_environment() else "."
            
            paths = {}
            if reporting.get("json"):
                paths["json"] = os.path.join(base_dir, "reports", f"{test_type}_{test_name}.json")
            if reporting.get("html"):
                paths["html"] = os.path.join(base_dir, "reports", f"{test_type}_{test_name}.html")
            
            return paths
        except Exception as e:
            logger.error(f"Error getting report paths: {e}")
            return {}
    
    def cleanup_reports(self, days: int = 30) -> None:
        """Clean up old report files."""
        try:
            reporting = self.config.get("reporting", {})
            base_dir = self.config.get("cloud", {}).get("temp_dir", ".") if self.is_cloud_environment() else "."
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for report_type in ["json", "html"]:
                if reporting.get(report_type):
                    report_dir = os.path.join(base_dir, "reports")
                    if os.path.exists(report_dir):
                        for file in os.listdir(report_dir):
                            file_path = os.path.join(report_dir, file)
                            if os.path.getmtime(file_path) < cutoff_date:
                                try:
                                    if os.path.isfile(file_path):
                                        os.remove(file_path)
                                    elif os.path.isdir(file_path):
                                        import shutil
                                        shutil.rmtree(file_path)
                                    logger.info(f"Deleted old report: {file_path}")
                                except Exception as e:
                                    logger.warning(f"Error deleting report {file_path}: {e}")
            
            logger.info(f"Cleaned up reports older than {days} days")
        except Exception as e:
            logger.error(f"Error cleaning up reports: {e}")
            raise

    def load_plugins(self):
        plugins = {}
        for plugin_name, plugin_path in self.config.get('plugins', {}).items():
            try:
                module_name, class_name = plugin_path.rsplit('.', 1)
                module = importlib.import_module(module_name)
                plugin_class = getattr(module, class_name)
                plugins[plugin_name] = plugin_class()
            except (ImportError, AttributeError) as e:
                print(f"Warning: Could not load plugin {plugin_name}: {str(e)}")
        return plugins

    def run_tests(self, test_type="all", test_file=None, test_name=None, url=None):
        results = []
        try:
            if test_type == "unit":
                results.extend(self.run_pytest(test_file))
            elif test_type == "e2e":
                results.extend(self.run_playwright(url))
            elif test_type == "sample":
                if test_file:
                    results.extend(self.run_pytest(test_file, is_sample=True))
                else:
                    result = {"type": "sample", "status": "pass", "name": test_name or "sample_test"}
                    self.db.add_result(test_type="sample", status="pass", test_name=test_name or "sample_test", duration=0.0)
                    results.append(result)
            elif test_type == "custom":
                if "custom" in self.plugins:
                    result = self.plugins["custom"].run(self.config)
                    self.db.add_result(test_type="custom", status=result.get("status", "fail"), test_name=test_name or "custom_test", duration=0.0)
                    results.append(result)
                else:
                    result = {"type": "custom", "status": "fail", "name": test_name or "custom_test", 
                            "error": "No custom plugin configured"}
                    self.db.add_result(test_type="custom", status="fail", test_name=test_name or "custom_test", duration=0.0)
                    results.append(result)
            return results
        except Exception as e:
            error_result = {"type": test_type, "status": "fail", "name": test_file or test_name or test_type,
                          "error": str(e)}
            self.db.add_result(test_type=test_type, status="fail", test_name=test_file or test_name or test_type, duration=0.0)
            return [error_result]

    def run_pytest(self, test_file=None, is_sample=False):
        """Run pytest with proper test directory handling."""
        if is_sample:
            test_dir = os.path.join('tests', 'sample')
        else:
            test_dir = os.path.join('tests', 'unit')  # Always use tests/unit for unit tests
        
        args = ['-v', '--tb=short']  # Use verbose output and short traceback
        if test_file:
            test_path = os.path.join(test_dir, test_file)
            if not os.path.exists(test_path):
                error_result = {"type": "unit", "status": "fail", "name": test_file,
                              "error": f"Test file not found: {test_path}"}
                self.db.add_result(test_type="unit", status="fail", test_name=test_file, duration=0.0)
                return [error_result]
            args = [test_path] + args
        else:
            args = [test_dir] + args

        try:
            # Capture test output
            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                exit_code = pytest.main(args)
            test_output = f.getvalue()
            
            status = "pass" if exit_code == 0 else "fail"
            result = {
                "type": "unit",
                "status": status,
                "name": test_file or "all_unit_tests",
                "output": test_output
            }
            
            # Save test output to database
            self.db.add_result(
                test_type="unit",
                status=status,
                test_name=test_file or "all_unit_tests",
                duration=0.0,
                error_message=None if status == "pass" else test_output
            )
            return [result]
        except Exception as e:
            error_result = {
                "type": "unit",
                "status": "fail",
                "name": test_file or "all_unit_tests",
                "error": str(e)
            }
            self.db.add_result(
                test_type="unit",
                status="fail",
                test_name=test_file or "all_unit_tests",
                duration=0.0,
                error_message=str(e)
            )
            return [error_result]

    def run_playwright(self, url=None):
        results = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                urls_to_test = [url] if url else self.config.get('e2e_tests', [])
                
                for test_url in urls_to_test:
                    try:
                        page.goto(test_url)
                        result = {"type": "e2e", "url": test_url, "status": "pass"}
                        self.db.add_result(test_type="e2e", status="pass", test_name=test_url, duration=0.0)
                        results.append(result)
                    except Exception as e:
                        result = {"type": "e2e", "url": test_url, "status": "fail",
                                "error": str(e)}
                        self.db.add_result(test_type="e2e", status="fail", test_name=test_url, duration=0.0)
                        results.append(result)
                browser.close()
            return results
        except Exception as e:
            error_result = {"type": "e2e", "status": "fail", "url": url or "all_urls",
                          "error": f"Playwright error: {str(e)}"}
            self.db.add_result(test_type="e2e", status="fail", test_name=url or "all_urls", duration=0.0)
            return [error_result]