# Lab 04: Migrazione PdM su Cluster K8s Multi-Nodo

## 🎯 Obiettivo del Laboratorio

Il test si focalizza sulla validazione di un’architettura a microservizi per la Manutenzione Predittiva (PdM) su un cluster **Minikube multi-nodo**.
L’idea di base è stata quella di prendere un’architettura PdM già esistente, sviluppata originariamente per girare su AWS e orchestrata tramite "docker compose" e riadattarla per testare un cluster K8s con più nodi su VM.

* **Repo di riferimento:** [https://github.com/AndreaProzzo21/Edge-Cloud-PdM-Pipeline]

---
## 📅 Log delle Attività

### Step 1: Analisi e Refactoring dei Microservizi

Prima di procedere con il deploy, è stata necessaria una fase di **refactoring e semplificazione**. Il codice originale, concepito per un'esecuzione locale o in ambiente controllato, presentava diverse logiche incompatibili con l'orchestrazione di Kubernetes.

La "pulizia" generale ha riguardato tre pilastri fondamentali:

* **Rimozione del Multithreading:** Nel codice originale, il simulatore gestiva più pompe contemporaneamente tramite thread Python. In un'architettura a microservizi scalabile, questa logica è controproducente. Ho rimosso i thread preferendo un approccio **1 Pod = 1 processo di simulazione flotta**. Questo permette a Kubernetes di gestire la scalabilità orizzontale (replicas) in modo molto più granulare ed efficiente.
* **No Local Storage:** Ho eliminato tutte le funzioni dedicate al salvataggio dei dati su file CSV locali. In Kubernetes, i Pod sono per natura volatili: scrivere dati su un disco locale senza un *Persistent Volume* significa perdere tutto al primo riavvio o rischedulazione. Ho preferito far "fluire" i dati esclusivamente via MQTT, rendendo i microservizi snelli e privi di stato.
* **Configurazione Esterna via Environment Variables:** Ho effettuato una bonifica totale degli indirizzi IP del broker, delle porte e dei topic. Questo è stato il passaggio chiave per poter utilizzare le **ConfigMap** di Kubernetes, permettendomi di cambiare il comportamento del sistema (es. passare da modalità "Stress" a "Nominal") senza dover mai ricompilare l'immagine Docker.

---

### Step 2: Preparazione dell'Infrastruttura (Host & Cluster)

In questa fase sono emersi i primi problemi tecnici "reali" legati alla gestione delle risorse hardware. Far girare un ambiente distribuito su una singola VM richiede una pianificazione oculata che inizialmente avevamo sottovalutato.

* **Reset e Pulizia:** Prima di partire, è stato necessario fare tabula rasa della sessione del laboratorio precedente. Abbiamo rimosso i vecchi residui per garantire che il nuovo setup multi-nodo non avesse conflitti di rete o di storage con i lavori passati.
* **Storage Out:** Il problema dello spazio si è presentato immediatamente, già nel tentativo di inizializzare Minikube con due nodi, segno che la partizione era al limite. Una volta risolto il blocco espandendo il disco fisico della VM (estendendo poi il *Volume Group* e il *Logical Volume* con il comando `lvextend`, e infine effettuato il resize del filesystem con `resize2fs`), abbiamo buildato l'immagine dell'Inference Service, che sfiorando 1GB (a causa di dipendenze pesanti come Scikit-Learn e Pandas) ha generato un warning di timeout durante il minikube image load. Nonostante l'allerta di lentezza di Docker, l'immagine è stata caricata con successo in tempi ragionevoli. Resta comunque un punto di attenzione per il futuro: l'immagine andrebbe decisamente alleggerita (ad esempio tramite multi-stage build) per evitare di stressare il demone Docker e ottimizzare i tempi di distribuzione nel cluster..
* **Bootstrap Multi-Nodo:** Solo dopo aver aumentato le specifiche della macchina e liberato spazio, siamo riusciti a lanciare Minikube in modalità distribuita:
`minikube start --nodes 2 --memory 3000 --cpus 2 --driver=docker`
Questo comando ha creato l'ambiente ideale per testare l'orchestrazione reale, con un nodo *Master* e un nodo *Worker* pronti a spartirsi il carico dei pod.

---

### Step 3: Organizzazione dei Manifest (IaC)

Per non fare confusione, ho diviso i file YAML in una struttura a cartelle dedicata. Ogni microservizio ha il suo "pacchetto" di configurazione e deploy:

* **`manifest/broker/`**: Contiene Mosquitto. È il fulcro della comunicazione.
* **`mainfest/simulator/`**: Qui risiede la flotta di sensori. Ho usato una ConfigMap per definire host, topic e diversi parametri della simulazione.
* **`mainfest/inference/`**: Qui c'è il "cervello" ML. Carica i modelli `.pkl` direttamente nell'immagine Docker per ora, per massimizzare la velocità di startup.

Certamente, ecco una versione sintetica ed efficace dello **Step 4**, strutturata come un flusso operativo rapido, ideale per un diario di bordo tecnico:

---

### Step 4: Build, Load & Deploy (Workflow Operativo)

In un'architettura multi-nodo, il passaggio critico è garantire che ogni nodo del cluster abbia accesso alle immagini. Ecco il ciclo di vita del deployment:

```bash
# 1. BUILD: Creazione immagini locali (Inference ~836MB, Simulator ~200MB)
# Nota: Uso del flag -f per puntare ai Dockerfile nelle sottocartelle
docker build -t pdm-simulator:v1 -f simulator/Dockerfile .
docker build -t pdm-inference:v1 -f inference/Dockerfile .

# 2. LOAD: Trasferimento immagini nel cluster (fondamentale per nodi Master/Worker)
# Nonostante il peso dell'inference e il warning di timeout, il caricamento è riuscito.
minikube image load pdm-simulator:v1
minikube image load pdm-inference:v1

# 3. APPLY: Orchestrazione dei manifest (Config -> Service -> Deployment)
kubectl apply -f manifest/broker/mosquitto-deploy.yml
kubectl apply -f manifest/inference/inf-config.yml
kubectl apply -f manifest/simulator/sim-config.yml
kubectl apply -f manifest/inference/inf-deploy.yml
kubectl apply -f manifest/simulator/sim-deploy.yml

# 4. VERIFY: Controllo distribuzione Pod sui nodi 'minikube' e 'minikube-m02'
kubectl get pods -o wide

```
---

### Step 5: Stress Test e Scalabilità

Ho testato la potenza dell'orchestrazione:

* **Scaling:** Ho portato i simulatori da 2 a 10 repliche con un solo comando.
* **Verifica:** Guardando i log di Mosquitto, ho visto "fisicamente" i nuovi pod connettersi da IP appartenenti a nodi diversi del cluster.
* **Rolling Update:** Ho cambiato la modalità di simulazione da `STRESS` a `NOMINAL` nella ConfigMap e ho lanciato un `rollout restart`. K8s ha sostituito i pod uno alla volta senza interrompere il flusso di dati verso l'AI.

---

## 📈 Stato Attuale e Osservazioni

Il sistema è attualmente operativo e stabile con un carico di **10 pod simulatori** (per un totale di 30 pompe monitorate simultaneamente). L'Inference Service sta dimostrando ottime capacità di processamento, gestendo migliaia di messaggi in tempo reale e notificando correttamente gli stati di `WARNING` e `FAULTY` tramite i log e il rilancio sui topic MQTT.

---

## 🚀 Prossimo Step: Persistence & Monitoring

Il sistema è ora in grado di "pensare", ma non ha ancora una "memoria" storica né un'interfaccia visuale. Il prossimo obiettivo del laboratorio sarà l'integrazione del **Monitoring Service**, che prevede:

1. **InfluxDB:** Introduzione di un database temporale (Time-Series Database) per archiviare lo storico della telemetria e delle predizioni del ML, evitando che i dati vadano persi al riavvio dei servizi.
2. **Grafana:** Creazione di una dashboard dinamica collegata a InfluxDB per visualizzare l'andamento della salute delle pompe, i trend delle vibrazioni e i contatori degli alert.

---

