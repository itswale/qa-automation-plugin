"""
Reporting functionality for QA Automation Plugin.
"""

import os
import json
import logging
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseReporter:
    """Base class for test reporters."""
    
    def __init__(self, output_dir: str):
        """Initialize reporter with output directory."""
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            logger.info(f"Ensured output directory exists: {self.output_dir}")
        except Exception as e:
            logger.error(f"Error creating output directory: {e}")
            raise
    
    def save_report(self, test_result: Dict[str, Any]) -> str:
        """Save test result report. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement save_report method")

class JSONReporter(BaseReporter):
    """JSON reporter for test results."""
    
    def __init__(self, output_dir: str = "reports"):
        """Initialize JSON reporter."""
        super().__init__(output_dir)
    
    def save_report(self, test_result: Dict[str, Any]) -> str:
        """Save test result as JSON file."""
        try:
            # Add timestamp if not present
            if "timestamp" not in test_result:
                test_result["timestamp"] = datetime.now().isoformat()
            
            # Generate filename
            filename = f"{test_result['test_type']}_{test_result['test_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            # Save report
            with open(filepath, 'w') as f:
                json.dump(test_result, f, indent=2)
            
            logger.info(f"Saved JSON report: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving JSON report: {e}")
            raise

class HTMLReporter(BaseReporter):
    """HTML reporter for test results."""
    
    def __init__(self, output_dir: str = "reports"):
        """Initialize HTML reporter."""
        super().__init__(output_dir)
    
    def save_report(self, test_result: Dict[str, Any]) -> str:
        """Save test result as HTML file."""
        try:
            # Generate HTML content
            html_content = self._generate_html(test_result)
            
            # Generate filename
            filename = f"{test_result['test_type']}_{test_result['test_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            filepath = os.path.join(self.output_dir, filename)
            
            # Save report
            with open(filepath, 'w') as f:
                f.write(html_content)
            
            logger.info(f"Saved HTML report: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving HTML report: {e}")
            raise
    
    def _generate_html(self, test_result: Dict[str, Any]) -> str:
        """Generate HTML content for test result."""
        # Basic HTML template
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Result: {test_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .header {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .result {{ margin-top: 20px; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .skipped {{ color: orange; }}
                .details {{ margin-top: 20px; }}
                .error {{ background-color: #fff0f0; padding: 10px; border-radius: 5px; }}
                .attachments {{ margin-top: 20px; }}
                .attachment {{ margin-top: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Test Result: {test_name}</h1>
                    <p>Type: {test_type}</p>
                    <p>Status: <span class="{status_class}">{status}</span></p>
                    <p>Timestamp: {timestamp}</p>
                    {duration_html}
                </div>
                {error_html}
                {parameters_html}
                {attachments_html}
            </div>
        </body>
        </html>
        """
        
        # Format duration if available
        duration_html = ""
        if "duration" in test_result:
            duration_html = f"<p>Duration: {test_result['duration']:.2f} seconds</p>"
        
        # Format error message if test failed
        error_html = ""
        if test_result["status"] == "failed" and "error_message" in test_result:
            error_html = f"""
            <div class="details">
                <h2>Error Details</h2>
                <div class="error">
                    <pre>{test_result['error_message']}</pre>
                </div>
            </div>
            """
        
        # Format parameters if available
        parameters_html = ""
        if "parameters" in test_result:
            parameters_html = """
            <div class="details">
                <h2>Test Parameters</h2>
                <table>
                    <tr><th>Parameter</th><th>Value</th></tr>
            """
            for param_name, param_value in test_result["parameters"].items():
                parameters_html += f"""
                    <tr>
                        <td>{param_name}</td>
                        <td>{param_value}</td>
                    </tr>
                """
            parameters_html += """
                </table>
            </div>
            """
        
        # Format attachments if available
        attachments_html = ""
        if "attachments" in test_result:
            attachments_html = """
            <div class="attachments">
                <h2>Attachments</h2>
            """
            for name, content in test_result["attachments"].items():
                if isinstance(content, str):
                    attachments_html += f"""
                    <div class="attachment">
                        <h3>{name}</h3>
                        <pre>{content}</pre>
                    </div>
                    """
            attachments_html += "</div>"
        
        # Determine status class
        status_class = {
            "passed": "passed",
            "failed": "failed",
            "skipped": "skipped"
        }.get(test_result["status"], "")
        
        # Format timestamp
        timestamp = test_result.get("timestamp", datetime.now().isoformat())
        if isinstance(timestamp, datetime):
            timestamp = timestamp.isoformat()
        
        # Generate final HTML
        return html_template.format(
            test_name=test_result["test_name"],
            test_type=test_result["test_type"],
            status=test_result["status"],
            status_class=status_class,
            timestamp=timestamp,
            duration_html=duration_html,
            error_html=error_html,
            parameters_html=parameters_html,
            attachments_html=attachments_html
        )

class ReportManager:
    """Manager for handling multiple report types."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize report manager with configuration."""
        self.config = config
        self.reporters = self._initialize_reporters()
    
    def _initialize_reporters(self) -> Dict[str, BaseReporter]:
        """Initialize reporters based on configuration."""
        reporters = {}
        reporting_config = self.config.get("reporting", {})
        
        # Get base directory for reports
        base_dir = self.config.get("cloud", {}).get("temp_dir", ".") if self.config.get("cloud", {}).get("enabled", False) else "."
        
        # Initialize JSON reporter if enabled
        if reporting_config.get("json", True):
            reporters["json"] = JSONReporter(os.path.join(base_dir, "reports"))
        
        # Initialize HTML reporter if enabled
        if reporting_config.get("html", True):
            reporters["html"] = HTMLReporter(os.path.join(base_dir, "reports"))
        
        logger.info(f"Initialized {len(reporters)} reporters")
        return reporters
    
    def save_report(self, test_result: Dict[str, Any]) -> Dict[str, str]:
        """Save test result using all enabled reporters."""
        report_paths = {}
        for reporter_name, reporter in self.reporters.items():
            try:
                report_path = reporter.save_report(test_result)
                report_paths[reporter_name] = report_path
            except Exception as e:
                logger.error(f"Error saving {reporter_name} report: {e}")
                report_paths[reporter_name] = None
        
        return report_paths
    
    def cleanup_reports(self, days: int = 30) -> None:
        """Clean up old report files."""
        for reporter in self.reporters.values():
            try:
                if os.path.exists(reporter.output_dir):
                    cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
                    for file in os.listdir(reporter.output_dir):
                        file_path = os.path.join(reporter.output_dir, file)
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
            except Exception as e:
                logger.error(f"Error cleaning up reports in {reporter.output_dir}: {e}")
    
    def get_report_paths(self, test_type: str, test_name: str) -> Dict[str, str]:
        """Get paths for different report types."""
        paths = {}
        for reporter_name, reporter in self.reporters.items():
            if isinstance(reporter, JSONReporter):
                paths["json"] = os.path.join(reporter.output_dir, f"{test_type}_{test_name}.json")
            elif isinstance(reporter, HTMLReporter):
                paths["html"] = os.path.join(reporter.output_dir, f"{test_type}_{test_name}.html")
        return paths