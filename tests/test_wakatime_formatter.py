"""
Unit tests for WakaTime formatter module.

Tests the _filter_and_renormalize_other function for filtering "Other" entries
and renormalizing percentages.
"""

import sys
from pathlib import Path

# Add parent directory to path to make sources a package
sys.path.insert(0, str(Path(__file__).parent.parent))

from sources.wakatime_formatter import _filter_and_renormalize_other


class TestFilterAndRenormalizeOther:
    """Test suite for _filter_and_renormalize_other function."""

    def test_empty_list(self):
        """Should return empty list for empty input."""
        result = _filter_and_renormalize_other([])
        assert result == []

    def test_filter_single_other(self):
        """Should remove single 'Other' entry and renormalize."""
        data = [
            {"name": "Python", "text": "10 hrs", "percent": 50.0},
            {"name": "Other", "text": "10 hrs", "percent": 50.0},
        ]
        result = _filter_and_renormalize_other(data)
        assert len(result) == 1
        assert result[0]["name"] == "Python"
        assert result[0]["percent"] == 100.0

    def test_renormalize_multiple(self):
        """Should renormalize percentages when 'Other' is removed."""
        data = [
            {"name": "Python", "text": "8 hrs", "percent": 40.0},
            {"name": "JavaScript", "text": "6 hrs", "percent": 30.0},
            {"name": "Other", "text": "6 hrs", "percent": 30.0},
        ]
        result = _filter_and_renormalize_other(data)
        assert len(result) == 2

        # Python: 40/70 * 100 = 57.14
        # JavaScript: 30/70 * 100 = 42.86
        assert result[0]["name"] == "Python"
        assert abs(result[0]["percent"] - 57.14) < 0.01
        assert result[1]["name"] == "JavaScript"
        assert abs(result[1]["percent"] - 42.86) < 0.01

        # Verify sum is 100
        total = sum(item["percent"] for item in result)
        assert abs(total - 100.0) < 0.01

    def test_all_other(self):
        """Should return empty list if all entries are 'Other'."""
        data = [
            {"name": "Other", "text": "20 hrs", "percent": 100.0},
        ]
        result = _filter_and_renormalize_other(data)
        assert result == []

    def test_case_insensitive(self):
        """Should handle case variations of 'other'."""
        data = [
            {"name": "Python", "text": "10 hrs", "percent": 50.0},
            {"name": "OTHER", "text": "5 hrs", "percent": 25.0},
            {"name": "Other", "text": "5 hrs", "percent": 25.0},
        ]
        result = _filter_and_renormalize_other(data)
        assert len(result) == 1
        assert result[0]["name"] == "Python"
        assert result[0]["percent"] == 100.0

    def test_no_other_entries(self):
        """Should work correctly when no 'Other' entries exist."""
        data = [
            {"name": "Python", "text": "10 hrs", "percent": 50.0},
            {"name": "JavaScript", "text": "10 hrs", "percent": 50.0},
        ]
        result = _filter_and_renormalize_other(data)
        assert len(result) == 2
        # Percentages should be adjusted slightly due to rounding
        total = sum(item["percent"] for item in result)
        assert abs(total - 100.0) < 0.01

    def test_rounding_precision(self):
        """Should round to 2 decimal places."""
        data = [
            {"name": "A", "text": "6 hrs", "percent": 33.3},
            {"name": "B", "text": "6 hrs", "percent": 33.3},
            {"name": "C", "text": "7 hrs", "percent": 33.4},
        ]
        result = _filter_and_renormalize_other(data)
        for item in result:
            # Check that percent has at most 2 decimal places
            percent_str = f"{item['percent']:.2f}"
            assert float(percent_str) == item["percent"]

    def test_real_world_example(self):
        """Test with real-world WakaTime data from user's request."""
        data = [
            {"name": "Other", "text": "38 hrs 23 mins", "percent": 75.98},
            {"name": "LaTeX", "text": "3 hrs 39 mins", "percent": 7.24},
            {"name": "C", "text": "3 hrs 1 min", "percent": 5.98},
            {"name": "Markdown", "text": "2 hrs 5 mins", "percent": 4.13},
            {"name": "Python", "text": "43 mins", "percent": 1.43},
        ]
        result = _filter_and_renormalize_other(data)

        # Should have 4 entries (all except "Other")
        assert len(result) == 4

        # Find each language and verify percentages
        latex = next(item for item in result if item["name"] == "LaTeX")
        c = next(item for item in result if item["name"] == "C")
        markdown = next(item for item in result if item["name"] == "Markdown")
        python = next(item for item in result if item["name"] == "Python")

        # Expected: sum = 18.78, factor = 100/18.78 = 5.325
        # LaTeX: 7.24 * 5.325 = 38.55
        # C: 5.98 * 5.325 = 31.84
        # Markdown: 4.13 * 5.325 = 21.99
        # Python: 1.43 * 5.325 = 7.61
        assert abs(latex["percent"] - 38.55) < 0.1
        assert abs(c["percent"] - 31.84) < 0.1
        assert abs(markdown["percent"] - 21.99) < 0.1
        assert abs(python["percent"] - 7.61) < 0.1

        # Verify sum is 100
        total = sum(item["percent"] for item in result)
        assert abs(total - 100.0) < 0.01

    def test_preserves_other_fields(self):
        """Should preserve text and other fields while updating percent."""
        data = [
            {"name": "Python", "text": "10 hrs 30 mins", "percent": 60.0, "extra": "data"},
            {"name": "Other", "text": "7 hrs", "percent": 40.0},
        ]
        result = _filter_and_renormalize_other(data)
        assert len(result) == 1
        assert result[0]["name"] == "Python"
        assert result[0]["text"] == "10 hrs 30 mins"
        assert result[0]["percent"] == 100.0
        assert result[0]["extra"] == "data"


if __name__ == "__main__":
    # Simple test runner
    import traceback

    test_suite = TestFilterAndRenormalizeOther()
    test_methods = [
        method for method in dir(test_suite)
        if method.startswith("test_")
    ]

    passed = 0
    failed = 0

    for test_name in test_methods:
        try:
            getattr(test_suite, test_name)()
            print(f"✓ {test_name}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_name}")
            traceback.print_exc()
            failed += 1
        except Exception as e:
            print(f"✗ {test_name} (error)")
            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
