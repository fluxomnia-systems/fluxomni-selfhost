# Workflow checks

The Installer workflow runs when installer, Compose, test or helper sources change. It checks shell syntax and ShellCheck, runs Ruff for Python helpers, tests the public install proxy and runs the full installer test suite.

Credential replacement uses `scripts/node-credentials.py`; changes to that helper run the same checks and the saved-candidate recovery tests in `tests/test_node_credentials.py`.
