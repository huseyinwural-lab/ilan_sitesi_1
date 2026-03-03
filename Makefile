.PHONY: rbac\:check rbac\:nightly rbac\:drift-demo

rbac\:check:
	python scripts/rbac_suite_runner.py --mode check

rbac\:nightly:
	python scripts/rbac_suite_runner.py --mode nightly

rbac\:drift-demo:
	RBAC_DRIFT_DEMO=1 python scripts/rbac_suite_runner.py --mode demo