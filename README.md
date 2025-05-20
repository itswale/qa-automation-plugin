# QA Automation Plugin

A Streamlit-based QA automation tool that helps run and manage automated tests with beautiful reporting.

## Features

- Run different types of tests (Unit, E2E, Sample, Custom)
- Beautiful test reports using Allure
- Test history tracking
- Interactive UI for test management
- Support for custom plugins

## Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
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

5. Run the application:
```bash
streamlit run app.py
```

## Deployment to Streamlit Cloud

1. Push your code to GitHub:
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

2. Go to [Streamlit Cloud](https://streamlit.io/cloud)

3. Click "New app"

4. Select your repository, branch, and main file (app.py)

5. Add the following secrets in Streamlit Cloud:
   - `ALLURE_VERSION`: The version of Allure commandline tool (e.g., "2.27.0")

6. Add the following build commands in Streamlit Cloud:
```bash
apt-get update && apt-get install -y default-jre
curl -o allure-commandline.zip -OL https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline/${ALLURE_VERSION}/allure-commandline-${ALLURE_VERSION}.zip
unzip allure-commandline.zip
mv allure-${ALLURE_VERSION} /usr/local/allure
ln -s /usr/local/allure/bin/allure /usr/local/bin/allure
```

## Project Structure

```
qa-automation-plugin/
├── .streamlit/              # Streamlit configuration
├── qa_plugin/              # Core plugin code
│   ├── __init__.py
│   ├── core.py             # Core QA functionality
│   ├── database.py         # Database handling
│   └── reports.py          # Reporting logic
├── tests/                  # Test files
│   ├── unit/              # Unit tests
│   └── sample/            # Sample tests
├── app.py                  # Streamlit application
├── config.yaml            # Configuration file
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Configuration

The application can be configured through `config.yaml`:

```yaml
plugins:
  custom: qa_plugin.plugins.custom.CustomPlugin

e2e_tests:
  - https://example.com
  - https://test.com
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License 