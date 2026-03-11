# Lab 02: Python Sensor Simulator (FastAPI + Probes + Persistence)

In questo laboratorio ho implementato un simulatore di sensore IoT utilizzando **FastAPI**. L'obiettivo è testare l'integrazione tra logica applicativa, configurazione esterna e persistenza dei dati in Kubernetes.

## 🏗️ Architettura del Lab

Il Pod è composto da un container Python che espone due endpoint:

* `GET /health`: Utilizzato dalla **Liveness Probe** per monitorare lo stato del processo.
* `GET /data`: Genera un valore casuale, lo logga su un file e lo restituisce come JSON.

## 🛠️ Tecnologie utilizzate

* **Docker**: Per containerizzare l'app Python.
* **ConfigMap**: Per definire il nome del sensore (`SENSOR_NAME`) senza cablarlo nel codice.
* **Volumes (hostPath)**: Per mappare la cartella `/data` del container sul filesystem del nodo Minikube, garantendo che i log sopravvivano al riavvio del Pod.
* **Liveness Probe**: Controllo HTTP periodico sulla porta 8000.

## 🚀 Comandi eseguiti

```bash
# 1. Build dell'immagine nell'ambiente Minikube
eval $(minikube docker-env)
docker build -t my-python-sensor:v1 .

# 2. Deploy dei manifest
kubectl apply -f configmap_manifest.yml
kubectl apply -f pod_manifest.yml

# 3. Test dell'endpoint (Port Forwarding)
kubectl port-forward python-sensor 8000:8000
curl http://localhost:8000/data

```

## 📈 Risultati ottenuti

* I log di sistema mostrano le chiamate regolari della **Liveness Probe**.
* Il file `/data/sensor_readings.log` persiste all'interno del nodo Minikube (verificabile tramite `minikube ssh`).
* L'applicazione legge correttamente il nome del sensore dalla **ConfigMap**.

---

## ⚠️ Troubleshooting & Note Tecniche

Durante lo sviluppo sono emersi alcuni punti critici fondamentali per il funzionamento dell'ambiente su **Minikube**:

### 1. Il "Mondo" di Minikube vs Host VM

Utilizzando il driver Docker, Minikube gira all'interno di un container separato.

* **Il problema**: Il percorso `hostPath: /home/docker/sensor-data` definito nel manifest **non punta alla tua VM Ubuntu**, ma al filesystem interno del nodo Minikube.
* **La soluzione**: Per verificare i dati persistenti, è necessario entrare nel nodo con `minikube ssh` oppure utilizzare `minikube mount` per creare un ponte diretto tra la tua VM e il cluster.

### 2. Context Docker

Per buildare l'immagine e renderla disponibile a Kubernetes senza usare un Registry esterno (Docker Hub), è obbligatorio sincronizzare la shell con il demone Docker di Minikube tramite:
`eval $(minikube docker-env)`.
*Senza questo comando, Kubernetes restituirà l'errore `ErrImagePull` poiché cercherà l'immagine online.*

### 3. Sintassi `envFrom`

A differenza del campo `env` (usato per singole chiavi), `envFrom` richiede una struttura specifica. L'errore `strict decoding error: unknown field "name"` si risolve nidificando correttamente il riferimento alla risorsa:

```yaml
envFrom:
- configMapRef:
    name: sensor-config

```

---
