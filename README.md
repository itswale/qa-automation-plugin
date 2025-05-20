# QA Automation Plugin

A powerful QA automation tool built with Streamlit, designed to simplify test execution and reporting.

## Features

- 🚀 **Streamlit-based UI**: Modern, interactive interface for test management
- 📊 **Built-in Reporting**: Integrated test reporting with Streamlit's visualization capabilities
- 🔄 **Multiple Test Types**: Support for unit, E2E, and custom tests
- 📈 **Test History**: Track test results over time with detailed statistics
- 🔍 **Real-time Monitoring**: Watch test execution progress in real-time
- 📱 **Cloud-Ready**: Deploy to Streamlit Cloud for team-wide access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/qa-automation-plugin.git
cd qa-automation-plugin
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install
```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Access the application at `http://localhost:8502`

### Running Tests

1. **Unit Tests**: Select test files from the unit tests directory
2. **E2E Tests**: Configure URLs and run end-to-end tests
3. **Custom Tests**: Use the plugin system for custom test scenarios

### Viewing Results

- **Reports Tab**: View detailed test results with:
  - Test execution status
  - Test output and error messages
  - Execution time
  - Test statistics
- **History Tab**: Track test history with:
  - Filtering by test type
  - Date range selection
  - Search functionality
  - Test statistics and trends

### Exporting Results

- Export test results as CSV
- View detailed test output in the UI
- Track test history over time

## Configuration

The application uses a `config.yaml` file for configuration:

```yaml
# Test directories
test_dirs:
  unit: "tests/unit"
  e2e: "tests/e2e"
  sample: "tests/sample"

# E2E test URLs
e2e_tests:
  - "https://example.com"
  - "https://test.com"

# Custom plugins
plugins:
  custom: "plugins.custom_plugin.CustomPlugin"
```

## Development

### Project Structure

```
qa-automation-plugin/
├── app.py                 # Streamlit application
├── config.yaml           # Configuration file
├── requirements.txt      # Python dependencies
├── qa_plugin/           # Core plugin package
│   ├── __init__.py
│   ├── core.py          # Core functionality
│   ├── database.py      # Database management
│   ├── reports.py       # Reporting system
│   └── api.py           # API endpoints
├── tests/               # Test directories
│   ├── unit/           # Unit tests
│   ├── e2e/            # E2E tests
│   └── sample/         # Sample tests
└── plugins/            # Custom plugins
    └── custom_plugin.py
```

### Adding Custom Tests

1. Create a new plugin in the `plugins` directory
2. Implement the required interface
3. Register the plugin in `config.yaml`

## Reporting

The application provides comprehensive test reporting through:

1. **Streamlit UI**:
   - Interactive test result visualization
   - Real-time test execution status
   - Detailed error messages and stack traces
   - Test statistics and trends

2. **Database Storage**:
   - Persistent test result storage
   - Historical test data
   - Test execution metrics

3. **Export Options**:
   - CSV export of test results
   - Detailed test output in the UI
   - Test history tracking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository. 