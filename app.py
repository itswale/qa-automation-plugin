"""
Streamlit UI for QA Automation Plugin.
"""

import streamlit as st
import yaml
from pathlib import Path
from qa_plugin.core import QACore
from qa_plugin.database import QADatabase, TestResult
from qa_plugin.reports import JSONReporter
from sqlalchemy import inspect
import os
import webbrowser
from urllib.parse import urljoin
import subprocess
from datetime import datetime
import logging
import sys
import tempfile
import traceback

# Configure logging first, before any other operations
def setup_logging():
    """Configure logging with proper error handling."""
    try:
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure logging with more detailed format
        log_file = os.path.join(log_dir, 'app.log')
        logging.basicConfig(
            level=logging.DEBUG,  # Set to DEBUG for more detailed logging
            format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logger = logging.getLogger(__name__)
        logger.info("Logging initialized successfully")
        return logger
    except Exception as e:
        # Fallback to basic logging if setup fails
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        logging.error(f"Failed to setup file logging: {str(e)}\n{traceback.format_exc()}")
        return logging.getLogger(__name__)

# Initialize logger
logger = setup_logging()

# --- Cloud Detection and Environment Functions ---
def is_cloud():
    """Check if running in Streamlit Cloud environment."""
    try:
        # Log all environment variables for debugging
        logger.debug("Environment variables:")
        for var in ['STREAMLIT_SERVER_PORT', 'STREAMLIT_SERVER_HEADLESS', 
                   'STREAMLIT_SERVER_ENABLE_STATIC_SERVING', 'HOME', 
                   'STREAMLIT_CLOUD']:
            logger.debug(f"{var}: {os.getenv(var)}")
        
        # Check for Streamlit Cloud specific environment variables
        cloud_env_vars = ['STREAMLIT_SERVER_PORT', 'STREAMLIT_SERVER_HEADLESS', 
                         'STREAMLIT_SERVER_ENABLE_STATIC_SERVING']
        is_cloud_env = any(os.getenv(var) for var in cloud_env_vars)
        logger.info(f"Cloud environment detected: {is_cloud_env}")
        return is_cloud_env
    except Exception as e:
        logger.error(f"Error checking cloud environment: {str(e)}\n{traceback.format_exc()}")
        return False

def get_database_path():
    """Get appropriate database path based on environment."""
    try:
        if is_cloud():
            # In cloud environment, use a path in the temporary directory
            temp_dir = tempfile.gettempdir()
            logger.debug(f"Using temp directory: {temp_dir}")
            db_path = os.path.join(temp_dir, 'qa_results.db')
            logger.info(f"Using cloud database path: {db_path}")
            
            # Verify directory permissions
            if not os.access(temp_dir, os.W_OK):
                logger.error(f"Temp directory is not writable: {temp_dir}")
                raise PermissionError(f"Temp directory is not writable: {temp_dir}")
        else:
            # In local environment, use a path in the project directory
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qa_results.db')
            logger.info(f"Using local database path: {db_path}")
            
            # Ensure directory exists and is writable
            db_dir = os.path.dirname(db_path)
            os.makedirs(db_dir, exist_ok=True)
            if not os.access(db_dir, os.W_OK):
                logger.error(f"Database directory is not writable: {db_dir}")
                raise PermissionError(f"Database directory is not writable: {db_dir}")
        
        return db_path
    except Exception as e:
        logger.error(f"Error getting database path: {str(e)}\n{traceback.format_exc()}")
        # Fallback to a default path
        return 'qa_results.db'

# Initialize components with proper error handling
try:
    logger.info("Starting application initialization...")
    
    # Log environment information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Environment: {'Cloud' if is_cloud() else 'Local'}")
    
    # Initialize database
    logger.info("Initializing database...")
    db_path = get_database_path()
    logger.debug(f"Database path: {db_path}")
    db = QADatabase(db_path=db_path)
    logger.info("Database initialized successfully")
    
    # Initialize core
    logger.info("Initializing QA core...")
    core = QACore(db=db)
    logger.info("QA core initialized successfully")
    
    # Initialize reporter
    logger.info("Initializing reporter...")
    reporter = JSONReporter()
    logger.info("Reporter initialized successfully")
    
    logger.info("All application components initialized successfully")
except Exception as e:
    error_msg = f"Error during initialization: {str(e)}\n{traceback.format_exc()}"
    logger.error(error_msg)
    st.error("Failed to initialize application. Please check the logs for details.")
    if not is_cloud():  # Only show detailed error in local environment
        st.error(f"Detailed error: {str(e)}")
    st.stop()

# --- Cloud Detection and Playwright Install ---
def install_playwright_browsers_if_cloud():
    if is_cloud():
        try:
            logger.info("Installing Playwright browsers for cloud environment")
            subprocess.run(["playwright", "install", "chromium"], check=True)
            logger.info("Successfully installed Playwright browsers")
        except Exception as e:
            logger.error(f"Playwright browser install failed: {str(e)}")
            st.error("Failed to install required browsers. Some features may not work.")

install_playwright_browsers_if_cloud()

# --- Environment Configuration ---
def is_cloud_environment():
    """Check if running in Streamlit Cloud."""
    return os.environ.get('STREAMLIT_CLOUD', 'false').lower() == 'true'

def get_base_url():
    """Get the base URL for the Streamlit app."""
    if is_cloud_environment():
        return None
    return f"http://localhost:{st.get_option('server.port')}"

def navigate_to(page, params=None):
    """Navigate to a specific page with optional parameters."""
    if is_cloud_environment():
        # In cloud, just update the query parameters
        st.query_params["page"] = page
        if params:
            for key, value in params.items():
                st.query_params[key] = value
        st.rerun()
        return
    
    # Local environment navigation
    base_url = get_base_url()
    if base_url:
        url = urljoin(base_url, page)
        if params:
            query_string = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query_string}"
        webbrowser.open(url)

