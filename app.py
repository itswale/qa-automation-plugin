"""
Streamlit UI for QA Automation Plugin.
"""

import streamlit as st
import yaml
from pathlib import Path
from qa_plugin.core import QACore
from qa_plugin.database import QADatabase, TestResult
from qa_plugin.reports import JSONReporter, AllureReporter
from sqlalchemy import inspect
import os
import webbrowser
from urllib.parse import urljoin
import subprocess
from datetime import datetime

# Initialize components
qa_core = QACore()
db = QADatabase()
json_reporter = JSONReporter()
allure_reporter = AllureReporter()

# --- Navigation Helpers ---
def get_base_url():
    """Get the base URL for the Streamlit app."""
    return f"http://localhost:{st.get_option('server.port')}"

def navigate_to(page, params=None):
    """Navigate to a specific page with optional parameters."""
    base_url = get_base_url()
    url = urljoin(base_url, page)
    if params:
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query_string}"
    webbrowser.open(url)

def handle_navigation():
    """Handle navigation based on query parameters."""
    if "page" in st.query_params:
        page = st.query_params["page"]
        if page == "reports":
            show_reports_page()
            return True
        elif page == "history":
            show_history_page()
            return True
    return False

# --- Session State Helpers ---
def get_results():
    session = db.Session()
    results = session.query(TestResult).order_by(TestResult.timestamp.desc()).all()
    session.close()
    return results

def update_results_state():
    """Update the results in session state from the database."""
    try:
        results = db.get_results()
        st.session_state["results"] = results
        st.session_state["last_update"] = datetime.now()
    except Exception as e:
        st.error(f"Error updating results: {str(e)}")

# --- Config Helpers ---
def load_config():
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {}

def save_config(config):
    with open("config.yaml", "w") as f:
        yaml.dump(config, f)

