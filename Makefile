.PHONY: rbac\:check rbac\:nightly rbac\:drift-demo nightly\:e2e nightly\:e2e\:check

rbac\:check:
	python scripts/rbac_suite_runner.py --mode check

rbac\:nightly:
	python scripts/rbac_suite_runner.py --mode nightly

rbac\:drift-demo:
	RBAC_DRIFT_DEMO=1 python scripts/rbac_suite_runner.py --mode demo

nightly\:e2e:
	python scripts/nightly_e2e_extended_runner.py --mode nightly

nightly\:e2e\:check:
	python scripts/nightly_e2e_extended_runner.py --mode check