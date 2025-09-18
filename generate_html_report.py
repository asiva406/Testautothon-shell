import os
import json
from collections import Counter


def generate_html_report(plan_json_path, html_path):
    # Ensure the output directory exists
    html_result_dir = os.path.join("test_results", "html_result")
    html_path = os.path.join(html_result_dir, "report.html")
    output_dir = os.path.dirname(html_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    # Copy style.css to html_result directory
    src_css = os.path.join('report_generation_utils', 'style.css')
    dst_css = os.path.join(html_result_dir, 'style.css')
    if os.path.exists(src_css):
        import shutil
        shutil.copyfile(src_css, dst_css)
    # Read test plan data from JSON file
    with open(plan_json_path, 'r', encoding='utf-8') as f:
        results = json.load(f)

    # Calculate dashboard summary
    total_incidents = len(results)
    module_counts = Counter([r.get('module', '') for r in results])
    failure_type_counts = Counter([r.get('failure_type', '') for r in results])
    environment_counts = Counter([r.get('environment', '') for r in results])


    # Use all modules for the bar graph
    all_modules = list(module_counts.keys())
    all_module_counts = [module_counts[m] for m in all_modules]

    # Keep top 5 for pie charts
    top_failure_types = failure_type_counts.most_common(5)
    top_environments = environment_counts.most_common(5)

    # Prepare data for charts
    module_labels = all_modules
    module_counts_data = all_module_counts
    failure_type_labels = [ft for ft, _ in top_failure_types]
    failure_type_counts_data = [c for _, c in top_failure_types]
    environment_labels = [env for env, _ in top_environments]
    environment_counts_data = [c for _, c in top_environments]

    # Prepare chart data as JSON for JS
    module_labels_js = json.dumps(module_labels)
    module_counts_data_js = json.dumps(module_counts_data)
    failure_type_labels_js = json.dumps(failure_type_labels)
    failure_type_counts_data_js = json.dumps(failure_type_counts_data)
    environment_labels_js = json.dumps(environment_labels)
    environment_counts_data_js = json.dumps(environment_counts_data)

    # HTML header, external CSS, and Chart.js
    html = f'''
    <html>
    <head>
        <title>E-Commerce Incidents Report</title>
        <link rel="stylesheet" type="text/css" href="style.css">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0"></script>
        <script>
        // Table sort and filter logic
        document.addEventListener('DOMContentLoaded', function() {{
            var table = document.getElementById('incidentsTable');
            var headers = table.querySelectorAll('th');
            var sortOrder = {{}};
            headers.forEach(function(th, idx) {{
                th.style.cursor = 'pointer';
                th.addEventListener('click', function() {{
                    sortTable(idx);
                }});
            }});
            function sortTable(colIdx) {{
                var tbody = table.querySelector('tbody');
                var rows = Array.from(tbody.querySelectorAll('tr'));
                var type = headers[colIdx].getAttribute('data-type') || 'string';
                sortOrder[colIdx] = !sortOrder[colIdx];
                // Reset all arrows
                for (let i = 0; i < headers.length; i++) {{
                    document.getElementById('sort-arrow-' + i).innerHTML = '';
                }}
                // Set arrow for sorted column
                let arrow = sortOrder[colIdx] ? '&#9650;' : '&#9660;'; // ▲ or ▼
                document.getElementById('sort-arrow-' + colIdx).innerHTML = arrow;
                rows.sort(function(a, b) {{
                    var v1 = a.children[colIdx].textContent.trim();
                    var v2 = b.children[colIdx].textContent.trim();
                    if (type === 'number') {{
                        v1 = parseFloat(v1) || 0;
                        v2 = parseFloat(v2) || 0;
                    }}
                    if (v1 < v2) return sortOrder[colIdx] ? -1 : 1;
                    if (v1 > v2) return sortOrder[colIdx] ? 1 : -1;
                    return 0;
                }});
                rows.forEach(function(row) {{ tbody.appendChild(row); }});
            }}
            // Filter logic
            var filterInput = document.getElementById('tableFilter');
            filterInput.addEventListener('input', function() {{
                var val = filterInput.value.toLowerCase();
                var tbody = table.querySelector('tbody');
                Array.from(tbody.querySelectorAll('tr')).forEach(function(row) {{
                    row.style.display = Array.from(row.children).some(function(td) {{ return td.textContent.toLowerCase().indexOf(val) !== -1; }}) ? '' : 'none';
                }});
            }});
        }});
        </script>
    </head>
    <body>
    <h1>E-Commerce Incidents Report</h1>
        <div class="dashboard">
            <strong>Total Incidents:</strong> {total_incidents}<br><br>
            <div class="dashboard-flex">
                <div class="dashboard-section">
                    <div style="margin-bottom: 10px; font-size: 1.2em; font-weight: bold;">Modules</div>
                    <canvas id="modulesChart" width="260" height="320"></canvas>
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
                            y: {{ beginAtZero: true, precision: 0 }},
                            x: {{
                                ticks: {{
                                    maxRotation: 60,
                                    minRotation: 45,
                                    autoSkip: false,
                                    font: {{ size: 12 }}
                                }},
                                padding: 30
                            }}
                        }}
                    }},
                    plugins: [ChartDataLabels]
                }};
            }}
            // Professional color palette
            const proBarColors = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f'];
            const proPieColors = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f'];

            new Chart(document.getElementById('modulesChart'), makeBarConfig({module_labels_js}, {module_counts_data_js}, proBarColors));
            new Chart(document.getElementById('failureTypesChart'), makePieConfig({failure_type_labels_js}, {failure_type_counts_data_js}, proPieColors));
            new Chart(document.getElementById('environmentsChart'), makePieConfig({environment_labels_js}, {environment_counts_data_js}, proPieColors));
        </script>
        <h2>Incidents Table (sorted by priority)</h2>
        <div style="margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
            <div>
                <strong>Severity Legend:</strong>
                <span style="background:#f8d7da; color:#333; padding:2px 8px; border-radius:4px; margin-right:8px;">High (&gt; 7)</span>
                <span style="background:#fff3cd; color:#333; padding:2px 8px; border-radius:4px; margin-right:8px;">Medium (4 - 7)</span>
                <span style="background:#d4edda; color:#333; padding:2px 8px; border-radius:4px;">Low (&lt; 4)</span>
            </div>
            <input id="tableFilter" type="text" placeholder="Filter table..." style="padding:6px; width:320px;">
        </div>
        <table id="incidentsTable">
            <thead>
            <tr>
                <th data-type="string">Test ID <span class="sort-arrow" id="sort-arrow-0"></span></th>
                <th data-type="string">Module <span class="sort-arrow" id="sort-arrow-1"></span></th>
                <th data-type="string">Environment <span class="sort-arrow" id="sort-arrow-2"></span></th>
                <th data-type="string">Failure Type <span class="sort-arrow" id="sort-arrow-3"></span></th>
                <th data-type="string">Impacted Layers <span class="sort-arrow" id="sort-arrow-4"></span></th>
                <th data-type="number">Base Minutes <span class="sort-arrow" id="sort-arrow-5"></span></th>
                <th data-type="number">Final Minutes <span class="sort-arrow" id="sort-arrow-6"></span></th>
                <th data-type="number">Priority Score <span class="sort-arrow" id="sort-arrow-7"></span></th>
            </tr>
            </thead>
            <tbody>
    '''

    # Sort results by priority_score descending, then module ascending
    sorted_results = sorted(
        results,
        key=lambda r: (-r.get('priority_score', 0), str(r.get('module', '')))
    )
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
            priority_score = f"{priority_score:.3f}"
        html += f'<tr class="{row_class}">' \
                f'<td>{result.get("test_id", "")}</td>' \
                f'<td>{result.get("module", "")}</td>' \
                f'<td>{result.get("environment", "")}</td>' \
                f'<td>{result.get("failure_type", "")}</td>' \
                f'<td>{", ".join(result.get("impacted_layers", []))}</td>' \
                f'<td>{base_minutes}</td>' \
                f'<td>{final_minutes}</td>' \
                f'<td>{priority_score}</td></tr>'

    html += '''
            </tbody>
        </table>
    </body>
    </html>
    '''

    # Ensure the output directory exists
    output_dir = os.path.dirname(html_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    # Write HTML file
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)


if __name__ == "__main__":
    plan_json_path = os.path.join("test_results", "final_incidents_list.json")
    html_path = os.path.join("test_results", "report.html")

    generate_html_report(plan_json_path, html_path)
