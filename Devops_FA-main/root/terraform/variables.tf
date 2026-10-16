variable "environment" {
  description = "Deployment environment name"
  type        = string

  validation {
    condition = contains(
      ["QA", "UAT", "PROD"],
      upper(var.environment)
    )

    error_message = "Environment must be QA, UAT or PROD."
  }
}

variable "container_prefix" {
  description = "Prefix for Docker resource names"
  type        = string
}

variable "frontend_port" {
  description = "Host port for frontend container"
  type        = number
}

variable "backend_port" {
  description = "Host port for backend container"
  type        = number
}

variable "app_version" {
  description = "Application version"
  type        = string
}

variable "log_level" {
  description = "Backend application log level"
  type        = string
}

variable "restart_policy" {
  description = "Docker container restart policy"
  type        = string
  default     = "unless-stopped"
}