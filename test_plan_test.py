import unittest
import json
import yaml

class TestPlanLogic(unittest.TestCase):
    def setUp(self):
        self.policy = {
            'layer_minutes': {'UI': 10, 'API': 20},
            'environment_multipliers': {'prod': 2.0, 'dev': 1.0},
            'failure_type_multipliers': {'crash': 3.0, 'timeout': 2.0},
            'module_priorities': {'auth': 5, 'payment': 10},
            'upper_cap_minutes': 100
        }

    def test_base_minutes(self):
        from test_plan import get_layer_minutes
        self.assertEqual(get_layer_minutes(['UI', 'API'], self.policy['layer_minutes']), 30)
        self.assertEqual(get_layer_minutes([], self.policy['layer_minutes']), 0)
        self.assertEqual(get_layer_minutes(['Unknown'], self.policy['layer_minutes']), 0)

    def test_multiplier(self):
        from test_plan import get_multiplier
        self.assertEqual(get_multiplier('prod', self.policy['environment_multipliers']), 2.0)
        self.assertEqual(get_multiplier('unknown', self.policy['environment_multipliers']), 1.0)

    def test_module_priority(self):
        from test_plan import get_module_priority
        self.assertEqual(get_module_priority('auth', self.policy['module_priorities']), 5)
        self.assertEqual(get_module_priority('unknown', self.policy['module_priorities']), 1)

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

if __name__ == '__main__':
    unittest.main()
