.DEFAULT_GOAL := help
SHELL := /bin/bash
DATE = $(shell date +%Y-%m-%dT%H:%M:%S)

APP_VERSION_FILE = app/version.py

GIT_BRANCH ?= $(shell git symbolic-ref --short HEAD 2> /dev/null || echo "detached")
GIT_COMMIT ?= $(shell git rev-parse HEAD 2> /dev/null || echo "")

DOCKER_IMAGE_TAG := $(shell cat docker/VERSION)
DOCKER_BUILDER_IMAGE_NAME = govuk/notify-admin-builder:${DOCKER_IMAGE_TAG}

BUILD_TAG ?= notifications-admin-manual
BUILD_NUMBER ?= 0
DEPLOY_BUILD_NUMBER ?= ${BUILD_NUMBER}
BUILD_URL ?=

DOCKER_CONTAINER_PREFIX = ${USER}-${BUILD_TAG}

CF_API ?= api.cloud.service.gov.uk
CF_ORG ?= govuk-notify
CF_SPACE ?= ${DEPLOY_ENV}
CF_HOME ?= ${HOME}
CF_APP ?= notify-admin
CF_MANIFEST_PATH ?= /tmp/manifest.yml
$(eval export CF_HOME)

NOTIFY_CREDENTIALS ?= ~/.notify-credentials

VIRTUALENV_ROOT := $(shell [ -z $$VIRTUAL_ENV ] && echo $$(pwd)/venv || echo $$VIRTUAL_ENV)


## DEVELOPMENT

.PHONY: help
help:
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: virtualenv
virtualenv:
	[ -z $$VIRTUAL_ENV ] && [ ! -d venv ] && python3 -m venv venv || true

.PHONY: upgrade-pip
upgrade-pip: virtualenv
	${VIRTUALENV_ROOT}/bin/pip install --upgrade pip

.PHONY: requirements
requirements: upgrade-pip requirements.txt
	${VIRTUALENV_ROOT}/bin/pip install -r requirements.txt

.PHONY: requirements-for-test
requirements-for-test: upgrade-pip requirements_for_test.txt
	${VIRTUALENV_ROOT}/bin/pip install -r requirements_for_test.txt

.PHONY: frontend
frontend:
	npm set progress=false
	npm install
	npm rebuild node-sass

.PHONY: generate-version-file
generate-version-file: ## Generates the app version file
	@echo -e "__git_commit__ = \"${GIT_COMMIT}\"\n__time__ = \"${DATE}\"" > ${APP_VERSION_FILE}

.PHONY: build
build: frontend requirements-for-test generate-version-file
	npm run build

.PHONY: test
test: ## Run tests
	./scripts/run_tests.sh

.PHONY: fix-imports
fix-imports:
	isort -rc ./app ./tests

.PHONY: freeze-requirements
freeze-requirements: requirements-for-test requirements.in requirements_for_test.in
	${VIRTUALENV_ROOT}/bin/pip-compile requirements.in
	${VIRTUALENV_ROOT}/bin/pip-compile requirements_for_test.in

.PHONY: prepare-docker-build-image
prepare-docker-build-image: ## Prepare the Docker builder image
	make -C docker build

define run_docker_container
	@docker run -it --rm \
		--name "${DOCKER_CONTAINER_PREFIX}-${1}" \
		-v "`pwd`:/var/project" \
		-e UID=$(shell id -u) \
		-e GID=$(shell id -g) \
		-e GIT_COMMIT=${GIT_COMMIT} \
		-e BUILD_NUMBER=${BUILD_NUMBER} \
		-e BUILD_URL=${BUILD_URL} \
		-e http_proxy="${HTTP_PROXY}" \
		-e HTTP_PROXY="${HTTP_PROXY}" \
		-e https_proxy="${HTTPS_PROXY}" \
		-e HTTPS_PROXY="${HTTPS_PROXY}" \
		-e NO_PROXY="${NO_PROXY}" \
		-e CI_NAME=${CI_NAME} \
		-e CI_BUILD_NUMBER=${BUILD_NUMBER} \
		-e CI_BUILD_URL=${BUILD_URL} \
		-e CI_BRANCH=${GIT_BRANCH} \
		-e CI_PULL_REQUEST=${CI_PULL_REQUEST} \
		-e CF_API="${CF_API}" \
		-e CF_USERNAME="${CF_USERNAME}" \
		-e CF_PASSWORD="${CF_PASSWORD}" \
		-e CF_ORG="${CF_ORG}" \
		-e CF_SPACE="${CF_SPACE}" \
		${DOCKER_BUILDER_IMAGE_NAME} \
		${2}
endef

.PHONY: build-with-docker
build-with-docker: prepare-docker-build-image ## Build inside a Docker container
	$(call run_docker_container,build,gosu hostuser make build)

.PHONY: test-with-docker
test-with-docker: prepare-docker-build-image ## Run tests inside a Docker container
	$(call run_docker_container,test,gosu hostuser make test)

.PHONY: clean-docker-containers
clean-docker-containers: ## Clean up any remaining docker containers
	docker rm -f $(shell docker ps -q -f "name=${DOCKER_CONTAINER_PREFIX}") 2> /dev/null || true

.PHONY: clean
clean:
	rm -rf node_modules cache target ${CF_MANIFEST_PATH}


## DEPLOYMENT

