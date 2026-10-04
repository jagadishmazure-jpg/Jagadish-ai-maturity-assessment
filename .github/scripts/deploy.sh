#!/usr/bin/env bash
# Deployment steps used by .github/workflows/deploy.yml and teardown.yml. Each subcommand is
# idempotent and reads its inputs from the environment:
#   DEPLOY_TOOL   terraform | bicep
#   TARGET_ENV    dev | prod
#   LOCATION      Azure region (default eastus2)
#   JOB_IMAGE     image reference pushed by the image job
#   ARM_* / AZURE_*  set by azure/login (OIDC) and the workflow env
#
#   deploy.sh provision   create/update the plane, write rg/storage/job to $GITHUB_OUTPUT
#   deploy.sh smoke       check blob versioning, Key Vault RBAC and the job's schedule trigger
#   deploy.sh run-job     start one job execution and wait for it to succeed
#   deploy.sh destroy     tear the environment down (teardown workflow only)
set -euo pipefail

TOOL="${DEPLOY_TOOL:-terraform}"
ENV_NAME="${TARGET_ENV:?TARGET_ENV is required}"
LOCATION="${LOCATION:-eastus2}"
STACK="infra/terraform"
OUT="${GITHUB_OUTPUT:-/dev/stdout}"
IMAGE_ARGS=()

log() { echo "::group::$*"; }
end() { echo "::endgroup::"; }

tf_init() {
  : "${TFSTATE_RESOURCE_GROUP:?set repo/environment variable TFSTATE_RESOURCE_GROUP}"
  : "${TFSTATE_STORAGE_ACCOUNT:?set repo/environment variable TFSTATE_STORAGE_ACCOUNT}"
  terraform -chdir="$STACK" init -input=false \
    -backend-config="envs/${ENV_NAME}.backend.hcl" \
    -backend-config="resource_group_name=${TFSTATE_RESOURCE_GROUP}" \
    -backend-config="storage_account_name=${TFSTATE_STORAGE_ACCOUNT}" \
    -backend-config="container_name=${TFSTATE_CONTAINER:-tfstate}"
}

provision() {
  if [[ "$TOOL" == "terraform" ]]; then
    log "terraform apply ($ENV_NAME)"
    tf_init
    [[ -n "${JOB_IMAGE:-}" ]] && IMAGE_ARGS=(-var "job_image=${JOB_IMAGE}")
    terraform -chdir="$STACK" apply -auto-approve -input=false \
      -var-file="envs/${ENV_NAME}.tfvars" -var "location=${LOCATION}" "${IMAGE_ARGS[@]}"
    rg=$(terraform -chdir="$STACK" output -raw AZURE_RESOURCE_GROUP)
    st=$(terraform -chdir="$STACK" output -raw EVIDENCE_STORAGE_ACCOUNT)
    job=$(terraform -chdir="$STACK" output -raw ASSESSMENT_JOB_NAME)
    end
  else
    log "bicep: az deployment sub create ($ENV_NAME)"
    schedule="0 6 * * 1"
    [[ "$ENV_NAME" == "prod" ]] && schedule="0 5 1 * *"
    [[ -n "${JOB_IMAGE:-}" ]] && IMAGE_ARGS=(jobImage="${JOB_IMAGE}")
    outputs=$(az deployment sub create --name "aimaturity-${ENV_NAME}-${GITHUB_RUN_ID:-local}" \
      --location "$LOCATION" --template-file infra/bicep/main.bicep \
      --parameters environment="$ENV_NAME" location="$LOCATION" jobSchedule="$schedule" "${IMAGE_ARGS[@]}" \
      --query properties.outputs -o json)
    rg=$(jq -r .AZURE_RESOURCE_GROUP.value <<<"$outputs")
    st=$(jq -r .EVIDENCE_STORAGE_ACCOUNT.value <<<"$outputs")
    job=$(jq -r .ASSESSMENT_JOB_NAME.value <<<"$outputs")
    end
  fi
  { echo "resource_group=$rg"; echo "storage_account=$st"; echo "job_name=$job"; } >>"$OUT"
}

smoke() {
  : "${RESOURCE_GROUP:?}" "${STORAGE_ACCOUNT:?}"
  v=$(az storage account blob-service-properties show --account-name "$STORAGE_ACCOUNT" -g "$RESOURCE_GROUP" --query isVersioningEnabled -o tsv)
  [[ "$v" == "true" ]] || { echo "::error::evidence store versioning is off"; exit 1; }
  k=$(az keyvault list -g "$RESOURCE_GROUP" --query "[0].properties.enableRbacAuthorization" -o tsv)
  [[ "$k" == "true" ]] || { echo "::error::Key Vault must use RBAC"; exit 1; }
  t=$(az containerapp job list -g "$RESOURCE_GROUP" --query "[0].properties.configuration.triggerType" -o tsv)
  [[ "$t" == "Schedule" ]] || { echo "::error::assessment job missing or not schedule-triggered"; exit 1; }
  echo "smoke checks passed: versioned evidence store, RBAC Key Vault, scheduled job"
}

run_job() {
  : "${RESOURCE_GROUP:?}" "${JOB_NAME:?}"
  exec_name=$(az containerapp job start -g "$RESOURCE_GROUP" -n "$JOB_NAME" --query name -o tsv)
  for _ in $(seq 1 40); do
    status=$(az containerapp job execution show -g "$RESOURCE_GROUP" -n "$JOB_NAME" --job-execution-name "$exec_name" --query properties.status -o tsv)
    [[ "$status" == "Succeeded" ]] && { echo "job execution $exec_name succeeded"; return 0; }
    [[ "$status" == "Failed" ]] && { echo "::error::job execution $exec_name failed"; exit 1; }
    sleep 15
  done
  echo "::error::job execution $exec_name did not finish in time"; exit 1
}

destroy() {
  if [[ "$TOOL" == "terraform" ]]; then
    tf_init
    terraform -chdir="$STACK" destroy -auto-approve -input=false \
      -var-file="envs/${ENV_NAME}.tfvars" -var "location=${LOCATION}"
  else
    case "$LOCATION" in eastus2) short=eus2 ;; westus2) short=wus2 ;; westeurope) short=weu ;; *) exit 1 ;; esac
    az group delete --name "rg-aimaturity-${ENV_NAME}-${short}-001" --yes
  fi
}

case "${1:-}" in
  provision) provision ;;
  smoke) smoke ;;
  run-job) run_job ;;
  destroy) destroy ;;
  *) echo "usage: deploy.sh provision|smoke|run-job|destroy"; exit 2 ;;
esac
