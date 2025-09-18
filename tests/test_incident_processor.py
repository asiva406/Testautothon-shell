import unittest
import sys
import os
# Ensure parent directory is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
import yaml

class TestPlanLogic(unittest.TestCase):
    def setUp(self):
            self.policy = {
                'layer_minutes': {'UI': 10, 'API': 20, 'DB': 15},
                'environment_multipliers': {'prod': 2.0, 'dev': 1.0, 'qa': 1.5},
                'failure_type_multipliers': {'crash': 3.0, 'timeout': 2.0, 'error': 1.5},
                'module_priorities': {'auth': 5, 'payment': 10, 'report': 0},
                'upper_cap_minutes': 100
            }

    def test_base_minutes(self):
        from incident_processor import get_layer_minutes
        self.assertEqual(get_layer_minutes(['UI', 'API'], self.policy['layer_minutes']), 30)
        self.assertEqual(get_layer_minutes([], self.policy['layer_minutes']), 0)
        self.assertEqual(get_layer_minutes(['Unknown'], self.policy['layer_minutes']), 0)
        self.assertEqual(get_layer_minutes(['UI', 'Unknown'], self.policy['layer_minutes']), 10)
        self.assertEqual(get_layer_minutes(['DB', 'API'], self.policy['layer_minutes']), 35)

    def test_multiplier(self):
        from incident_processor import get_multiplier
        self.assertEqual(get_multiplier('prod', self.policy['environment_multipliers']), 2.0)
        self.assertEqual(get_multiplier('unknown', self.policy['environment_multipliers']), 1.0)
        self.assertEqual(get_multiplier('qa', self.policy['environment_multipliers']), 1.5)
        self.assertEqual(get_multiplier('', self.policy['environment_multipliers']), 1.0)

    def test_module_priority(self):
        from incident_processor import get_module_priority
        self.assertEqual(get_module_priority('auth', self.policy['module_priorities']), 5)
        self.assertEqual(get_module_priority('unknown', self.policy['module_priorities']), 1)
        self.assertEqual(get_module_priority('report', self.policy['module_priorities']), 0)

    def test_final_minutes_and_priority(self):
        # Simulate incident
        incident = {
            'module': 'auth',
            'environment': 'prod',
            'failure_type': 'crash',
            'impacted_layers': ['UI', 'API']
        }
        base_minutes = 30
        env_mult = 2.0
        fail_mult = 3.0
        final_minutes = base_minutes * env_mult * fail_mult
        if final_minutes > self.policy['upper_cap_minutes']:
            final_minutes = self.policy['upper_cap_minutes']
        self.assertEqual(final_minutes, 100)
        module_priority = 5
        priority_score = round(module_priority * env_mult * fail_mult, 3)
        self.assertEqual(priority_score, 30.0)

    def test_final_minutes_no_layers(self):
        from incident_processor import get_layer_minutes, get_multiplier, get_module_priority
        base_minutes = get_layer_minutes([], self.policy['layer_minutes'])
        env_mult = get_multiplier('dev', self.policy['environment_multipliers'])
        fail_mult = get_multiplier('timeout', self.policy['failure_type_multipliers'])
        final_minutes = base_minutes * env_mult * fail_mult
        self.assertEqual(final_minutes, 0)
        module_priority = get_module_priority('payment', self.policy['module_priorities'])
        priority_score = round(module_priority * env_mult * fail_mult, 3)
        self.assertEqual(priority_score, 20.0)

    def test_final_minutes_upper_cap(self):
        from incident_processor import get_layer_minutes, get_multiplier
        base_minutes = get_layer_minutes(['API', 'DB'], self.policy['layer_minutes'])
        env_mult = get_multiplier('prod', self.policy['environment_multipliers'])
        fail_mult = get_multiplier('crash', self.policy['failure_type_multipliers'])
        final_minutes = base_minutes * env_mult * fail_mult
        if final_minutes > self.policy['upper_cap_minutes']:
            final_minutes = self.policy['upper_cap_minutes']
        self.assertEqual(final_minutes, 100)

    def test_priority_score_zero_module(self):
        from incident_processor import get_module_priority, get_multiplier
        module_priority = get_module_priority('report', self.policy['module_priorities'])
        env_mult = get_multiplier('qa', self.policy['environment_multipliers'])
        fail_mult = get_multiplier('error', self.policy['failure_type_multipliers'])
        priority_score = round(module_priority * env_mult * fail_mult, 3)
        self.assertEqual(priority_score, 0.0)

    def test_priority_score_missing_keys(self):
        from incident_processor import get_module_priority, get_multiplier
        module_priority = get_module_priority(None, self.policy['module_priorities'])
        env_mult = get_multiplier(None, self.policy['environment_multipliers'])
        fail_mult = get_multiplier(None, self.policy['failure_type_multipliers'])
        priority_score = round(module_priority * env_mult * fail_mult, 3)
        self.assertEqual(priority_score, 1.0)

    def test_empty_policy(self):
        from incident_processor import get_layer_minutes, get_multiplier, get_module_priority
        empty_policy = {}
        self.assertEqual(get_layer_minutes(['UI'], empty_policy), 0)
        self.assertEqual(get_multiplier('prod', empty_policy), 1.0)
        self.assertEqual(get_module_priority('auth', empty_policy), 1)

    def test_none_inputs(self):
        from incident_processor import get_layer_minutes, get_multiplier, get_module_priority
        self.assertEqual(get_layer_minutes(None, self.policy['layer_minutes']), 0)
        self.assertEqual(get_multiplier(None, self.policy['environment_multipliers']), 1.0)
        self.assertEqual(get_module_priority(None, self.policy['module_priorities']), 1)

    def test_multiple_unknown_layers(self):
        from incident_processor import get_layer_minutes
        self.assertEqual(get_layer_minutes(['Unknown1', 'Unknown2'], self.policy['layer_minutes']), 0)

    def test_large_layer_list(self):
        from incident_processor import get_layer_minutes
        layers = ['UI', 'API', 'DB', 'Unknown', 'UI', 'DB']
        expected = 10 + 20 + 15 + 0 + 10 + 15
        self.assertEqual(get_layer_minutes(layers, self.policy['layer_minutes']), expected)

if __name__ == '__main__':
    unittest.main()
