src := $(wildcard *.py)

all: format test
.PHONY: all

format: .build/format
.PHONY: format

test: .build/test
.PHONY: test

clean:
	@rm -rf .build/
.PHONY: clean

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

.build:
	@mkdir .build
