locals {
  short  = "aimaturity"
  region = { eastus2 = "eus2", westus2 = "wus2", westeurope = "weu" }[var.location]
  suffix = "${var.environment}-${local.region}-001"
  tags = merge({
    "env"         = var.environment
    "owner"       = "ai-governance-office"
    "app"         = "ai-maturity-assessment"
    "cost-center" = "CC-7200"
    "managed-by"  = "terraform"
  }, var.tags)
  # evidence: snapshots and questionnaires; reports: Markdown/HTML/SVG; audit: HITL audit logs
  evidence_containers = ["evidence", "reports", "audit"]
}
