import json
import os
from flask import Flask, render_template_string
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), 'sample_data')
PLAN_PATH = os.path.join(DATA_DIR, 'plan.json')

app = Flask(__name__)

# Load plan.json
with open(PLAN_PATH, 'r') as f:
    incidents = json.load(f)

df = pd.DataFrame(incidents)

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test Plan Dashboard</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        body { padding: 2em; }
        .table-responsive { max-height: 500px; overflow-y: auto; }
    </style>
</head>
<body>
    <h1>Test Plan Dashboard</h1>
    <h3>Total Incidents: {{ total_incidents }}</h3>
    <div class="row">
        <div class="col-md-4">
            <h5>Top Modules</h5>
            <ul>
            {% for module, count in top_modules %}
                <li>{{ module }}: {{ count }}</li>
            {% endfor %}
            </ul>
        </div>
        <div class="col-md-4">
            <h5>Top Failure Types</h5>
            <ul>
            {% for ft, count in top_failure_types %}
                <li>{{ ft }}: {{ count }}</li>
            {% endfor %}
            </ul>
        </div>
        <div class="col-md-4">
            <h5>Top Environments</h5>
            <ul>
            {% for env, count in top_envs %}
                <li>{{ env }}: {{ count }}</li>
            {% endfor %}
            </ul>
        </div>
    </div>
    <hr>
    <h4>Incidents Table (sorted by priority)</h4>
    <div class="table-responsive">
        <table class="table table-striped table-bordered">
            <thead>
                <tr>
                    <th>Test ID</th>
                    <th>Module</th>
                    <th>Environment</th>
                    <th>Failure Type</th>
                    <th>Impacted Layers</th>
                    <th>Base Minutes</th>
                    <th>Final Minutes</th>
                    <th>Priority Score</th>
                </tr>
            </thead>
            <tbody>
            {% for row in table_rows %}
                <tr>
                    <td>{{ row.test_id }}</td>
                    <td>{{ row.module }}</td>
                    <td>{{ row.environment }}</td>
                    <td>{{ row.failure_type }}</td>
                    <td>{{ row.impacted_layers|join(', ') }}</td>
                    <td>{{ row.base_minutes }}</td>
                    <td>{{ row.final_minutes }}</td>
                    <td>{{ row.priority_score }}</td>
                </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
'''

@app.route('/')
def dashboard():
    # Summary stats
    total_incidents = len(df)
    top_modules = df['module'].value_counts().head(5).items()
    top_failure_types = df['failure_type'].value_counts().head(5).items()
    top_envs = df['environment'].value_counts().head(5).items()
    # Table rows sorted by priority_score desc, module asc
    # Format priority_score and final_minutes to 1 decimal digit
    df['priority_score'] = df['priority_score'].apply(lambda x: f"{x:.1f}" if x is not None else "")
    df['final_minutes'] = df['final_minutes'].apply(lambda x: f"{x:.1f}" if x is not None else "")
    table_rows = df.sort_values(['priority_score', 'module'], ascending=[False, True]).to_dict('records')
    return render_template_string(
        DASHBOARD_HTML,
        total_incidents=total_incidents,
        top_modules=top_modules,
        top_failure_types=top_failure_types,
        top_envs=top_envs,
        table_rows=table_rows
    )

def export_html_report():
    with app.app_context():
        # Summary stats
        total_incidents = len(df)
        top_modules = df['module'].value_counts().head(5).items()
        top_failure_types = df['failure_type'].value_counts().head(5).items()
        top_envs = df['environment'].value_counts().head(5).items()
        table_rows = df.sort_values(['priority_score', 'module'], ascending=[False, True]).to_dict('records')
        html = render_template_string(
            DASHBOARD_HTML,
            total_incidents=total_incidents,
            top_modules=top_modules,
            top_failure_types=top_failure_types,
            top_envs=top_envs,
            table_rows=table_rows
        )
        out_path = os.path.join(os.path.dirname(__file__), 'test_results', 'dashboard_report.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"HTML report exported to {out_path}")

if __name__ == '__main__':
    import sys
    if '--export' in sys.argv:
        export_html_report()
    else:
        app.run(debug=True)
