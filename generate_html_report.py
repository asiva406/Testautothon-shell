import json
import os


def generate_html_report(plan_json_path, html_path):
    # Read test plan data from JSON file
    with open(plan_json_path, 'r', encoding='utf-8') as f:
        results = json.load(f)

    # Calculate dashboard summary
    total_incidents = len(results)
    from collections import Counter
    module_counts = Counter([r.get('module', '') for r in results])
    failure_type_counts = Counter([r.get('failure_type', '') for r in results])
    environment_counts = Counter([r.get('environment', '') for r in results])

    # Sort for top 5
    top_modules = module_counts.most_common(5)
    top_failure_types = failure_type_counts.most_common(5)
    top_environments = environment_counts.most_common(5)

    # Prepare data for charts
    module_labels = [m for m, _ in top_modules]
    module_counts_data = [c for _, c in top_modules]
    failure_type_labels = [ft for ft, _ in top_failure_types]
    failure_type_counts_data = [c for _, c in top_failure_types]
    environment_labels = [env for env, _ in top_environments]
    environment_counts_data = [c for _, c in top_environments]

    # Copy style.css to test_results folder
    import shutil
    css_src = os.path.join('report_generation_utils', 'style.css')
    css_dst_dir = os.path.join('test_results')
    css_dst = os.path.join(css_dst_dir, 'style.css')
    os.makedirs(css_dst_dir, exist_ok=True)
    shutil.copyfile(css_src, css_dst)

    # HTML header, external CSS, and Chart.js
    html = f'''
    <html>
    <head>
        <title>E-Commerce Incidents Report</title>
        <link rel="stylesheet" type="text/css" href="style.css">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0"></script>
    </head>
    <body>
    <h1>E-Commerce Incidents Report</h1>
        <div class="dashboard">
            <strong>Total Incidents:</strong> {total_incidents}<br><br>
            <div class="dashboard-flex">
                <div class="dashboard-section">
                    <div style="margin-bottom: 10px; font-size: 1.2em; font-weight: bold;">Modules</div>
                    <canvas id="modulesChart" width="260" height="220"></canvas>
                </div>
                <div class="dashboard-section">
                    <div style="margin-bottom: 10px; font-size: 1.2em; font-weight: bold;">Failure Types</div>
                    <canvas id="failureTypesChart" width="220" height="220"></canvas>
                </div>
                <div class="dashboard-section">
                    <div style="margin-bottom: 10px; font-size: 1.2em; font-weight: bold;">Environments</div>
                    <canvas id="environmentsChart" width="220" height="220"></canvas>
                </div>
            </div>
        </div>
        <script>
            Chart.register(window.ChartDataLabels);
            function makePieConfig(labels, data, colors) {{
                return {{
                    type: 'pie',
                    data: {{
                        labels: labels,
                        datasets: [{{
                            data: data,
                            backgroundColor: colors,
                        }}]
                    }},
                    options: {{
                        plugins: {{
                            legend: {{ display: true, position: 'bottom' }},
                            datalabels: {{
                                color: '#222',
                                font: {{ weight: 'bold' }},
                                formatter: function(value, context) {{
                                    return value;
                                }}
                            }}
                        }}
                    }},
                    plugins: [ChartDataLabels]
                }};
            }}
            function makeBarConfig(labels, data, colors) {{
                return {{
                    type: 'bar',
                    data: {{
                        labels: labels,
                        datasets: [{{
                            label: 'Count',
                            data: data,
                            backgroundColor: colors,
                        }}]
                    }},
                    options: {{
                        plugins: {{
                            legend: {{ display: false }},
                            datalabels: {{
                                anchor: 'end',
                                align: 'top',
                                color: '#222',
                                font: {{ weight: 'bold' }},
                                formatter: function(value) {{ return value; }}
                            }}
                        }},
                        scales: {{
                            y: {{ beginAtZero: true, precision: 0 }}
                        }}
                    }},
                    plugins: [ChartDataLabels]
                }};
            }}
            // Professional color palette
            const proBarColors = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f'];
            const proPieColors = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f'];

            new Chart(document.getElementById('modulesChart'), makeBarConfig({module_labels}, {module_counts_data}, proBarColors));
            new Chart(document.getElementById('failureTypesChart'), makePieConfig({failure_type_labels}, {failure_type_counts_data}, proPieColors));
            new Chart(document.getElementById('environmentsChart'), makePieConfig({environment_labels}, {environment_counts_data}, proPieColors));
        </script>
        <h2>Incidents Table (sorted by priority)</h2>
        <div style="margin-bottom: 10px;">
            <strong>Severity Legend:</strong>
            <span style="background:#f8d7da; color:#333; padding:2px 8px; border-radius:4px; margin-right:8px;">High (&gt; 7)</span>
            <span style="background:#fff3cd; color:#333; padding:2px 8px; border-radius:4px; margin-right:8px;">Medium (4 - 7)</span>
            <span style="background:#d4edda; color:#333; padding:2px 8px; border-radius:4px;">Low (&lt; 4)</span>
        </div>
        <table>
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
    '''

    # Sort results by priority_score descending
    sorted_results = sorted(results, key=lambda r: r.get('priority_score', 0), reverse=True)
    for result in sorted_results:
        score = result.get('priority_score', 0)
        if score > 7:
            row_class = 'high'
        elif 4 <= score <= 7:
            row_class = 'medium'
        else:
            row_class = 'low'
        base_minutes = result.get('base_minutes', '')
        final_minutes = result.get('final_minutes', '')
        priority_score = result.get('priority_score', '')
        # Format decimals to one decimal point if they are numbers
        if isinstance(base_minutes, float):
            base_minutes = f"{base_minutes:.1f}"
        if isinstance(final_minutes, float):
            final_minutes = f"{final_minutes:.1f}"
        if isinstance(priority_score, float):
            priority_score = f"{priority_score:.1f}"
        html += f'<tr class="{row_class}">' \
                f'<td>{result.get("test_id", "")}</td>' \
                f'<td>{result.get("module", "")}</td>' \
                f'<td>{result.get("environment", "")}</td>' \
                f'<td>{result.get("failure_type", "")}</td>' \
                f'<td>{", ".join(result.get("impacted_layers", []))}</td>' \
                f'<td>{base_minutes}</td>' \
                f'<td>{final_minutes}</td>' \
                f'<td>{priority_score}</td></tr>'

    # HTML footer
    html += '''
        </table>
    </body>
    </html>
    '''

    # Write to HTML file
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == "__main__":
    plan_json_path = os.path.join('sample_data', 'plan.json')
    html_path = os.path.join('test_results', 'report.html')
    generate_html_report(plan_json_path, html_path)
    print(f"Report generated at {html_path}")
