variable "environment" {
  description = "dev or prod"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment must be dev or prod"
  }
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus2"
  validation {
    condition     = contains(["eastus2", "westus2", "westeurope"], var.location)
    error_message = "location must be eastus2, westus2 or westeurope"
  }
}

variable "log_retention_days" {
  description = "Log Analytics retention (30 is the free-retention minimum)"
  type        = number
  default     = 30
}

variable "log_daily_quota_gb" {
  description = "Daily ingestion cap for Log Analytics, so a logging bug cannot run up a bill"
  type        = number
  default     = 0.5
}

variable "job_image" {
  description = "Container image the scheduled assessment job runs (built by deploy.yml)"
  type        = string
  default     = "ghcr.io/jagadishmazure-jpg/ai-maturity-assessment:0.1.0"
}

variable "job_schedule" {
  description = "Cron expression (UTC) for the scheduled re-assessment"
  type        = string
  default     = "0 6 * * 1"
}

variable "job_enabled" {
  description = "Create the scheduled job; dev can switch it off and run assessments on demand"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Extra tags merged into the required ones"
  type        = map(string)
  default     = {}
}