# --- Config Helpers ---
def load_config():
    """Load configuration with cloud environment awareness."""
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
    else:
        config = {}
    
    # Add cloud-specific configuration
    if is_cloud_environment():
        config['cloud'] = True
        config['database_path'] = get_database_path()
        config['reports_dir'] = os.path.join(os.environ.get('STREAMLIT_TEMP_DIR', '/tmp'), 'reports')
    else:
        config['cloud'] = False
        config['database_path'] = 'qa_results.db'
        config['reports_dir'] = 'reports'
    
    return config

def save_config(config):
    with open("config.yaml", "w") as f:
        yaml.dump(config, f)

# --- Main UI ---
def main():
    try:
        # Set page config for consistent layout
        st.set_page_config(
            page_title="QA Automation Dashboard",
            page_icon="🧪",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Add cloud environment indicator
        if is_cloud_environment():
            st.sidebar.info("🌐 Running in Streamlit Cloud")
            logger.info("Running in Streamlit Cloud environment")
        
        st.title("QA Automation Dashboard")
        
        # Initialize session state
        if "results" not in st.session_state:
            update_results_state()
        if "test_running" not in st.session_state:
            st.session_state["test_running"] = False
        if "last_test_status" not in st.session_state:
            st.session_state["last_test_status"] = None
        if "serve_report" not in st.session_state:
            st.session_state["serve_report"] = False
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "run"
        if "cloud_environment" not in st.session_state:
            st.session_state["cloud_environment"] = is_cloud_environment()

        # Sidebar - Always show this
        with st.sidebar:
            st.title("Navigation")
            page = st.radio(
                "Go to",
                ["Run Tests", "Reports", "Test History", "Configuration"],
                key="nav_radio"
            )
            
            # Update current page in session state
            page_map = {
                "Run Tests": "run",
                "Reports": "reports",
                "Test History": "history",
                "Configuration": "config"
            }
            st.session_state["current_page"] = page_map[page]
            
            # Add some spacing and a divider
            st.markdown("---")
            st.markdown("### Quick Actions")
            if st.button("🔄 Refresh Results", key="refresh_sidebar"):
                update_results_state()
                st.rerun()
        
        # Handle page routing
        current_page = st.session_state["current_page"]
        
        # Update query params to match current page
        st.query_params["page"] = current_page
        
        # Show appropriate page content
        if current_page == "reports":
            show_reports_page()
        elif current_page == "history":
            show_history_page()
        elif current_page == "run":
            show_run_tests()
        else:
            show_configuration()
    except Exception as e:
        logger.error(f"Error in main(): {str(e)}")
        st.error(f"Application encountered an error: {str(e)}")
        st.stop()

# --- Dashboard ---
def show_dashboard():
    st.header("Test Results Overview (Dashboard)")
    if st.button("Refresh Results"):
        update_results_state()
    results = st.session_state.get("results", [])
    if results:
        st.table([{k: v for k, v in r.__dict__.items() if not k.startswith('_sa_instance_state')} for r in results])
    else:
        st.info("No test results available yet.")
    if st.session_state.get("test_running"):
        st.warning("A test is currently running...")
    if st.session_state.get("last_test_status"):
        st.success(f"Last test status: {st.session_state['last_test_status']}")

# --- Run Tests ---
def discover_tests(test_type):
    """Discover available tests based on test type."""
    if test_type == "unit":
        test_dir = "tests/unit"
        if not os.path.exists(test_dir):
            return [], {
                "error": f"❌ Unit test directory '{test_dir}' not found.",
                "next_steps": [
                    "Create a 'unit' directory inside your 'tests' directory",
                    "Add your unit test files (e.g., test_basic.py)",
                    "Make sure test files start with 'test_' and end with '.py'",
                    "Example test file structure:",
                    "```python",
                    "def test_example():",
                    "    assert True  # Your test here",
                    "```"
                ]
            }
        test_files = [f for f in os.listdir(test_dir) if f.startswith("test_") and f.endswith(".py")]
        if not test_files:
            return [], {
                "error": f"❌ No unit test files found in '{test_dir}'.",
                "next_steps": [
                    "Add test files to the 'tests/unit' directory",
                    "Name your test files starting with 'test_' (e.g., test_basic.py)",
                    "Make sure your test files contain test functions",
                    "Example test file:",
                    "```python",
                    "def test_example():",
                    "    assert True  # Your test here",
                    "```"
                ]
            }
        return test_files, None
    elif test_type == "sample":
        sample_dir = "tests/sample"
        if not os.path.exists(sample_dir):
            return [], {
                "error": f"❌ Sample test directory '{sample_dir}' not found.",
                "next_steps": [
                    "Create a 'sample' directory inside your 'tests' directory",
                    "Add sample test files (e.g., sample_test.py)",
                    "These are for demonstration and quick testing",
                    "Example sample test:",
                    "```python",
                    "def test_sample():",
                    "    assert True  # Your sample test here",
                    "```"
                ]
            }
        test_files = [f for f in os.listdir(sample_dir) if f.endswith(".py")]
        if not test_files:
            return [], {
                "error": f"❌ No sample test files found in '{sample_dir}'.",
                "next_steps": [
                    "Add sample test files to the 'tests/sample' directory",
                    "These are for demonstration purposes",
                    "Example sample test:",
                    "```python",
                    "def test_sample():",
                    "    assert True  # Your sample test here",
                    "```"
                ]
            }
        return test_files, None
    return [], None

def show_run_tests():
    st.header("Run Tests")
    test_types = ["unit", "e2e", "sample", "custom"]
    test_type = st.radio("Select Test Type", test_types, help="Choose the type of test to run.")
    
    # Discover available tests
    available_tests, error_info = discover_tests(test_type)
    
    # Show test discovery status
    if error_info:
        st.error(error_info["error"])
        st.info("💡 What to do next:")
        for step in error_info["next_steps"]:
            st.markdown(step)
        return
    
    # Test selection based on type
    selected_tests = []
    if test_type in ["unit", "sample"] and available_tests:
        st.success(f"✅ Found {len(available_tests)} test files")
        test_selection = st.multiselect(
            "Select tests to run",
            options=["all"] + available_tests,
            default=["all"],
            help="Choose specific tests or 'all' to run everything"
        )
        if "all" in test_selection:
            selected_tests = available_tests
        else:
            selected_tests = [t for t in test_selection if t != "all"]
    
    # E2E test configuration
    config = load_config()
    e2e_urls = config.get("e2e_tests", [])
    url = None
    if test_type == "e2e":
        if not e2e_urls:
            st.warning("⚠️ No E2E test URLs configured")
            st.info("💡 What to do next:")
            st.markdown("""
            1. Go to the Configuration tab
            2. Add URLs to test in the "Edit E2E Test URLs" section
            3. URLs should be complete (e.g., https://example.com)
            4. Make sure the URLs are accessible
            """)
            return
        url = st.selectbox("Select URL to test", e2e_urls)
        st.caption("You can add more URLs in the Configuration tab.")
    
    # Test name for custom/sample tests
    test_name = None
    if test_type in ["sample", "custom"]:
        test_name = st.text_input("Test Name (optional)", help="Enter a name for your test")
    
    # Create placeholders for status messages
    status_placeholder = st.empty()
    error_placeholder = st.empty()

    if st.button("Run Test", disabled=st.session_state.get("test_running")):
        st.session_state["test_running"] = True
        status_placeholder.info("🔄 Test is starting...")
        error_placeholder.empty()
        
        try:
            # Create a placeholder for progress
            progress_placeholder = st.empty()
            progress_bar = progress_placeholder.progress(0.0)  # Start at 0.0
            
            if test_type == "unit":
                if not selected_tests:
                    raise ValueError("No test files selected")
                status_placeholder.info(f"🔄 Running {len(selected_tests)} unit tests...")
                progress_bar.progress(0.25)  # 25% progress
                for i, test_file in enumerate(selected_tests):
                    status_placeholder.info(f"🔄 Running test file: {test_file}")
                    result = core.run_tests("unit", test_file=test_file)
                    if result and result[0].get("status") == "fail":
                        error_msg = result[0].get("error", "Unknown error")
                        raise Exception(f"Test failed: {error_msg}")
                    # Calculate progress between 0.25 and 1.0
                    progress = 0.25 + (0.75 * (i + 1) / len(selected_tests))
                    progress_bar.progress(min(1.0, progress))
                st.session_state["last_test_status"] = f"✅ {len(selected_tests)} unit tests completed successfully!"
            
            elif test_type == "e2e":
                if not url:
                    raise ValueError("No URL selected for E2E testing")
                status_placeholder.info(f"🔄 Running E2E test for {url}...")
                progress_bar.progress(0.25)  # 25% progress
                if url and url not in e2e_urls:
                    e2e_urls.append(url)
                    config["e2e_tests"] = e2e_urls
                    save_config(config)
                result = core.run_tests("e2e", url=url)
                if result and any(r.get("status") == "fail" for r in result):
                    error_msg = next((r.get("error") for r in result if r.get("status") == "fail"), "Unknown error")
                    raise Exception(f"E2E test failed: {error_msg}")
                progress_bar.progress(1.0)  # 100% progress
                st.session_state["last_test_status"] = f"✅ E2E test for {url} completed successfully!"
            
            elif test_type == "sample":
                if not selected_tests:
                    raise ValueError("No sample tests selected")
                status_placeholder.info(f"🔄 Running {len(selected_tests)} sample tests...")
                progress_bar.progress(0.25)  # 25% progress
                for i, test_file in enumerate(selected_tests):
                    status_placeholder.info(f"🔄 Running sample test: {test_file}")
                    result = core.run_tests("sample", test_file=test_file, test_name=test_name)
                    if result and result[0].get("status") == "fail":
                        error_msg = result[0].get("error", "Unknown error")
                        raise Exception(f"Sample test failed: {error_msg}")
                    # Calculate progress between 0.25 and 1.0
                    progress = 0.25 + (0.75 * (i + 1) / len(selected_tests))
                    progress_bar.progress(min(1.0, progress))
                st.session_state["last_test_status"] = f"✅ {len(selected_tests)} sample tests completed successfully!"
            
            elif test_type == "custom":
                status_placeholder.info("🔄 Running custom plugin test...")
                progress_bar.progress(0.25)  # 25% progress
                result = core.run_tests("custom", test_name=test_name)
                if result and result[0].get("status") == "fail":
                    error_msg = result[0].get("error", "Unknown error")
                    raise Exception(f"Custom plugin test failed: {error_msg}")
                progress_bar.progress(1.0)  # 100% progress
                st.session_state["last_test_status"] = "✅ Custom plugin test completed successfully!"
            
            # Clear progress bar
            progress_placeholder.empty()
            
            # Update results
            update_results_state()
            
            # Show success message
            if st.session_state.get("last_test_status", "").startswith("✅"):
                st.success("✅ Test completed successfully!")
                st.info("""
                📊 To view test results:
                1. Go to the Reports tab in the sidebar
                2. You'll find comprehensive test results
                3. Use the refresh button to update the results
                """)
            
        except ValueError as ve:
            error_placeholder.error(f"❌ Configuration Error: {str(ve)}")
            status_placeholder.error("Test execution failed due to configuration issues")
            st.info("💡 What to do next:")
            st.markdown("""
            1. Make sure you've selected the correct test type
            2. For unit/sample tests: Select at least one test file
            3. For E2E tests: Select a valid URL
            4. For custom tests: Make sure your plugin is configured
            """)
        except Exception as e:
            error_placeholder.error(f"❌ Test Error: {str(e)}")
            status_placeholder.error("Test execution failed")
            st.info("💡 Try these steps:")
            st.markdown("""
            1. Check the test configuration
            2. Verify test files exist and are valid
            3. Check test dependencies
            4. Review error message for details
            """)
        finally:
            st.session_state["test_running"] = False

# --- Reports ---
def show_reports_page():
    """Dedicated reports page with its own URL."""
    st.header("Test Reports")
    
    # Ensure we're on the reports page
    if "page" not in st.query_params or st.query_params["page"] != "reports":
        st.query_params.clear()
        st.query_params["page"] = "reports"
        st.rerun()
    
    # Add action buttons
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🔄 Refresh Results", key="refresh_latest_reports", use_container_width=True):
            update_results_state()
            st.rerun()
    with col2:
        if st.button("🗑️ Reset All Results", key="reset_results", use_container_width=True):
            if st.session_state.get("confirm_reset", False):
                db.clear_results()
                update_results_state()
                st.success("✅ All test results have been cleared")
                st.session_state["confirm_reset"] = False
                st.rerun()
            else:
                st.session_state["confirm_reset"] = True
                st.warning("⚠️ Are you sure you want to delete all test results? This cannot be undone.")
                if st.button("✅ Yes, Delete All Results", key="confirm_reset_button", use_container_width=True):
                    db.clear_results()
                    update_results_state()
                    st.success("✅ All test results have been cleared")
                    st.session_state["confirm_reset"] = False
                    st.rerun()
    
    results = st.session_state.get("results", [])
    if results:
        # Convert results to DataFrame for better display
        import pandas as pd
        df = pd.DataFrame([{k: v for k, v in r.__dict__.items() if not k.startswith('_sa_instance_state')} for r in results])
        
        # Add timestamp column for sorting
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp', ascending=False)
        
        # Display the dataframe with better formatting
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "timestamp": st.column_config.DatetimeColumn("Timestamp", format="D MMM, YYYY, HH:mm:ss"),
                "status": st.column_config.TextColumn("Status", help="Test execution status"),
                "test_type": st.column_config.TextColumn("Type", help="Type of test"),
                "name": st.column_config.TextColumn("Name", help="Test name or identifier")
            }
        )
        
        # Add summary metrics with consistent styling
        st.markdown("### Test Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Tests", len(results))
        with col2:
            passed = sum(1 for r in results if r.status == "pass")
            st.metric("Passed Tests", passed, delta=f"{passed/len(results)*100:.1f}%" if results else None)
        with col3:
            failed = sum(1 for r in results if r.status == "fail")
            st.metric("Failed Tests", failed, delta=f"{failed/len(results)*100:.1f}%" if results else None)
        
        # Add export button
        if st.button("📥 Export Results", key="export_results", use_container_width=True):
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                "test_results.csv",
                "text/csv",
                key="download_csv"
            )
    else:
        st.info("No test results available yet. Run some tests to see results here.")

