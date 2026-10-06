import unittest

import numpy as np
from mbtrack2.tracking import ACSkewQuadrupole, SkewQuadrupole

from src.simulation.emittance_control import setup_emittance_control


class FakeRing:

    def __init__(self):
        self.emit = np.array([100.0, 0.0])
        self.tune = np.array([54.23, 18.21])


class SetupEmittanceControlTest(unittest.TestCase):

    def test_default_non_unity_ratio_uses_white_noise(self):
        ring = FakeRing()

        method, element = setup_emittance_control(
            ring,
            {"emittance_ratio": 0.3},
        )

        self.assertEqual(method, "white_noise")
        self.assertIsNone(element)
        self.assertEqual(ring.emit[1], 30.0)
        np.testing.assert_allclose(ring.tune, [54.23, 18.21])

    def test_default_unity_ratio_preserves_static_skew_behavior(self):
        ring = FakeRing()

        method, element = setup_emittance_control(
            ring,
            {"emittance_ratio": 1.0},
        )

        self.assertEqual(method, "skew_quadrupole")
        self.assertIsInstance(element, SkewQuadrupole)
        self.assertEqual(element.strength, 0.001)
        self.assertEqual(ring.emit[1], 2.0)
        np.testing.assert_allclose(ring.tune, [54.2, 18.2])

    def test_explicit_white_noise_can_produce_unity_ratio(self):
        ring = FakeRing()

        method, element = setup_emittance_control(
            ring,
            {
                "emittance_control_method": "white_noise",
                "emittance_ratio": 1.0,
            },
        )

        self.assertEqual(method, "white_noise")
        self.assertIsNone(element)
        self.assertEqual(ring.emit[1], 100.0)
        np.testing.assert_allclose(ring.tune, [54.23, 18.21])

    def test_auto_method_selects_from_emittance_ratio(self):
        white_noise_method, white_noise_element = setup_emittance_control(
            FakeRing(),
            {
                "emittance_control_method": "auto",
                "emittance_ratio": 0.3,
            },
        )
        skew_method, skew_element = setup_emittance_control(
            FakeRing(),
            {
                "emittance_control_method": "auto",
                "emittance_ratio": 1.0,
                "skew_strength": 0.004,
            },
        )

        self.assertEqual(white_noise_method, "white_noise")
        self.assertIsNone(white_noise_element)
        self.assertEqual(skew_method, "skew_quadrupole")
        self.assertIsInstance(skew_element, SkewQuadrupole)
        self.assertEqual(skew_element.strength, 0.004)

    def test_static_skew_parameters_are_configurable(self):
        ring = FakeRing()

        method, element = setup_emittance_control(
            ring,
            {
                "emittance_control_method": "skew_quadrupole",
                "coupling_base_emittance_ratio": 0.01,
                "skew_strength": 0.005,
                "skew_tune_x": 54.25,
                "skew_tune_y": 18.25,
            },
        )

        self.assertEqual(method, "skew_quadrupole")
        self.assertIsInstance(element, SkewQuadrupole)
        self.assertEqual(element.strength, 0.005)
        self.assertEqual(ring.emit[1], 1.0)
        np.testing.assert_allclose(ring.tune, [54.25, 18.25])

    def test_ac_skew_uses_tune_difference_frequency_by_default(self):
        ring = FakeRing()

        method, element = setup_emittance_control(
            ring,
            {"emittance_control_method": "ac_skew_quadrupole"},
        )

        self.assertEqual(method, "ac_skew_quadrupole")
        self.assertIsInstance(element, ACSkewQuadrupole)
        self.assertEqual(ring.emit[1], 2.0)
        self.assertAlmostEqual(element.frequency, 0.02)
        np.testing.assert_allclose(ring.tune, [54.23, 18.21])

    def test_ac_skew_strength_and_frequency_are_configurable(self):
        ring = FakeRing()

        method, element = setup_emittance_control(
            ring,
            {
                "emittance_control_method": "ac_skew_quadrupole",
                "coupling_base_emittance_ratio": 0.01,
                "ac_skew_strength": 0.004,
                "ac_skew_frequency": 0.025,
                "ac_skew_seed": 7,
            },
        )

        self.assertEqual(method, "ac_skew_quadrupole")
        self.assertEqual(ring.emit[1], 1.0)
        self.assertEqual(element.strength, 0.004)
        self.assertEqual(element.frequency, 0.025)
        self.assertEqual(element.initial_phase, 0.0)
        self.assertEqual(element.frequency_jitter, 0.0)

    def test_unknown_method_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            setup_emittance_control(
                FakeRing(),
                {"emittance_control_method": "invalid"},
            )


if __name__ == "__main__":
    unittest.main()
