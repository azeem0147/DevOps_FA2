output "environment" {
  description = "Environment currently deployed"
  value       = upper(var.environment)
}

output "frontend_url" {
  description = "URL for opening the frontend application"
  value       = "http://localhost:${var.frontend_port}"
}

output "backend_url" {
  description = "URL for accessing the backend API"
  value       = "http://localhost:${var.backend_port}"
}

output "health_url" {
  description = "Backend health endpoint"
  value       = "http://localhost:${var.backend_port}/health"
}

output "frontend_container" {
  description = "Frontend Docker container name"
  value       = docker_container.frontend_container.name
}

output "backend_container" {
  description = "Backend Docker container name"
  value       = docker_container.backend_container.name
}

output "docker_network" {
  description = "Docker network used by the application"
  value       = docker_network.application_network.name
}

output "database_volume" {
  description = "Docker volume containing SQLite data"
  value       = docker_volume.database_data.name
}

output "application_version" {
  description = "Application version deployed"
  value       = var.app_version
}