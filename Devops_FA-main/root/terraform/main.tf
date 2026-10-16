locals {
  network_name = (
    "${var.container_prefix}-campus-event-network"
  )

  volume_name = (
    "${var.container_prefix}-campus-event-data"
  )

  backend_container_name = (
    "${var.container_prefix}-campus-event-backend"
  )

  frontend_container_name = (
    "${var.container_prefix}-campus-event-frontend"
  )

  backend_image_name  = "campus-event-backend:${lower(var.environment)}"
  frontend_image_name = "campus-event-frontend:${lower(var.environment)}"
}

resource "docker_network" "application_network" {
  name = local.network_name
}


resource "docker_volume" "database_data" {
  name = local.volume_name
}


resource "docker_image" "backend_image" {
  name = local.backend_image_name

  build {
    context    = "${path.module}/../docker/backend"
    dockerfile = "Dockerfile"
  }

  keep_locally = true
}


resource "docker_image" "frontend_image" {
  name = local.frontend_image_name

  build {
    context    = "${path.module}/../docker/frontend"
    dockerfile = "Dockerfile"
  }

  keep_locally = true
}


resource "docker_container" "backend_container" {
  name  = local.backend_container_name
  image = docker_image.backend_image.image_id

  restart = var.restart_policy

  env = [
    "APP_NAME=Campus Event Management System",
    "APP_ENV=${upper(var.environment)}",
    "APP_VERSION=${var.app_version}",
    "LOG_LEVEL=${var.log_level}",
    "DATABASE_PATH=/app/data/campus_events.db"
  ]

  ports {
    internal = 5000
    external = var.backend_port
  }

  volumes {
    volume_name    = docker_volume.database_data.name
    container_path = "/app/data"
  }

  networks_advanced {
    name = docker_network.application_network.name

    aliases = [
      "backend"
    ]
  }
}


resource "docker_container" "frontend_container" {
  name  = local.frontend_container_name
  image = docker_image.frontend_image.image_id

  restart = var.restart_policy

  ports {
    internal = 80
    external = var.frontend_port
  }

  networks_advanced {
    name = docker_network.application_network.name
  }

  depends_on = [
    docker_container.backend_container
  ]
}