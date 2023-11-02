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
	poetry install --sync
	poetry run playwright install --with-deps
	source $(NVMSH) --no-use && nvm install && npm ci --no-audit
	source $(NVMSH) && npm run build

.PHONY: watch-frontend
watch-frontend:  ## Build frontend and watch for changes
	source $(NVMSH) && npm run watch

.PHONY: run-flask
run-flask:  ## Run flask
	poetry run newrelic-admin run-program flask run -p 6012 --host=0.0.0.0

.PHONY: run-flask-bare
run-flask-bare:  ## Run flask without invoking poetry so we can override ENV variables in .env
	flask run -p 6012 --host=0.0.0.0

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
py-lint: ## Run python linting scanners and black
	poetry self add poetry-dotenv-plugin
	poetry run black .
	poetry run flake8 .
	poetry run isort --check-only ./app ./tests

.PHONY: avg-complexity
avg-complexity:
	echo "*** Shows average complexity in radon of all code ***"
	poetry run radon cc ./app -a -na

.PHONY: too-complex
too-complex:
	echo "*** Shows code that got a rating of C, D or F in radon ***"
	poetry run radon cc ./app -a -nc

.PHONY: py-test
py-test: export NEW_RELIC_ENVIRONMENT=test
py-test: ## Run python unit tests
	poetry run coverage run --omit=*/notifications_utils/* -m pytest --maxfail=10 --ignore=tests/end_to_end tests/
	poetry run coverage report --fail-under=96
	poetry run coverage html -d .coverage_cache

.PHONY: dead-code
dead-code:
	poetry run vulture ./app --min-confidence=100

.PHONY: e2e-test
e2e-test: export NEW_RELIC_ENVIRONMENT=test
e2e-test: ## Run end-to-end integration tests
	poetry run pytest -v --browser chromium --browser firefox --browser webkit tests/end_to_end

.PHONY: js-lint
js-lint: ## Run javascript linting scanners
	source $(NVMSH) && npm run lint

.PHONY: js-test
js-test: ## Run javascript unit tests
	source $(NVMSH) && npm test

.PHONY: fix-imports
fix-imports: ## Fix imports using isort
	poetry run isort ./app ./tests

.PHONY: py-lock
py-lock: ## Syncs dependencies and updates lock file without performing recursive internal updates
	poetry lock --no-update
	poetry install --sync

.PHONY: update-utils
update-utils: ## Forces Poetry to pull the latest changes from the notifications-utils repo; requires that you commit the changes to poetry.lock!
	poetry update notifications-utils
	@echo
	@echo !!! PLEASE MAKE SURE TO COMMIT AND PUSH THE UPDATED poetry.lock FILE !!!
	@echo

.PHONY: freeze-requirements
freeze-requirements: ## create static requirements.txt
	poetry export --without-hashes --format=requirements.txt > requirements.txt

.PHONY: pip-audit
pip-audit:
	poetry requirements > requirements.txt
	poetry requirements --dev > requirements_for_test.txt
	poetry run pip-audit -r requirements.txt
	poetry run pip-audit -r requirements_for_test.txt

.PHONY: audit
audit: npm-audit pip-audit

.PHONY: static-scan
static-scan:
	poetry run bandit -r app/

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
