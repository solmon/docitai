# Kubernetes Deployment Manifests for Tenant Management Service
# -----------------------------------------------------------------
# These manifests provide a production-ready deployment configuration
# for the Tenant Management Service on Kubernetes.
#
# Prerequisites:
# - Kubernetes cluster (1.25+)
# - kubectl configured
# - Container registry access (update image references)
# - PostgreSQL database (external or in-cluster)
#
# Usage:
# 1. Update secrets in secret.yaml (use base64 encoding)
# 2. Update ConfigMap values in configmap.yaml
# 3. Update image reference in deployment.yaml
# 4. Apply manifests:
#    kubectl apply -f namespace.yaml
#    kubectl apply -f configmap.yaml
#    kubectl apply -f secret.yaml
#    kubectl apply -f deployment.yaml
#    kubectl apply -f service.yaml
#    kubectl apply -f hpa.yaml
#    kubectl apply -f ingress.yaml
#
# Or apply all at once:
#    kubectl apply -f .

# Directory Structure:
# k8s/
# ├── README.md           # This file
# ├── namespace.yaml      # Namespace definition
# ├── configmap.yaml      # Application configuration
# ├── secret.yaml         # Sensitive configuration (secrets)
# ├── deployment.yaml     # Deployment specification
# ├── service.yaml        # Service definition
# ├── hpa.yaml            # Horizontal Pod Autoscaler
# └── ingress.yaml        # Ingress configuration

# Environment-specific configurations can be managed using:
# - Kustomize overlays (recommended)
# - Helm values files
# - ArgoCD ApplicationSets
