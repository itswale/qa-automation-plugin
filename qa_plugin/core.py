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
    def __init__(self, config_path="config.yaml"):
        self.config = self.load_config(config_path)
        self.plugins = self.load_plugins()
        self.db = QADatabase()

    def load_config(self, config_path):
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}

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
                    self.db.save_result(test_type="sample", status="pass", name=test_name or "sample_test")
                    results.append(result)
            elif test_type == "custom":
                if "custom" in self.plugins:
                    result = self.plugins["custom"].run(self.config)
                    self.db.save_result(test_type="custom", status=result.get("status", "fail"), name=test_name or "custom_test")
                    results.append(result)
                else:
                    result = {"type": "custom", "status": "fail", "name": test_name or "custom_test", 
                            "error": "No custom plugin configured"}
                    self.db.save_result(test_type="custom", status="fail", name=test_name or "custom_test")
                    results.append(result)
            return results
        except Exception as e:
            error_result = {"type": test_type, "status": "fail", "name": test_file or test_name or test_type,
                          "error": str(e)}
            self.db.save_result(test_type=test_type, status="fail", name=test_file or test_name or test_type)
            return [error_result]

    def run_pytest(self, test_file=None, is_sample=False):
        """Run pytest with proper test directory handling."""
        if is_sample:
            test_dir = os.path.join('tests', 'sample')
        else:
            test_dir = os.path.join('tests', 'unit')  # Always use tests/unit for unit tests
        
        args = ['--alluredir', 'allure-results']
        if test_file:
            test_path = os.path.join(test_dir, test_file)
            if not os.path.exists(test_path):
                error_result = {"type": "unit", "status": "fail", "name": test_file,
                              "error": f"Test file not found: {test_path}"}
                self.db.save_result(test_type="unit", status="fail", name=test_file)
                return [error_result]
            args = [test_path] + args
        else:
            args = [test_dir] + args

        try:
            exit_code = pytest.main(args)
            status = "pass" if exit_code == 0 else "fail"
            self.db.save_result(test_type="unit", status=status, name=test_file or "all_unit_tests")
            return [{"type": "unit", "status": status, "name": test_file or "all_unit_tests"}]
        except Exception as e:
            error_result = {"type": "unit", "status": "fail", "name": test_file or "all_unit_tests",
                          "error": str(e)}
            self.db.save_result(test_type="unit", status="fail", name=test_file or "all_unit_tests")
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
                        self.db.save_result(test_type="e2e", status="pass", name=test_url)
                        results.append(result)
                    except Exception as e:
                        result = {"type": "e2e", "url": test_url, "status": "fail",
                                "error": str(e)}
                        self.db.save_result(test_type="e2e", status="fail", name=test_url)
                        results.append(result)
                browser.close()
            return results
        except Exception as e:
            error_result = {"type": "e2e", "status": "fail", "url": url or "all_urls",
                          "error": f"Playwright error: {str(e)}"}
            self.db.save_result(test_type="e2e", status="fail", name=url or "all_urls")
            return [error_result]