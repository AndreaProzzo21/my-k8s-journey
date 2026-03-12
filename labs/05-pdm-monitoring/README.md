# Lab 05: Monitoring, Time-Series & Visualization

## 🎯 Obiettivo del Lab

In questa sessione evolviamo l'architettura base del lab precedente aggiungendo uno **stack di monitoraggio**. L'obiettivo è disaccoppiare la logica di business dalla persistenza dei dati, implementando un worker dedicato che funge da bridge tra il flusso dei messaggi (MQTT) e un database a serie temporali (InfluxDB), visualizzando infine il tutto su Grafana.

---

## 🏗️ Architettura del Servizio Monitoring

Il servizio `monitoring-worker` è stato progettato con una logica modulare e disaccoppiata per garantirne la manutenibilità:

* **MQTT Fetcher**: Gestisce la connessione al broker Mosquitto e la sottoscrizione ai topic delle predizioni (`factory/predictions/#`). È l'orecchio del sistema.
* **Core Manager**: Il cervello del servizio. Riceve i messaggi dal Fetcher, valida il JSON e coordina il passaggio dei dati verso il database.
* **Data Manager**: Gestisce l'interazione con InfluxDB 2.x, inclusa la gestione del token di autenticazione, l'organizzazione e il batching dei dati per ottimizzare le scritture.

---

## 🛠️ Configurazione dell'Infrastruttura Esterna

### 1. InfluxDB (Data Persistence)

Utilizziamo InfluxDB come database a serie temporali. È ideale per i dati PdM (Predictive Maintenance) perché permette query efficienti su trend storici.

**Punti chiave del Manifest:**

* Utilizzo di una `ConfigMap` per definire l'organizzazione (`pdm_org`) e il bucket (`pdm_data`).
* Esposizione tramite `Service` ClusterIP sulla porta `8086`.

### 2. Grafana (Dashboarding)

Il front-end del nostro sistema. Si collega a InfluxDB per trasformare i dati grezzi in dashboard.

**Punti chiave del Manifest:**

* Deployment leggero (`grafana-oss`).
* Esposizione via `NodePort` (porta `32000`) per l'accesso dall'host.

---

## ⚠️ Note su Sicurezza e Persistenza (Disclaimer)

Le configurazioni fornite in questo lab sono state semplificate per scopi didattici. In un ambiente di produzione reale, andrebbero implementati i seguenti miglioramenti:

* **Gestione dei Segreti**: I token di InfluxDB e le password di Grafana non dovrebbero essere in `ConfigMap` in chiaro, ma gestiti tramite **Kubernetes Secrets**.
* **Persistenza dei Dati**: I database (InfluxDB) e Grafana in questo lab usano lo storage temporaneo del Pod. Al riavvio del Pod, i dati andrebbero persi. In produzione è obbligatorio l'uso di **PersistentVolumes (PV)** e **PersistentVolumeClaims (PVC)**.
* **Network Policies**: L'accesso ai database dovrebbe essere ristretto solo ai servizi necessari tramite policy di rete specifiche.

L'obiettivo qui è la comprensione di un sistema IoT end-to-end funzionante, riducendo la complessità infrastrutturale.

---

## 📝 Manifests Kubernetes

### Il Servizio `monitoring-worker`

Il deployment del nostro worker personalizzato.

```yaml
# Estratto del Deploy
image: pdm-monitoring:v3
envFrom:
  - configMapRef:
      name: monitoring-config

```

> **Nota di Lab**: È fondamentale che l'immagine venga buildata con il contesto corretto (all'interno della cartella `/monitoring`) per garantire che i percorsi dei file Python siano corretti.

---

## 🚀 Guida all'Esecuzione

### Step 1: Build dell'immagine

```bash
cd monitoring
docker build -t pdm-monitoring:v3 .
minikube image load pdm-monitoring:v3

```

### Step 2: Deploy dell'Infrastruttura

```bash
kubectl apply -f manifest/influx-deploy.yaml
kubectl apply -f manifest/mon-config.yaml
kubectl apply -f manifest/mon-deploy.yaml
kubectl apply -f manifest/grafana-deploy.yaml

```

### Step 3: Troubleshooting Log

Per verificare che il bridge stia funzionando e scrivendo su InfluxDB:

```bash
kubectl logs -f deployment/monitoring-deployment

```

---

## ✅ Conclusioni

Al termine della sessione, abbiamo verificato il corretto funzionamento dell'intera pipeline: il worker processa i messaggi MQTT in tempo reale e popola correttamente il database a serie temporali. La creazione di dashboard dinamiche su Grafana ha certificato l'integrità del flusso dati, permettendo una visualizzazione chiara degli indici di salute delle pompe e la tempestiva rilevazione delle anomalie generate dal sistema di inferenza.