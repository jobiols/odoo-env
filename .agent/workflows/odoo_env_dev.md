---
description: Develop and Test Odoo Env
---

Follow these steps to work on odoo-env.

1. Ensure dependencies are installed in the virtual environment.
   ```bash
   python3 -m venv venv
   ./venv/bin/pip install tornado docker PyYAML
   ```

2. Run the unit tests.
   ```bash
   ./venv/bin/python -m unittest odoo_env/test_oe.py
   ```

3. Verify the CLI manually.
   ```bash
   ./venv/bin/python -m odoo_env.oe --help
   ```
