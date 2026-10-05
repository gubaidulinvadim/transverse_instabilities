import unittest

import numpy as np

from src.simulation.fill_patterns import build_filling_pattern


class BuildFillingPatternTest(unittest.TestCase):

    def test_legacy_config_fills_every_bucket(self):
        pattern = build_filling_pattern(
            harmonic_number=416,
            bunch_current=1.2e-3,
            config={"n_bunches": 416},
        )

        np.testing.assert_allclose(pattern, np.full(416, 1.2e-3))

    def test_uniform_32_bunch_pattern_uses_13_bucket_spacing(self):
        pattern = build_filling_pattern(
            harmonic_number=416,
            bunch_current=2e-3,
            config={"fill_pattern": "uniform", "n_bunches": 32},
        )

        np.testing.assert_array_equal(
            np.flatnonzero(pattern),
            np.arange(0, 416, 13),
        )
        self.assertEqual(np.count_nonzero(pattern), 32)

    def test_four_trains_with_two_bucket_gaps(self):
        pattern = build_filling_pattern(
            harmonic_number=416,
            bunch_current=1.2e-3,
            config={
                "fill_pattern": "trains",
                "n_trains": 4,
                "bunches_per_train": 102,
                "gap_buckets": 2,
                "n_bunches": 408,
            },
        )

        np.testing.assert_array_equal(
            np.flatnonzero(pattern == 0),
            np.array([102, 103, 206, 207, 310, 311, 414, 415]),
        )
        self.assertEqual(np.count_nonzero(pattern), 408)

    def test_explicit_pattern_sorts_bucket_indices(self):
        pattern = build_filling_pattern(
            harmonic_number=416,
            bunch_current=1e-3,
            config={
                "fill_pattern": "explicit",
                "filled_buckets": [26, 0, 13],
                "n_bunches": 3,
            },
        )

        np.testing.assert_array_equal(np.flatnonzero(pattern), [0, 13, 26])

    def test_uniform_pattern_requires_exact_spacing(self):
        with self.assertRaisesRegex(ValueError, "equidistantly"):
            build_filling_pattern(
                harmonic_number=416,
                bunch_current=1e-3,
                config={"fill_pattern": "uniform", "n_bunches": 23},
            )

    def test_train_pattern_must_fill_ring_circumference(self):
        with self.assertRaisesRegex(ValueError, "one ring circumference"):
            build_filling_pattern(
                harmonic_number=416,
                bunch_current=1e-3,
                config={
                    "fill_pattern": "trains",
                    "n_trains": 4,
                    "bunches_per_train": 100,
                    "gap_buckets": 2,
                },
            )

    def test_explicit_pattern_rejects_duplicate_buckets(self):
        with self.assertRaisesRegex(ValueError, "duplicates"):
            build_filling_pattern(
                harmonic_number=416,
                bunch_current=1e-3,
                config={
                    "fill_pattern": "explicit",
                    "filled_buckets": [0, 13, 13],
                },
            )


if __name__ == "__main__":
    unittest.main()
