
# E-Commerce Incident Processing & Reporting

This project processes e-commerce incident logs using configurable policies, calculates priorities and time estimates, and generates a visual HTML dashboard report.

## Features

- Reads incident logs and applies rules from a policy file
- Calculates how important each incident is and how much time it may take
- Makes a sorted list of incidents to work on (saved as `final_incidents_list.json` in `test_results`)
- Creates a visual dashboard (HTML) with charts and tables
- Uses colors to show how severe each incident is
- Dashboard files (`report.html`, `style.css`) are saved in `test_results/html_result` for better organization
- Can automatically generate reports when you push code (GitHub Actions)
- Can send notifications to Slack

## Prerequisites
- Python 3.11 or higher
- Required Python packages (see `requirements.txt`)

## How to Run

### 1. Process Incidents and Generate Plan
```sh
python incident_processor.py
```
This reads `sample_data/Failures.jsonl` and `sample_data/Policy.yaml`, then writes the sorted plan to `test_results/final_incidents_list.json`.

### 2. Generate the HTML Report
```sh
python generate_html_report.py
```
This creates a dashboard in the `test_results/html_result` folder (`report.html` and `style.css`).

## Project Structure
```
├── incident_processor.py        # Processes incidents and generates plan.json
├── generate_html_report.py      # Generates the HTML dashboard/report
├── report_generation_utils/     # CSS and utility assets
├── sample_data/                 # Input data files (Failures.jsonl, Policy.yaml, etc.)
├── test_results/                # Output folder for reports and assets
├── .github/workflows/           # GitHub Actions workflow files
```

## GitHub Actions
Workflow `generate-ecommerce-incident-report` automates report generation and artifact upload on push or manual trigger.

## Example Commands
```
├── incident_processor.py        # Processes incidents and generates final_incidents_list.json
├── generate_html_report.py      # Generates the HTML dashboard/report
├── report_generation_utils/     # CSS and utility assets
├── sample_data/                 # Input data files (Failures.jsonl, Policy.yaml, etc.)
├── test_results/
│   ├── final_incidents_list.json   # Output plan file
│   └── html_result/
│       ├── report.html             # Dashboard HTML file
│       └── style.css               # Dashboard CSS file
```
- Modify `report_generation_utils/style.css` for custom styles.
