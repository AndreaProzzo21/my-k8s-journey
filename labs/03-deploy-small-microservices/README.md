# 🧪 Lab 03: Deployment e Microservizi MQTT

## 🎯 Scopo del Laboratorio

L'obiettivo principale di questo laboratorio è stato l'applicazione pratica dei concetti di **Deployment** e **Service** in Kubernetes. Attraverso la creazione di un'architettura semplificata a microservizi, abbiamo esplorato come far comunicare diversi componenti nel cluster utilizzando un broker MQTT.

Sebbene i componenti siano script elementari senza persistenza su database, l'esercitazione ha permesso di comprendere le dinamiche di rete interna, la gestione delle configurazioni centralizzate e la resilienza del sistema.

---

## 🏗️ Step 1: Il Simulatore del Reparto (Sensor-Sim)

Il primo componente creato è un simulatore Python che genera dati fittizi di temperatura e vibrazioni, modellando una stazione di assemblaggio.

### Containerizzazione

Abbiamo isolato il simulatore in un'immagine Docker leggera.

```bash
# All'interno della cartella del sensore
eval $(minikube docker-env)
docker build -t factory-sensor:v1 .

```

### Configurazione e Deployment

Per evitare di cablare i parametri nel codice, abbiamo utilizzato una **ConfigMap** per gestire l'indirizzo del broker e i topic. Successivamente, abbiamo definito il **Deployment** per gestire le repliche dei sensori.

* **ConfigMap**: Definisce `MQTT_BROKER_HOST` e `MQTT_BASE_TOPIC`.
* **Deployment**: Inietta queste variabili nei container e definisce i limiti di risorse (CPU/RAM).

---

## 📡 Step 2: Il Broker MQTT e il Monitor

Per permettere la comunicazione, abbiamo introdotto il cuore dell'architettura: **Mosquitto MQTT**.

### Il Broker

Configurato come Deployment a replica singola e raggruppato sotto un **Service (ClusterIP)**, rendendolo raggiungibile dagli altri pod tramite il nome DNS interno `mqtt-broker`.

### Il Monitor (Subscriber)

Abbiamo sviluppato un secondo microservizio dedicato esclusivamente all'ascolto dei dati. Questo componente ci permette di validare in tempo reale che il flusso dei messaggi tra sensori e broker sia corretto.

```bash
# Build dell'immagine del monitor
docker build -t factory-monitor:v1 ./monitor

```

---

## 🚀 Step 3: Deployment Sequenziale

Per mettere in funzione l'intera infrastruttura, abbiamo seguito un ordine logico di applicazione dei manifest YAML:

1. **Inizializzazione configurazioni:**
```bash
kubectl apply -f 00-factory-configmap.yaml

```

2. **Lancio dell'infrastruttura di rete (Broker):**
```bash
kubectl apply -f 01-mosquitto-setup.yaml

```

3. **Lancio dei microservizi (Sensori e Monitor):**
```bash
kubectl apply -f 02-sensor-deploy.yaml
kubectl apply -f 03-monitor-deploy.yaml

```

---

## 🔍 Step 4: Test e Validazione del Sistema

Una volta che tutti i componenti sono passati in stato `Running`, abbiamo effettuato diversi controlli per testare la robustezza del cluster.

### 1. Analisi dei Log

Abbiamo verificato la corretta ricezione dei dati osservando i log del monitor:

```bash
kubectl logs -f -l app=factory-monitor

```

### 2. Scalabilità del Reparto

Abbiamo testato la scalabilità orizzontale aumentando il numero di sensori da 3 a 10:

```bash
kubectl scale deployment assembly-line-deploy --replicas=10

```

Il monitor ha iniziato a ricevere istantaneamente i flussi di dati dalle nuove repliche, confermando l'efficacia del Service DNS.

### 3. Test di Resilienza (Chaos Engineering)

Abbiamo simulato un crash critico eliminando il pod del broker:

```bash
kubectl delete pod -l app=mosquitto

```

**Risultato:** Il controller di Kubernetes ha ricreato il broker in modo **quasi istantaneo**. I sensori e il monitor, dopo un breve timeout di riconnessione, hanno ristabilito automaticamente il flusso dati (Self-healing). Le operazioni di scaling (passaggio a 10 repliche e ritorno a 0) hanno richiesto tempi leggermente superiori ma comunque accettabili, coerenti con la gestione delle risorse del cluster.

---

## 💡 Note Tecniche e Troubleshooting

### Gestione delle risorse (Resource Pressure)

Durante il laboratorio è stato riscontrato che l'ambiente di esecuzione (VM con **4096MB di RAM**) operava vicino al limite critico di saturazione del disco (**97% di utilizzo**).

* Questo stato ha probabilmente influenzato i tempi di risposta di Kubernetes, rendendo lo scheduling di nuovi Pod (specialmente durante lo scale-up a 10 repliche) più lento rispetto alle operazioni di ripristino di un singolo Pod esistente.

### Conflitto di Client ID e "Scale to Zero"

Un problema tecnico rilevante è emerso dopo il riavvio del broker: i client (monitor e sensori) tentavano di riconnettersi usando ID statici, causando disconnessioni a catena (flapping) sul broker MQTT.

* **Soluzione:** Abbiamo implementato la generazione di **ID dinamici** negli script Python.
* **Manovra di emergenza:** Per risolvere lo stato di stallo, è stata applicata la tecnica dello **"Scale to Zero"**, portando tutte le repliche a 0 per pulire le sessioni residue sul broker, per poi riavviare il monitor e infine i sensori in modo sequenziale.

---

