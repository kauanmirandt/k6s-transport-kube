#!/bin/bash
set -e
CLUSTER_NAME="k6s"
RECREATE=false

K8S_DIR="./k8s"
KIND_CONFIG=$K8S_DIR"/kind-config.yaml"

# parse arg
if [ "${1:-}" = "--recreate" ]; then
  RECREATE=true
fi

# deps quick check
for cmd in kind kubectl docker; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Erro: '$cmd' não encontrado. Instale-o e rode novamente." >&2
    exit 1
  fi
done

# recreate cluster if requested
if [ "$RECREATE" = true ]; then
  echo "Deletando cluster '${CLUSTER_NAME}' (se existir)..."
  kind delete cluster --name "$CLUSTER_NAME" || true
fi

# create cluster if not exists
if kind get clusters | grep -qx "$CLUSTER_NAME"; then
  echo "Cluster '${CLUSTER_NAME}' já existe. Pulando criação."
else
  echo "Criando cluster kind '${CLUSTER_NAME}'..."
  kind create cluster --name "$CLUSTER_NAME" --config "$KIND_CONFIG"
fi

# Aplicar manifests na ordem declarada no kustomization.yaml
kubectl apply -k k8s/

kubectl create secret generic telegraf-credentials \
  --from-literal=INFLUX_TOKEN='influxdbtoken' \
  --from-literal=ONOS_USERNAME='onos' \
  --from-literal=ONOS_PASSWORD='rocks' \
  -n telemetry

helm upgrade --install grafana grafana/grafana \
  -n monitoring \
  -f charts-values/grafana-values.yaml

kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode >> grafana-token.txt

helm upgrade --install influxdb influxdata/influxdb2 \
  -n database \
  -f charts-values/influxdb-values.yaml 

helm upgrade --install onos ./onos-transport-chart \
  -n transport-network \

kubectl get all -A -w