# --- Configuration ---
def show_configuration():
    st.header("Configuration")
    config = load_config()
    st.subheader("Current Configuration (YAML)")
    st.json(config)

    st.subheader("Edit E2E Test URLs")
    e2e_urls = config.get("e2e_tests", [])
    new_url = st.text_input("Add new E2E URL")
    if st.button("Add URL") and new_url:
        if new_url not in e2e_urls:
            e2e_urls.append(new_url)
            config["e2e_tests"] = e2e_urls
            save_config(config)
            st.success(f"Added {new_url}")
        else:
            st.info("URL already exists.")
    if e2e_urls:
        remove_url = st.selectbox("Remove URL", ["None"] + e2e_urls)
        if st.button("Remove Selected URL") and remove_url != "None":
            e2e_urls.remove(remove_url)
            config["e2e_tests"] = e2e_urls
            save_config(config)
            st.success(f"Removed {remove_url}")

    st.subheader("Test Tags (for Filtering)")
    test_tags = config.get("test_tags", [])
    new_tag = st.text_input("Add new test tag (e.g. smoke, regression)")
    if st.button("Add Tag") and new_tag:
        if new_tag not in test_tags:
            test_tags.append(new_tag)
            config["test_tags"] = test_tags
            save_config(config)
            st.success(f"Added tag: {new_tag}")
        else:
            st.info("Tag already exists.")
    if test_tags:
        remove_tag = st.selectbox("Remove Tag", ["None"] + test_tags)
        if st.button("Remove Selected Tag") and remove_tag != "None":
            test_tags.remove(remove_tag)
            config["test_tags"] = test_tags
            save_config(config)
            st.success(f"Removed tag: {remove_tag}")

    st.subheader("Plugin Settings (YAML)")
    plugin_settings = config.get("plugins", {})
    plugin_yaml = st.text_area("Edit plugin settings (YAML)", yaml.dump(plugin_settings))
    if st.button("Save Plugin Settings"):
        try:
            plugin_data = yaml.safe_load(plugin_yaml)
            config["plugins"] = plugin_data
            save_config(config)
            st.success("Plugin settings saved successfully!")
        except Exception as e:
            st.error(f"Error saving plugin settings: {e}")