.PHONY: check-env-vars
check-env-vars: ## Check mandatory environment variables
	$(if ${DEPLOY_ENV},,$(error Must specify DEPLOY_ENV))
	$(if ${DNS_NAME},,$(error Must specify DNS_NAME))

.PHONY: preview
preview: ## Set environment to preview
	$(eval export DEPLOY_ENV=preview)
	$(eval export DNS_NAME="notify.works")
	@true

.PHONY: staging
staging: ## Set environment to staging
	$(eval export DEPLOY_ENV=staging)
	$(eval export DNS_NAME="staging-notify.works")
	@true

.PHONY: production
production: ## Set environment to production
	$(eval export DEPLOY_ENV=production)
	$(eval export DNS_NAME="notifications.service.gov.uk")
	@true

.PHONY: cf-login
cf-login: ## Log in to Cloud Foundry
	$(if ${CF_USERNAME},,$(error Must specify CF_USERNAME))
	$(if ${CF_PASSWORD},,$(error Must specify CF_PASSWORD))
	$(if ${CF_SPACE},,$(error Must specify CF_SPACE))
	@echo "Logging in to Cloud Foundry on ${CF_API}"
	@cf login -a "${CF_API}" -u ${CF_USERNAME} -p "${CF_PASSWORD}" -o "${CF_ORG}" -s "${CF_SPACE}"

.PHONY: generate-manifest
generate-manifest:
	$(if ${CF_APP},,$(error Must specify CF_APP))
	$(if ${CF_SPACE},,$(error Must specify CF_SPACE))
	$(if $(shell which gpg2), $(eval export GPG=gpg2), $(eval export GPG=gpg))
	$(if ${GPG_PASSPHRASE_TXT}, $(eval export DECRYPT_CMD=echo -n $$$${GPG_PASSPHRASE_TXT} | ${GPG} --quiet --batch --passphrase-fd 0 --pinentry-mode loopback -d), $(eval export DECRYPT_CMD=${GPG} --quiet --batch -d))

	@jinja2 --strict manifest.yml.j2 \
	    -D environment=${CF_SPACE} \
	    -D CF_APP=${CF_APP} \
	    --format=yaml \
	    <(${DECRYPT_CMD} ${NOTIFY_CREDENTIALS}/credentials/${CF_SPACE}/paas/environment-variables.gpg) 2>&1

.PHONY: upload-static ## Upload the static files to be served from S3
upload-static:
	aws s3 cp --region eu-west-1 --recursive --cache-control max-age=315360000,immutable ./app/static s3://${DNS_NAME}-static

.PHONY: cf-deploy
cf-deploy: ## Deploys the app to Cloud Foundry
	$(if ${CF_SPACE},,$(error Must specify CF_SPACE))
	@cf app --guid notify-admin || exit 1
	# cancel any existing deploys to ensure we can apply manifest (if a deploy is in progress you'll see ScaleDisabledDuringDeployment)
	cf cancel-deployment ${CF_APP} || true

	# generate manifest (including secrets) and write it to CF_MANIFEST_PATH (in /tmp/)
	make -s CF_APP=${CF_APP} generate-manifest > ${CF_MANIFEST_PATH}
	# reads manifest from CF_MANIFEST_PATH
	CF_STARTUP_TIMEOUT=10 cf push ${CF_APP} --strategy=rolling -f ${CF_MANIFEST_PATH}
	# delete old manifest file
	rm -f ${CF_MANIFEST_PATH}

.PHONY: cf-deploy-prototype
cf-deploy-prototype: cf-target ## Deploys the first prototype to Cloud Foundry
	make -s CF_APP=notify-admin-prototype generate-manifest > ${CF_MANIFEST_PATH}
	cf push notify-admin-prototype --strategy=rolling -f ${CF_MANIFEST_PATH}
	rm -f ${CF_MANIFEST_PATH}

.PHONY: cf-deploy-prototype-2
cf-deploy-prototype-2: cf-target ## Deploys the second prototype to Cloud Foundry
	make -s CF_APP=notify-admin-prototype-2 generate-manifest > ${CF_MANIFEST_PATH}
	cf push notify-admin-prototype-2 --strategy=rolling -f ${CF_MANIFEST_PATH}
	rm -f ${CF_MANIFEST_PATH}

.PHONY: cf-rollback
cf-rollback: cf-target ## Rollbacks the app to the previous release
	cf cancel-deployment ${CF_APP}
	rm -f ${CF_MANIFEST_PATH}

.PHONY: cf-target
cf-target: check-env-vars
	@cf target -o ${CF_ORG} -s ${CF_SPACE}

.PHONY: cf-failwhale-deployed
cf-failwhale-deployed:
	@cf app notify-admin-failwhale --guid || (echo "notify-admin-failwhale is not deployed on ${CF_SPACE}" && exit 1)

.PHONY: enable-failwhale
enable-failwhale: cf-target cf-failwhale-deployed ## Enable the failwhale app and disable admin
	@cf map-route notify-admin-failwhale ${DNS_NAME} --hostname www
	@cf unmap-route notify-admin ${DNS_NAME} --hostname www
	@echo "Failwhale is enabled"

.PHONY: disable-failwhale
disable-failwhale: cf-target cf-failwhale-deployed ## Disable the failwhale app and enable admin
	@cf map-route notify-admin ${DNS_NAME} --hostname www
	@cf unmap-route notify-admin-failwhale ${DNS_NAME} --hostname www
	@echo "Failwhale is disabled"
