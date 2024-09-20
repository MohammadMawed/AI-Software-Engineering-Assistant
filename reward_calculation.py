def calculate_reward(tests_passed, lint_errors, comparison_result, code_quality_metrics=None):
    """
    Calculates the reward based on test results, linting errors, comparison results, and code quality metrics.

    Args:
        tests_passed (bool): Whether the tests passed.
        lint_errors (int): Number of linting errors.
        comparison_result (bool): Whether the code comparison succeeded.
        code_quality_metrics (dict, optional): Additional code quality metrics (e.g., cyclomatic complexity).

    Returns:
        int: The calculated reward.
    """
    reward = 0

    # Reward or penalize based on code comparison
    if comparison_result:
        reward += 10
    else:
        reward -= 10

    # Reward or penalize based on test results
    if tests_passed:
        reward += 20
    else:
        reward -= 20

    # Penalize based on the number of linting errors
    # Each linting error reduces the reward by 1 point
    reward -= lint_errors

    # Consider additional code quality metrics if provided
    if code_quality_metrics:
        # Example: Reward based on cyclomatic complexity
        complexity = code_quality_metrics.get('cyclomatic_complexity', 0)
        if complexity <= 10:
            reward += 5
        elif complexity <= 20:
            reward += 0
        else:
            reward -= 5

        # Example: Penalize for code duplication
        duplication = code_quality_metrics.get('code_duplication', 0)
        reward -= duplication  # Each duplicated code instance reduces reward

    # Ensure reward is within reasonable bounds
    reward = max(reward, -100)
    reward = min(reward, 100)

    return reward
