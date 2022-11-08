.DEFAULT_GOAL := help
SHELL := /bin/bash
DATE = $(shell date +%Y-%m-%dT%H:%M:%S)

APP_VERSION_FILE = app/version.py

GIT_BRANCH ?= $(shell git symbolic-ref --short HEAD 2> /dev/null || echo "detached")
GIT_COMMIT ?= $(shell git rev-parse HEAD 2> /dev/null || echo "")

VIRTUALENV_ROOT := $(shell [ -z $$VIRTUAL_ENV ] && echo $$(pwd)/venv || echo $$VIRTUAL_ENV)

NVMSH := $(shell [ -f "$(HOME)/.nvm/nvm.sh" ] && echo "$(HOME)/.nvm/nvm.sh" || echo "/usr/local/share/nvm/nvm.sh")

## DEVELOPMENT

.PHONY: bootstrap
bootstrap: generate-version-file ## Set up everything to run the app
	pipenv install --dev
	source $(NVMSH) --no-use && nvm install && npm ci --no-audit
	source $(NVMSH) && npm run build

.PHONY: watch-frontend
watch-frontend:  ## Build frontend and watch for changes
	npm run watch

.PHONY: run-flask
run-flask:  ## Run flask
	pipenv run flask run -p 6012 --host=0.0.0.0

.PHONY: npm-audit
npm-audit:  ## Check for vulnerabilities in NPM packages
	source $(NVMSH) && npm run audit

.PHONY: help
help:
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: generate-version-file
generate-version-file: ## Generates the app version file
	@echo -e "__git_commit__ = \"${GIT_COMMIT}\"\n__time__ = \"${DATE}\"" > ${APP_VERSION_FILE}

.PHONY: test
test: py-lint py-test js-lint js-test ## Run tests

.PHONY: py-lint
py-lint: ## Run python linting scanners
	pipenv run flake8 .
	pipenv run isort --check-only ./app ./tests

.PHONY: py-test
py-test: ## Run python unit tests
	pipenv run py.test -n auto --maxfail=10 tests/

.PHONY: js-lint
js-lint: ## Run javascript linting scanners
	source $(NVMSH) && npm run lint

.PHONY: js-test
js-test: ## Run javascript unit tests
	source $(NVMSH) && npm test

.PHONY: fix-imports
fix-imports: ## Fix imports using isort
	pipenv run isort ./app ./tests

.PHONY: freeze-requirements
freeze-requirements: ## create static requirements.txt
	pipenv requirements > requirements.txt

.PHONY: pip-audit
pip-audit:
	pipenv run pip-audit -r requirements.txt -l --ignore-vuln PYSEC-2022-237
	-pipenv run pip-audit -r requirements_for_test.txt -l

.PHONY: audit
audit: npm-audit pip-audit

.PHONY: static-scan
static-scan:
	pipenv run bandit -r app/

.PHONY: a11y-scan
a11y-scan:
	source $(NVMSH) && npm install -g pa11y-ci
	source $(NVMSH) && pa11y-ci

.PHONY: clean
clean:
	rm -rf node_modules cache target ${CF_MANIFEST_PATH}


## DEPLOYMENT

.PHONY: upload-static ## Upload the static files to be served from S3
upload-static:
	aws s3 cp --region us-west-2 --recursive --cache-control max-age=315360000,immutable ./app/static s3://${DNS_NAME}-static

# .PHONY: cf-failwhale-deployed
# cf-failwhale-deployed:
# 	@cf app notify-admin-failwhale --guid || (echo "notify-admin-failwhale is not deployed on ${CF_SPACE}" && exit 1)

# .PHONY: enable-failwhale
# enable-failwhale: cf-target cf-failwhale-deployed ## Enable the failwhale app and disable admin
# 	@cf map-route notify-admin-failwhale ${DNS_NAME} --hostname www
# 	@cf unmap-route notify-admin ${DNS_NAME} --hostname www
# 	@echo "Failwhale is enabled"

# .PHONY: disable-failwhale
# disable-failwhale: cf-target cf-failwhale-deployed ## Disable the failwhale app and enable admin
# 	@cf map-route notify-admin ${DNS_NAME} --hostname www
# 	@cf unmap-route notify-admin-failwhale ${DNS_NAME} --hostname www
# 	@echo "Failwhale is disabled"
