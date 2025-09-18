# E-Commerce Incidents Report

This project generates a comprehensive dashboard and HTML report for e-commerce incidents using failure log data and policy configurations.

## Features
- Visual dashboard with bar and pie charts
- Severity-based color coding
- Incident table sorted by priority and module
- GitHub Actions workflow for automated report generation
- Slack Integration

## Prerequisites
- Python 3.11 or higher
- Required Python packages (see `requirements.txt`)

## How to Run

### 1. Run the main script to process the test plan
```sh
python test_plan.py
```

### 2. Generate the HTML Report
```sh
python generate_html_report.py
```

The HTML report and CSS will be generated in the `test_results` folder.

## Project Structure
```
├── test_plan.py                # Main script for processing test plan
├── generate_html_report.py     # Generates the HTML dashboard/report
├── report_generation_utils/    # Contains CSS and utility assets
├── sample_data/                # Input data files (plan.json, Policy.yaml, etc.)
├── test_results/               # Output folder for reports and assets
├── .github/workflows/          # GitHub Actions workflow files
```

## GitHub Actions
A workflow named `generate-ecommerce-incident-report` is provided to automate report generation and artifact upload on push or manual trigger.

## Example Commands
```sh
# Command to run the main script
python test_plan.py

# Command to generate HTML Report
python generate_html_report.py
```

## Customization
- Update `sample_data/plan.json` and `sample_data/Policy.yaml` for your data and policies.
- Modify `report_generation_utils/style.css` for custom styles.
