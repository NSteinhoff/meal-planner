src := $(wildcard *.py)

all: format lint test
.PHONY: all

lint: .build/lint
.PHONY: lint

format: .build/format
.PHONY: format

test: .build/test
.PHONY: test

benchmark: .build/benchmark
.PHONY: benchmark

clean:
	@rm -rf .build/
.PHONY: clean

.build/lint: ${src} | .build
	@echo --- Format
	@flake8 $?
	@date +'%Y-%m-%d %H:%M:%S' > $@
	@echo ---

.build/format: ${src} | .build
	@echo --- Format
	@black $?
	@date +'%Y-%m-%d %H:%M:%S' > $@
	@echo ---

.build/test: ${src} | .build
	@echo --- Test
	@bats .
	@date +'%Y-%m-%d %H:%M:%S' > $@
	@echo ---

.build/benchmark: ${src} | .build
	@echo --- Benchmark
	@time -p bats .
	@date +'%Y-%m-%d %H:%M:%S' > $@
	@echo ---

.build:
	@mkdir .build
