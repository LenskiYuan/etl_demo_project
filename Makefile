PYTHONPATH=src
PYTHON=python3

.PHONY: demo generate etl report test clean

demo: generate etl report

generate:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m medical_ai_demo.pipeline generate --seed 7 --requests 120

etl:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m medical_ai_demo.pipeline etl

report:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m medical_ai_demo.pipeline report

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m unittest discover -s tests -p 'test_*.py'

clean:
	rm -rf data/generated/raw data/generated/analytics data/generated/reports
