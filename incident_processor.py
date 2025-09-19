
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

# Add assertions to validate generated data
def validate_results(results, policy):
    """Validate the processed incident data for correctness."""
    logging.info("Starting data validation...")
    
    assert results, "Results list should not be empty"
    assert isinstance(results, list), "Results should be a list"
    
    upper_cap = policy.get('caps', {}).get('per_incident_minutes_max')
    layer_minutes = policy.get('minutes_per_impacted_layer', {})
    env_mults = policy.get('multipliers', {}).get('by_environment', {})
    fail_mults = policy.get('multipliers', {}).get('by_failure_type', {})
    module_priorities = policy.get('module_priority_score', {})
    
    for idx, incident in enumerate(results):
        # Test basic structure
        assert isinstance(incident, dict), f"Incident {idx} should be a dictionary"
        required_fields = ['test_id', 'module', 'environment', 'failure_type', 
                          'impacted_layers', 'base_minutes', 'final_minutes', 'priority_score']
        
        for field in required_fields:
            assert field in incident, f"Incident {idx} missing required field: {field}"
        
        # Validate data types
        assert isinstance(incident['impacted_layers'], list), f"Incident {idx}: impacted_layers should be a list"
        assert isinstance(incident['base_minutes'], (int, float)), f"Incident {idx}: base_minutes should be numeric"
        assert isinstance(incident['final_minutes'], (int, float)), f"Incident {idx}: final_minutes should be numeric"
        assert isinstance(incident['priority_score'], (int, float)), f"Incident {idx}: priority_score should be numeric"
        
        # Validate non-negative values
        assert incident['base_minutes'] >= 0, f"Incident {idx}: base_minutes should be non-negative"
        assert incident['final_minutes'] >= 0, f"Incident {idx}: final_minutes should be non-negative"
        assert incident['priority_score'] >= 0, f"Incident {idx}: priority_score should be non-negative"
        
        # Validate upper cap is respected
        if upper_cap is not None:
            assert incident['final_minutes'] <= upper_cap, f"Incident {idx}: final_minutes {incident['final_minutes']} exceeds cap {upper_cap}"
        
        # Validate base_minutes calculation
        expected_base = sum(layer_minutes.get(layer, 0) for layer in incident['impacted_layers'])
        assert incident['base_minutes'] == expected_base, f"Incident {idx}: base_minutes calculation incorrect. Expected {expected_base}, got {incident['base_minutes']}"
        
        # Validate final_minutes calculation (considering multipliers and cap)
        env_mult = env_mults.get(incident['environment'], 1.0)
        fail_mult = fail_mults.get(incident['failure_type'], 1.0)
        expected_final = incident['base_minutes'] * env_mult * fail_mult
        if upper_cap is not None and expected_final > upper_cap:
            expected_final = upper_cap
        
        assert abs(incident['final_minutes'] - expected_final) < 0.001, f"Incident {idx}: final_minutes calculation incorrect. Expected {expected_final}, got {incident['final_minutes']}"
        
        # Validate priority_score calculation
        module_priority = module_priorities.get(incident['module'], 1)
        expected_priority = round(module_priority * env_mult * fail_mult, 3)
        assert abs(incident['priority_score'] - expected_priority) < 0.001, f"Incident {idx}: priority_score calculation incorrect. Expected {expected_priority}, got {incident['priority_score']}"
    
    # Validate sorting order (priority_score desc, then module asc)
    for i in range(len(results) - 1):
        current = results[i]
        next_item = results[i + 1]
        
        if current['priority_score'] == next_item['priority_score']:
            # If priority scores are equal, module should be in ascending order
            current_module = current['module'] if current['module'] is not None else ''
            next_module = next_item['module'] if next_item['module'] is not None else ''
            assert current_module <= next_module, f"Sorting error at index {i}: modules not in ascending order when priority scores are equal"
        else:
            # Priority scores should be in descending order
            assert current['priority_score'] >= next_item['priority_score'], f"Sorting error at index {i}: priority scores not in descending order"
    
    logging.info(f"Data validation completed successfully for {len(results)} incidents.")
    print(f"✓ Data validation passed for {len(results)} incidents.")

# Run validation
try:
    validate_results(results, policy)
except AssertionError as e:
    logging.error(f"Data validation failed: {e}")
    print(f"❌ Data validation failed: {e}")
    raise
except Exception as e:
    logging.error(f"Unexpected error during validation: {e}")
    print(f"❌ Unexpected error during validation: {e}")
    raise

# Write to final_incidents_list.json in test_results
PLAN_FILE = os.path.join(LOG_DIR, 'final_incidents_list.json')
with open(PLAN_FILE, 'w') as f:
    json.dump(results, f, indent=2)

logging.info(f"Plan written to {PLAN_FILE} with {len(results)} incidents.")
print(f"Plan written to {PLAN_FILE} with {len(results)} incidents.")