def show_history_page():
    """Dedicated history page with its own URL."""
    st.header("Test History")
    
    # Add refresh button at the top
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh Results", key="refresh_history", use_container_width=True):
            update_results_state()
            st.rerun()
    
    # Add filters with consistent styling
    st.markdown("### Filter Results")
    col1, col2, col3 = st.columns(3)
    with col1:
        search = st.text_input("Search by test name", "", help="Filter tests by name")
    with col2:
        test_types = ["all", "unit", "e2e", "sample", "custom"]
        filter_type = st.selectbox("Filter by test type", test_types, index=0)
    with col3:
        time_range = st.selectbox(
            "Time Range",
            ["All Time", "Last 24 Hours", "Last 7 Days", "Last 30 Days"],
            index=0
        )
    
    # Add date range filter
    st.markdown("### Date Range")
    col3, col4 = st.columns(2)
    with col3:
        start_date = st.date_input("Start Date", value=None)
    with col4:
        end_date = st.date_input("End Date", value=None)
    
    try:
        # Get results based on time range
        if time_range == "Last 24 Hours":
            results = db.get_recent_results(days=1)
        elif time_range == "Last 7 Days":
            results = db.get_recent_results(days=7)
        elif time_range == "Last 30 Days":
            results = db.get_recent_results(days=30)
        else:
            results = db.get_results()
        
        # Apply filters
        if search:
            results = [r for r in results if search.lower() in (r.name or "").lower()]
        if filter_type != "all":
            results = [r for r in results if r.test_type == filter_type]
        if start_date:
            results = [r for r in results if r.timestamp.date() >= start_date]
        if end_date:
            results = [r for r in results if r.timestamp.date() <= end_date]
        
        if results:
            # Get test summary
            summary = db.get_statistics()
            
            # Display summary metrics
            st.markdown("### Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Tests", summary["total"])
            with col2:
                st.metric("Passed", summary["passed"], 
                         delta=f"{summary['pass_rate']:.1f}%")
            with col3:
                st.metric("Failed", summary["failed"])
            with col4:
                st.metric("Skipped", summary["skipped"])
            
            # Get test type distribution
            test_types = set(r.test_type for r in results)
            type_counts = {t: len([r for r in results if r.test_type == t]) for t in test_types}
            
            # Display test type distribution
            st.markdown("### Test Distribution")
            type_cols = st.columns(len(type_counts))
            for (test_type, count), col in zip(type_counts.items(), type_cols):
                with col:
                    st.metric(test_type.title(), count)
            
            # Convert to DataFrame for better display
            st.markdown("### Test Results")
            import pandas as pd
            df = pd.DataFrame([{k: v for k, v in r.__dict__.items() if not k.startswith('_sa_instance_state')} for r in results])
            
            # Sort by timestamp
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp', ascending=False)
            
            # Display with better formatting
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "timestamp": st.column_config.DatetimeColumn("Timestamp", format="D MMM, YYYY, HH:mm:ss"),
                    "status": st.column_config.TextColumn("Status", help="Test execution status"),
                    "test_type": st.column_config.TextColumn("Type", help="Type of test"),
                    "name": st.column_config.TextColumn("Name", help="Test name or identifier")
                }
            )
            
            # Add export button
            if st.button("📥 Export Results", key="export_history", use_container_width=True):
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "test_history.csv",
                    "text/csv",
                    key="download_csv"
                )
        else:
            st.info("No matching test results found. Try adjusting your filters.")
            
    except Exception as e:
        st.error(f"Error retrieving test history: {str(e)}")
        st.info("💡 Try refreshing the results or check the database connection.")

# --- Session State Helpers ---
def get_results():
    """Retrieve test results from the database (or return an empty list if not available)."""
    try:
        return db.get_results()
    except Exception as e:
        logger.warning("Unable to retrieve results (database or directory not available): " + str(e))
        return []


def update_results_state():
    """Update session state with test results (or an empty list if none available)."""
    st.session_state["results"] = get_results()

# --- (End Session State Helpers) ---

if __name__ == "__main__":
    main()