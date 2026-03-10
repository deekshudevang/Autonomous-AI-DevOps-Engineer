terraform {
  required_version = ">= 1.5.0"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23.0"
    }
  }
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}

# ---------------------------------------------
# Core Namespaces
# ---------------------------------------------
resource "kubernetes_namespace" "aship_system" {
  metadata {
    name = "aship-system"
    labels = {
      "istio-injection" = "enabled" # mTLS enforcement
    }
  }
}

resource "kubernetes_namespace" "aship_sandbox" {
  metadata {
    name = "aship-sandbox"
    labels = {
      "purpose" = "ephemeral-testing"
    }
  }
}

# ---------------------------------------------
# RBAC: Zero Trust / Least Privilege Agent Role
# ---------------------------------------------
resource "kubernetes_role" "agent_role" {
  metadata {
    name      = "aship-agent-role"
    namespace = kubernetes_namespace.aship_system.metadata[0].name
  }

  rule {
    api_groups = ["", "apps", "extensions"]
    resources  = ["pods", "deployments", "replicasets"]
    verbs      = ["get", "list", "watch", "patch", "update"] # No 'delete' by default
  }
}

resource "kubernetes_role_binding" "agent_binding" {
  metadata {
    name      = "aship-agent-binding"
    namespace = kubernetes_namespace.aship_system.metadata[0].name
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.agent_role.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = "aship-agent-sa"
    namespace = kubernetes_namespace.aship_system.metadata[0].name
  }
}
