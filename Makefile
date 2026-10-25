PY ?= python3
PK = $(PY) -m pilotkit

.PHONY: help demo test redteam eval pilot gate site all clean

help:
	@echo "make demo     ask the same questions as five different employees"
	@echo "make test     unit tests"
	@echo "make redteam  284 adversarial permission tests across 3 ACL modes"
	@echo "make eval     answer quality + refusal accuracy"
	@echo "make pilot    replay the two-week pilot and print the readout"
	@echo "make gate     everything CI enforces (fails on any leak or missed target)"
	@echo "make site     rebuild the interactive demo at site/index.html"

demo:
	@for u in dev rosa alex; do \
		$(PK) ask --no-audit --as $$u "What happened in the Brightwave security incident?"; echo; \
	done
	@$(PK) ask --no-audit --as dev "How do I get access to the staging database?"

test:
	$(PY) -m unittest discover -s tests -t . -v

redteam:
	$(PK) redteam -v

eval:
	$(PK) eval -v

pilot:
	$(PK) pilot

gate:
	$(PY) -m unittest discover -s tests -t .
	$(PK) redteam --gate
	$(PK) eval --gate

site:
	$(PK) build-site

all: gate pilot site

clean:
	rm -rf reports __pycache__ */__pycache__
