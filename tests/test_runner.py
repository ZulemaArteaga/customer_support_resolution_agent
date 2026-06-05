import sys
import os
import io

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.coordinator import run_coordinator
from tests.test_scenarios import SCENARIOS

def run_test(scenario: dict) -> dict:
    """
    Runs a single test scenario and captures the output.
    Returns a result dict with pass/fail and details.
    """
    print(f"\n{'='*60}")
    print(f"TEST {scenario['id']}: {scenario['name']}")
    print(f"Description: {scenario['description']}")
    print(f"{'='*60}")

    # Capture all printed output
    captured = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = captured

    try:
        # No more patches! This will use real API calls.
        response = run_coordinator(
            scenario['message'],
            session_name=scenario['session_name'],
            resume=scenario['resume']
        )
        print(f"--- Agent: {response}")
        error = None
    except Exception as e:
        error = str(e)
    finally:
        sys.stdout = original_stdout

    output = captured.getvalue()

    # Print the captured output so we can see it
    print(output)

    # Evaluate results
    result = evaluate_scenario(scenario, output, error)

    # Print result summary
    status = "✅ PASSED" if result['passed'] else "❌ FAILED"
    print(f"\n{status} — {scenario['name']}")
    if result['failures']:
        for failure in result['failures']:
            print(f"  ✗ {failure}")
    if result['passes']:
        for passed in result['passes']:
            print(f"  ✓ {passed}")

    return result

def evaluate_scenario(scenario: dict, output: str, error: str) -> dict:
    """
    Evaluates the output of a scenario against expected results.
    """
    failures = []
    passes = []
    output_lower = output.lower()

    expected = scenario['expected']

    # Check 1: Did it crash unexpectedly?
    if error and not expected['should_fail']:
        failures.append(f"Unexpected error: {error}")
    elif not error:
        passes.append("No unexpected errors")

    # Check 2: Are expected keywords in the response?
    for keyword in expected['keywords_in_response']:
        if keyword.lower() in output_lower:
            passes.append(f"Keyword found: '{keyword}'")
        else:
            failures.append(f"Expected keyword missing: '{keyword}'")

    # Check 3: Escalation behavior
    escalated = "escalat" in output_lower
    if expected['should_escalate'] and not escalated:
        failures.append("Expected escalation but none occurred")
    elif expected['should_escalate'] and escalated:
        passes.append("Correctly escalated to human")
    elif not expected['should_escalate'] and escalated:
        failures.append("Unexpected escalation occurred")
    else:
        passes.append("Escalation behavior correct")

    # Check 5: Failure handling
    if expected['should_fail']:
        if "sorry" in output_lower or "couldn't verify" in output_lower or "error" in output_lower:
            passes.append("Graceful failure handled correctly")
        else:
            failures.append("Expected graceful failure but got unexpected output")

    passed = len(failures) == 0
    return {
        "scenario_id": scenario['id'],
        "scenario_name": scenario['name'],
        "passed": passed,
        "passes": passes,
        "failures": failures
    }

def run_all_tests():
    """
    Runs all test scenarios and prints a final summary.
    """
    print("\n" + "="*60)
    print("CUSTOMER SUPPORT AGENT — END TO END TEST SUITE (LIVE API)")
    print("="*60)

    results = []
    for scenario in SCENARIOS:
        result = run_test(scenario)
        results.append(result)

    # Final summary
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)

    passed = sum(1 for r in results if r['passed'])
    failed = sum(1 for r in results if not r['passed'])
    total = len(results)

    for result in results:
        status = "✅" if result['passed'] else "❌"
        print(f"{status} Test {result['scenario_id']}: {result['scenario_name']}")

    print(f"\nTotal: {passed}/{total} passed")

    if failed == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {failed} test(s) failed — review output above for details.")

if __name__ == "__main__":
    run_all_tests()