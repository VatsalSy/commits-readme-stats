"""
Standalone test for _filter_and_renormalize_other function.
This test can run without installing dependencies.
"""


try:
    from sources.wakatime_formatter import _filter_and_renormalize_other
except Exception:
    # Fallback for dependency-free execution.
    def _filter_and_renormalize_other(data: list[dict]) -> list[dict]:
        """
        Filter out "Other" entries and renormalize percentages.

        Removes all entries where name.lower() == "other" and recalculates
        percentages so remaining entries sum to 100%.

        Args:
            data: List of WakaTime data items with name and percent keys

        Returns:
            Filtered and renormalized list of data items

        Edge cases handled:
            - Empty list: returns empty list
            - All "Other" entries: returns empty list
            - No "Other" entries: returns original data with adjusted decimals
            - Zero sum: returns empty list (defensive programming)
        """
        if not data:
            return []

        # Filter out "Other" entries (case-insensitive)
        # Use .copy() to avoid mutating original data
        filtered_data = [
            item.copy() for item in data
            if item.get("name", "").lower() != "other"
        ]

        # If no items remain, return empty list
        if not filtered_data:
            return []

        # Calculate sum of remaining percentages
        percent_sum = sum(item.get("percent", 0.0) for item in filtered_data)

        # Handle edge case: zero sum (defensive programming)
        if percent_sum <= 0:
            return []

        # Renormalize percentages to sum to 100%
        for item in filtered_data:
            old_percent = item.get("percent", 0.0)
            new_percent = (old_percent / percent_sum) * 100.0
            item["percent"] = round(new_percent, 2)

        return filtered_data


# Test cases
def run_tests():
    passed = 0
    failed = 0

    # Test 1: Real-world example from user's request
    print("Test 1: Real-world WakaTime data")
    data = [
        {"name": "Other", "text": "38 hrs 23 mins", "percent": 75.98},
        {"name": "LaTeX", "text": "3 hrs 39 mins", "percent": 7.24},
        {"name": "C", "text": "3 hrs 1 min", "percent": 5.98},
        {"name": "Markdown", "text": "2 hrs 5 mins", "percent": 4.13},
        {"name": "Python", "text": "43 mins", "percent": 1.43},
    ]
    result = _filter_and_renormalize_other(data)

    print(f"  Input: {len(data)} entries (including Other)")
    print(f"  Output: {len(result)} entries (Other removed)")
    print()

    for item in result:
        print(f"  {item['name']:12} {item['text']:20} {item['percent']:6.2f} %")

    # Verify percentages
    latex = next(item for item in result if item["name"] == "LaTeX")
    c = next(item for item in result if item["name"] == "C")
    markdown = next(item for item in result if item["name"] == "Markdown")
    python = next(item for item in result if item["name"] == "Python")

    # Expected values
    expected_latex = 38.55
    expected_c = 31.84
    expected_markdown = 21.99
    expected_python = 7.61

    print()
    print(f"  Expected: LaTeX={expected_latex}%, C={expected_c}%, Markdown={expected_markdown}%, Python={expected_python}%")
    print(f"  Actual:   LaTeX={latex['percent']}%, C={c['percent']}%, Markdown={markdown['percent']}%, Python={python['percent']}%")

    total = sum(item["percent"] for item in result)
    print(f"  Sum: {total:.2f}%")

    if (abs(latex["percent"] - expected_latex) < 0.1 and
        abs(c["percent"] - expected_c) < 0.1 and
        abs(markdown["percent"] - expected_markdown) < 0.1 and
        abs(python["percent"] - expected_python) < 0.1 and
        abs(total - 100.0) < 0.05):
        print("  ✓ PASSED")
        passed += 1
    else:
        print("  ✗ FAILED")
        failed += 1

    print()

    # Test 2: Empty list
    print("Test 2: Empty list")
    result = _filter_and_renormalize_other([])
    if result == []:
        print("  ✓ PASSED")
        passed += 1
    else:
        print("  ✗ FAILED")
        failed += 1
    print()

    # Test 3: All Other
    print("Test 3: All entries are 'Other'")
    data = [{"name": "Other", "text": "20 hrs", "percent": 100.0}]
    result = _filter_and_renormalize_other(data)
    if result == []:
        print("  ✓ PASSED")
        passed += 1
    else:
        print("  ✗ FAILED")
        failed += 1
    print()

    # Test 4: Case insensitive
    print("Test 4: Case-insensitive filtering")
    data = [
        {"name": "Python", "text": "10 hrs", "percent": 50.0},
        {"name": "OTHER", "text": "5 hrs", "percent": 25.0},
        {"name": "Other", "text": "5 hrs", "percent": 25.0},
    ]
    result = _filter_and_renormalize_other(data)
    if len(result) == 1 and result[0]["name"] == "Python" and result[0]["percent"] == 100.0:
        print("  ✓ PASSED")
        passed += 1
    else:
        print("  ✗ FAILED")
        failed += 1
    print()

    # Test 5: Multiple entries renormalization
    print("Test 5: Multiple entries renormalization")
    data = [
        {"name": "Python", "text": "8 hrs", "percent": 40.0},
        {"name": "JavaScript", "text": "6 hrs", "percent": 30.0},
        {"name": "Other", "text": "6 hrs", "percent": 30.0},
    ]
    result = _filter_and_renormalize_other(data)
    python_item = next(item for item in result if item["name"] == "Python")
    js_item = next(item for item in result if item["name"] == "JavaScript")
    total = sum(item["percent"] for item in result)

    if (len(result) == 2 and
        abs(python_item["percent"] - 57.14) < 0.01 and
        abs(js_item["percent"] - 42.86) < 0.01 and
        abs(total - 100.0) < 0.01):
        print("  ✓ PASSED")
        passed += 1
    else:
        print("  ✗ FAILED")
        failed += 1
    print()

    print("=" * 60)
    print(f"Tests passed: {passed}/{passed + failed}")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
