
import json
import yaml
import os
import logging

# Set up logging
LOG_DIR = os.path.join(os.path.dirname(__file__), 'test_results')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'incident_processor.log')
logging.basicConfig(
    filename=LOG_FILE,
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'sample_data')
# Load Policy.yaml
with open(os.path.join(DATA_DIR, 'Policy.yaml'), 'r') as f:
    policy = yaml.safe_load(f)

# Load Failures.jsonl and filter required fields
failures = []
with open(os.path.join(DATA_DIR, 'Failures.jsonl'), 'r') as f:
    for idx, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            failures.append({
                'test_id': rec.get('test_id'),
                'module': rec.get('module'),
                'environment': rec.get('environment'),
                'failure_type': rec.get('failure_type'),
                'impacted_layers': rec.get('impacted_layers', [])
            })
        except json.JSONDecodeError as e:
            logging.warning(f"Skipping malformed JSON on line {idx}: {e}")
            print(f"Warning: Skipping malformed JSON on line {idx}: {e}")

# Helper functions
def get_layer_minutes(layers, layer_minutes):
    if not layers:
        return 0
    return sum(layer_minutes.get(layer, 0) for layer in layers)

def get_multiplier(key, mapping):
    return mapping.get(key, 1.0)

def get_module_priority(module, priorities):
    return priorities.get(module, 1)

results = []
for incident in failures:
    module = incident.get('module')
    environment = incident.get('environment')
    failure_type = incident.get('failure_type')
    impacted_layers = incident.get('impacted_layers', [])
    test_id = incident.get('test_id', None)

    # Get policy keys
    layer_minutes = policy.get('minutes_per_impacted_layer', {})
    env_mults = policy.get('multipliers', {}).get('by_environment', {})
    fail_mults = policy.get('multipliers', {}).get('by_failure_type', {})
    module_priorities = policy.get('module_priority_score', {})
    upper_cap = policy.get('caps', {}).get('per_incident_minutes_max', None)

    # Base minutes
    base_minutes = get_layer_minutes(impacted_layers, layer_minutes)

    # Multipliers
    env_mult = get_multiplier(environment, env_mults)
    fail_mult = get_multiplier(failure_type, fail_mults)

    # Final minutes
    final_minutes = base_minutes * env_mult * fail_mult
    if upper_cap is not None and final_minutes > upper_cap:
        final_minutes = upper_cap

    # Priority score
    module_priority = get_module_priority(module, module_priorities)
    priority_score = module_priority * env_mult * fail_mult
    priority_score = round(priority_score, 3)

    results.append({
        'test_id': test_id,
        'module': module,
        'environment': environment,
        'failure_type': failure_type,
        'impacted_layers': impacted_layers,
        'base_minutes': base_minutes,
        'final_minutes': final_minutes,
        'priority_score': priority_score
    })

# Sort by priority_score desc, then module asc
def sort_key(x):
    return (-x['priority_score'], x['module'] if x['module'] is not None else '')

results.sort(key=sort_key)

# Write to final_incidents_list.json in test_results
PLAN_FILE = os.path.join(LOG_DIR, 'final_incidents_list.json')
with open(PLAN_FILE, 'w') as f:
    json.dump(results, f, indent=2)

logging.info(f"Plan written to {PLAN_FILE} with {len(results)} incidents.")
print(f"Plan written to {PLAN_FILE} with {len(results)} incidents.")
