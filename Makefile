# Configuration
PROJECT_ID := $(shell gcloud config get-value project)
REGION := us-east1
SERVICE_NAME := bq-to-alloy-service
IMAGE_NAME := bq-to-alloy
SA_NAME := bq-to-alloy-sa
CONNECTOR_NAME := bq-to-alloy-connector
ARTIFACT_REGISTRY := $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(IMAGE_NAME)

.PHONY: all build deploy setup clean create-registry

all: setup build deploy

setup: 
# create-registry
	@echo "Creating service account..."
	gcloud iam service-accounts create $(SA_NAME) \
		--display-name="Service Account for BigQuery to AlloyDB transfer"
	
	@echo "Granting necessary permissions..."
	gcloud projects add-iam-policy-binding $(PROJECT_ID) \
		--member="serviceAccount:$(SA_NAME)@$(PROJECT_ID).iam.gserviceaccount.com" \
		--role="roles/bigquery.dataViewer"
	
	gcloud projects add-iam-policy-binding $(PROJECT_ID) \
		--member="serviceAccount:$(SA_NAME)@$(PROJECT_ID).iam.gserviceaccount.com" \
		--role="roles/alloydb.client"
	
	gcloud projects add-iam-policy-binding $(PROJECT_ID) \
		--member="serviceAccount:$(SA_NAME)@$(PROJECT_ID).iam.gserviceaccount.com" \
		--role="roles/secretmanager.secretAccessor"

create-registry:
	@echo "Creating Artifact Registry repository..."
	gcloud artifacts repositories create $(IMAGE_NAME) \
		--repository-format=docker \
		--location=$(REGION) \
		--description="Repository for BQ to AlloyDB transfer images"

create-secrets:
	@echo "Creating secrets..."
	yq r secrets.yaml database | gcloud secrets create alloydb-db-name --data-file=- || true
	yq r secrets.yaml username | gcloud secrets create alloydb-db-user --data-file=- || true
	yq r secrets.yaml password | gcloud secrets create alloydb-db-password --data-file=- || true

build:
	@echo "Building Docker image..."
	docker build -t $(IMAGE_NAME) .
	
	@echo "Tagging image..."
	docker tag $(IMAGE_NAME) $(ARTIFACT_REGISTRY)/$(IMAGE_NAME)
	
	@echo "Pushing to Artifact Registry..."
	docker push $(ARTIFACT_REGISTRY)/$(IMAGE_NAME)

deploy:
	@echo "Deploying to Cloud Run..."
	export PROJECT_ID=$(PROJECT_ID) && \
	export REGION=$(REGION) && \
	export CONNECTOR_NAME=$(CONNECTOR_NAME) && \
	export INSTANCE_CONNECTION_NAME=$(INSTANCE_CONNECTION_NAME) && \
	export IMAGE_NAME=$(IMAGE_NAME) && \
	envsubst < cloud-run-service.yaml > cloud-run-service-resolved.yaml && \
	gcloud run services replace cloud-run-service-resolved.yaml \
		--region $(REGION) && \
	rm cloud-run-service-resolved.yaml

clean:
	@echo "Cleaning up resources..."
	gcloud run services delete $(SERVICE_NAME) --region $(REGION) --quiet
	gcloud iam service-accounts delete $(SA_NAME)@$(PROJECT_ID).iam.gserviceaccount.com --quiet

logs:
	gcloud logs tail $(SERVICE_NAME)

# Helper commands
create-vpc-connector:
	# Google Cloud recommends 10.8.x.x/28 for Serverless VPC Access
	gcloud compute networks vpc-access connectors create $(CONNECTOR_NAME) \
		--network default \
		--region $(REGION) \
		--range 10.8.0.0/28 \
		--min-instances=2 \
		--max-instances=3 \
		--machine-type=e2-micro

delete-vpc-connector:
	gcloud compute networks vpc-access connectors delete $(CONNECTOR_NAME) \
		--region $(REGION)