# --- Main UI ---
def main():
    # Set page config for consistent layout
    st.set_page_config(
        page_title="QA Automation Dashboard",
        page_icon="🧪",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
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
    
    # Test type descriptions with more details
    st.markdown("""
    **Test Type Descriptions:**
    - **unit**: Runs pytest-based unit tests from the `/tests` directory
      - Files must start with `test_` (e.g., `test_login.py`)
      - Tests are discovered automatically
      - You can select specific test files to run
      - Example test:
        ```python
        def test_example():
            assert True  # Your test here
        ```
    - **e2e**: Runs browser-based end-to-end tests
      - Requires configured URLs in the Configuration tab
      - Uses Playwright for browser automation
      - Tests each configured URL
      - Make sure URLs are accessible
    - **sample**: Runs tests from the `/tests/sample` directory
      - For demonstration and quick testing
      - You can select specific sample tests
      - Useful for testing the framework
    - **custom**: Runs your custom plugin logic
      - Uses the configured custom plugin
      - Good for integration with other tools
      - Configure in the Configuration tab
    """)

    # Create placeholders for status messages
    status_placeholder = st.empty()
    report_placeholder = st.empty()
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
                    result = qa_core.run_tests("unit", test_file=test_file)
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
                result = qa_core.run_tests("e2e", url=url)
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
                    result = qa_core.run_tests("sample", test_file=test_file, test_name=test_name)
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
                result = qa_core.run_tests("custom", test_name=test_name)
                if result and result[0].get("status") == "fail":
                    error_msg = result[0].get("error", "Unknown error")
                    raise Exception(f"Custom plugin test failed: {error_msg}")
                progress_bar.progress(1.0)  # 100% progress
                st.session_state["last_test_status"] = "✅ Custom plugin test completed successfully!"
            
            # Clear progress bar
            progress_placeholder.empty()
            
            # Generate report in background
            try:
                results = get_results()
                if not results:
                    report_placeholder.warning("No test results available to generate report.")
                    return
                    
                results_dicts = [{k: v for k, v in r.__dict__.items() if not k.startswith('_sa_instance_state')} for r in results]
                report_path = allure_reporter.generate_report({"tests": results_dicts})
                report_placeholder.success(f"📊 Report generated successfully at: {report_path}")
                
                # Show report buttons if tests completed successfully
                if st.session_state.get("last_test_status", "").startswith("✅"):
                    st.markdown("### Report Actions")
                    st.success("✅ Test completed successfully!")
                    st.info("""
                    📊 To view detailed test reports:
                    1. Go to the Reports tab in the sidebar
                    2. You'll find comprehensive test results and Allure reports
                    3. Use the refresh button to update the results
                    """)
                    
                    # Only keep the Serve Report button
                    if st.button("🌐 Serve Report", key="serve_report_run", use_container_width=True):
                        try:
                            report_path = allure_reporter.serve_report()
                            st.success(f"Report served at: {report_path}")
                            st.info("💡 The report will open in your default browser")
                        except Exception as e:
                            st.error(f"❌ Error serving report: {str(e)}")
                            st.info("💡 Try generating a new report first")
            except Exception as e:
                report_placeholder.error(f"❌ Error generating report: {str(e)}")
                error_placeholder.error("💡 Try these steps:")
                st.markdown("""
                1. Make sure Allure is properly installed
                2. Check if you have test results available
                3. Try cleaning the allure-results directory
                4. Restart the application
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
            error_placeholder.error(f"❌ Error running test: {str(e)}")
            status_placeholder.error("Test execution failed")
            st.info("💡 What to do next:")
            if "ModuleNotFoundError" in str(e):
                st.markdown("""
                1. Check if all required packages are installed:
                   ```bash
                   pip install -r requirements.txt
                   ```
                2. Make sure you're in the correct virtual environment:
                   ```bash
                   source venv/bin/activate  # On Unix/MacOS
                   .\\venv\\Scripts\\activate  # On Windows
                   ```
                3. Try running `pytest` directly to see detailed error messages:
                   ```bash
                   pytest tests/  # For unit tests
                   pytest tests/sample/  # For sample tests
                   ```
                """)
            elif "ImportError" in str(e):
                st.markdown("""
                1. Check if all test files are properly formatted:
                   - Files should start with `test_`
                   - Test functions should start with `test_`
                   - Make sure all imports are correct
                2. Example test file structure:
                   ```python
                   # test_example.py
                   def test_something():
                       assert True  # Your test here
                   ```
                3. Try running the test file directly:
                   ```bash
                   python -m pytest tests/test_example.py -v
                   ```
                """)
            elif "Playwright" in str(e):
                st.markdown("""
                1. Make sure Playwright is installed:
                   ```bash
                   pip install playwright
                   playwright install
                   ```
                2. Check if the URL is accessible
                3. Verify your internet connection
                4. Try accessing the URL in a browser
                """)
            else:
                st.markdown("""
                1. Check the error message above
                2. Make sure all required files exist
                3. Verify your test configuration
                4. Try running a simpler test first
                5. Check the logs for more details
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
    
    # Add tabs for different report views with consistent styling
    tab1, tab2 = st.tabs(["📊 Latest Results", "📈 Allure Reports"])
    
    with tab1:
        st.markdown("### Latest Test Results")
        if st.button("🔄 Refresh Results", key="refresh_latest_reports", use_container_width=True):
            update_results_state()
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
        else:
            st.info("No test results available yet. Run some tests to see results here.")
    
    with tab2:
        st.markdown("### Allure Reports")
        
        # Check if Allure is installed
        try:
            subprocess.run(["allure", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            st.error("❌ Allure command-line tool is not installed or not in PATH")
            st.info("""
            💡 To install Allure:
            1. Install Java Runtime Environment (JRE)
            2. Install Allure command-line tool:
               ```bash
               # Using Scoop (Windows)
               scoop install allure
               
               # Using Homebrew (macOS)
               brew install allure
               
               # Using SDKMAN (Linux/macOS)
               sdk install allure
               ```
            3. Restart the application after installation
            """)
            return
        
        # Check for test results
        if not os.path.exists("allure-results"):
            st.info("No Allure results available. Run some tests first to generate reports.")
            return
        
        # Generate report section
        st.markdown("#### Generate Report")
        if st.button("📊 Generate New Allure Report", key="generate_allure_reports", use_container_width=True):
            with st.spinner("Generating Allure report..."):
                try:
                    results = get_results()
                    if not results:
                        st.warning("No test results available to generate report.")
                        return
                        
                    results_dicts = [{k: v for k, v in r.__dict__.items() if not k.startswith('_sa_instance_state')} for r in results]
                    report_path = allure_reporter.generate_report({"tests": results_dicts})
                    st.success(f"✅ Report generated successfully at: {report_path}")
                except Exception as e:
                    st.error(f"❌ Error generating report: {str(e)}")
                    st.info("💡 Try these steps:")
                    st.markdown("""
                    1. Make sure Allure is properly installed
                    2. Check if you have test results available
                    3. Try cleaning the allure-results directory
                    4. Restart the application
                    """)
        
        # Report actions section
        st.markdown("#### Report Actions")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Open Latest Report", key="view_report_reports", use_container_width=True):
                try:
                    allure_reporter.open_report()
                    st.success("✅ Report opened successfully")
                except Exception as e:
                    st.error(f"❌ Error opening report: {str(e)}")
                    st.info("💡 Make sure to generate a report first")
        
        with col2:
            if st.button("🌐 Serve Report", key="serve_report_reports", use_container_width=True):
                try:
                    if allure_reporter.serve_report():
                        st.success("✅ Report server started successfully")
                        st.info("💡 The report will open in your default browser")
                except Exception as e:
                    st.error(f"❌ Error serving report: {str(e)}")
                    st.info("💡 Try these steps:")
                    st.markdown("""
                    1. Make sure no other Allure server is running
                    2. Generate a new report first
                    3. Check if port 8080 is available
                    4. Try restarting the application
                    """)

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
            summary = db.get_test_summary()
            
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
                st.metric("Pass Rate", f"{summary['pass_rate']:.1f}%")
            
            # Display test type distribution
            st.markdown("### Test Distribution")
            type_cols = st.columns(len(summary["by_type"]))
            for (test_type, count), col in zip(summary["by_type"].items(), type_cols):
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

if __name__ == "__main__":
    main()