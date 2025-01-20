terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.8.0"
    }
  }
  backend "gcs" {
    bucket  = var.bucket_name
    prefix  = var.key_prefix
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

resource "google_compute_network" "vpc_network" {
  name = var.vpc_network_name
}

resource "google_compute_instance" "vm_instance" {
  name = var.vm_instance_name
  machine_type = var.machine_type
  tags = ["k8s", "sandbox"]

  boot_disk {
    initialize_params {
      image = var.machine_image
    }
  }

  network_interface {
    network = google_compute_network.vpc_network.name
    access_config {
      
    }
  }

  metadata = {
    ssh-keys = "ubuntu:${file(var.ssh_key_file_path)}"
    startup-script = file("userdata.tpl")
  }
}

resource "google_compute_firewall" "rules" {
  name        = "k8s-sandbox-firewall-rule"
  network     = google_compute_network.vpc_network.name
  description = "Creates firewall rule targeting tagged instances"

  allow {
    protocol  = "tcp"
    ports     = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags = ["k8s", "sandbox"]
}