terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

provider "docker" {}

resource "docker_container" "neo4j" {
  image = "neo4j:5"
  name  = "neo4j_tf"
  ports {
    internal = 7474
    external = 7474
  }
  ports {
    internal = 7687
    external = 7687
  }
}

resource "docker_container" "backend" {
  image = "riatalsania/ndtp-backend:latest"
  name  = "backend_tf"
  ports {
    internal = 8000
    external = 8001
  }
}