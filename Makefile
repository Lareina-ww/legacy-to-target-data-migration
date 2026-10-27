.PHONY: setup migrate test clean

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install -r requirements.txt

migrate:
	.venv/bin/python run_migration.py

test:
	.venv/bin/python -m pytest -q

clean:
	rm -f outputs/target.db outputs/exception_log.csv outputs/migration_report.md
	rm -f outputs/reconciliation_report.md outputs/reconciliation_summary.json outputs/uat_checklist.md

