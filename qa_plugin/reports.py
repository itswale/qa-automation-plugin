"""
Reporting logic for test results (Allure, JSON).
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import webbrowser
import time

class QAReporter:
    """Base reporter class for QA test results."""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a report from test results."""
        raise NotImplementedError

class JSONReporter(QAReporter):
    """Generate JSON reports."""
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a JSON report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"report_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
            
        return str(report_path)

class AllureReporter:
    """Generates and serves Allure reports."""
    
    def __init__(self, report_dir="allure-results", report_path="allure-report"):
        self.report_dir = report_dir
        self.report_path = report_path
        os.makedirs(report_dir, exist_ok=True)
        os.makedirs(report_path, exist_ok=True)
    
    def _clean_report_directory(self):
        """Clean the report directory."""
        for file in os.listdir(self.report_dir):
            os.remove(os.path.join(self.report_dir, file))
    
    def _sanitize_filename(self, name: str) -> str:
        """Convert a string into a valid filename.
        
        Args:
            name: The string to convert into a filename
            
        Returns:
            A string that can be used as a valid filename
        """
        # Replace invalid characters with underscores
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # Replace multiple underscores with a single one
        while '__' in name:
            name = name.replace('__', '_')
        
        # Remove leading/trailing underscores
        name = name.strip('_')
        
        # If the name is empty after sanitization, use a default
        if not name:
            name = 'unnamed_test'
            
        # Ensure the filename isn't too long
        if len(name) > 100:
            name = name[:100]
            
        return name
    
    def _convert_timestamp(self, timestamp) -> int:
        """Convert timestamp to Unix timestamp in milliseconds."""
        if isinstance(timestamp, datetime):
            return int(timestamp.timestamp() * 1000)
        return int(datetime.now().timestamp() * 1000)
    
    def generate_report(self, data):
        """Generate an Allure report from test results."""
        try:
            # Clean previous report
            self._clean_report_directory()
            
            # Convert test results to Allure format
            for test in data.get("tests", []):
                # Sanitize the test name for the filename
                safe_name = self._sanitize_filename(test.get("name", "test"))
                result_file = os.path.join(self.report_dir, f"{safe_name}-result.json")
                
                # Get and convert timestamp
                timestamp = self._convert_timestamp(test.get("timestamp", datetime.now()))
                
                with open(result_file, "w") as f:
                    json.dump({
                        "name": test.get("name", "Unnamed Test"),
                        "status": test.get("status", "unknown"),
                        "stage": "finished",
                        "start": timestamp,
                        "stop": timestamp + 1000,  # Add 1 second to end time
                        "description": test.get("description", ""),
                        "fullName": test.get("name", "Unnamed Test"),
                        "labels": [
                            {"name": "testType", "value": test.get("test_type", "unknown")},
                            {"name": "status", "value": test.get("status", "unknown")}
                        ],
                        "steps": [],
                        "attachments": []
                    }, f)
            
            # Generate Allure report
            try:
                subprocess.run(
                    ["allure", "generate", self.report_dir, "-o", self.report_path, "--clean"],
                    check=True,
                    capture_output=True,
                    text=True
                )
                return os.path.abspath(self.report_path)
            except subprocess.CalledProcessError as e:
                raise Exception(f"Failed to generate Allure report: {e.stderr}")
            except FileNotFoundError:
                raise Exception("Allure command not found. Please install Allure command-line tool.")
            
        except Exception as e:
            raise Exception(f"Error generating Allure report: {str(e)}")
    
    def open_report(self):
        """Open the generated Allure report in the default browser."""
        try:
            if not os.path.exists(self.report_path):
                raise Exception("No Allure report found. Generate a report first.")
            
            # Check if report files exist
            index_html = os.path.join(self.report_path, "index.html")
            if not os.path.exists(index_html):
                raise Exception("Report files not found. Generate a new report first.")
            
            # Open report in browser
            webbrowser.open(f"file://{os.path.abspath(index_html)}")
            return True
        except Exception as e:
            raise Exception(f"Error opening Allure report: {str(e)}")
    
    def serve_report(self):
        """Serve the Allure report on a local server."""
        try:
            if not os.path.exists(self.report_path):
                raise Exception("No Allure report found. Generate a report first.")
            
            # Check if report files exist
            index_html = os.path.join(self.report_path, "index.html")
            if not os.path.exists(index_html):
                raise Exception("Report files not found. Generate a new report first.")
            
            # Start Allure server
            try:
                process = subprocess.Popen(
                    ["allure", "serve", self.report_dir],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                # Wait a moment for the server to start
                time.sleep(2)
                if process.poll() is not None:
                    # Process ended, check for errors
                    _, stderr = process.communicate()
                    raise Exception(f"Allure server failed to start: {stderr}")
                return True
            except subprocess.CalledProcessError as e:
                raise Exception(f"Failed to start Allure server: {e.stderr}")
            except FileNotFoundError:
                raise Exception("Allure command not found. Please install Allure command-line tool.")
            
        except Exception as e:
            raise Exception(f"Error serving Allure report: {str(e)}")