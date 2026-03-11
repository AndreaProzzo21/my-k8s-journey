# Data Persistence & Configuration Management

In un ecosistema a container, tutto è progettato per essere effimero: se un container muore, il suo file system viene resettato. Per applicazioni reali (come un database o un digital twin che deve storicizzare dati), abbiamo bisogno di due strumenti chiave: **Volumi** e **ConfigMaps**.

## 1. I Volumi: Dare una memoria ai Pod

Un **Volume** in Kubernetes (e similarmente in Docker) è essenzialmente una directory accessibile ai container all'interno di un Pod. Serve a garantire che i dati sopravvivano ai crash dei container o siano condivisibili tra container diversi nello stesso Pod.

### Tipologie principali (Astrazioni)

1. **emptyDir**: Una cartella vuota creata nel momento in cui il Pod viene assegnato a un nodo. Vive finché il Pod resta vivo. Ottima per cache o file temporanei.
2. **hostPath**: Monta una directory del file system del nodo ospite (la tua VM Ubuntu) direttamente nel Pod. Utile per test locali o per accedere ai log di sistema.
3. **PersistentVolume (PV) & Claim (PVC)**: La soluzione professionale. Astrae lo storage fisico (disco cloud, NAS, ecc.) permettendo al Pod di richiedere spazio senza sapere "dove" sia fisicamente.

### Il meccanismo: Volume vs VolumeMount

Per usare un volume, Kubernetes richiede sempre due passaggi nel Manifest, che funzionano come un "ponte":

1. **`spec.volumes` (Dichiarazione)**: Definisce *quale* storage usare e gli dà un nome (es. "presa elettrica"). È a livello di Pod.
2. **`spec.containers.volumeMounts` (Montaggio)**: Definisce *dove* quel volume deve apparire dentro il file system del container (es. "collego il cavo"). È a livello di singolo container.

---

### Sotto-sezione sulla Persistenza Professionale:

### L'astrazione PV e PVC (Il contratto di affitto)

Se i volumi `hostPath` o `emptyDir` sono legati al ciclo di vita del nodo o del pod, per i database e i dati storici degli asset industriali si usa il sistema **PV/PVC**:

* **PersistentVolume (PV)**: È la risorsa fisica (es. un disco da 50GB creato dall'amministratore).
* **PersistentVolumeClaim (PVC)**: È la richiesta dell'utente ("Mi servono 10GB con permessi di scrittura").
* **StorageClass**: È l'automatismo che crea il disco appena lo richiedi (molto usato in Cloud o con Minikube).

**Perché usarlo?** Se il Pod si sposta su un altro server (nodo), Kubernetes scollega il disco dal vecchio server e lo riattacca al nuovo. I tuoi dati "viaggiano" con l'app.

> 💡 **Tip:** Poiché i Volumi sono definiti a livello di **Pod**, due container nello stesso Pod possono montare lo **stesso volume** (anche in cartelle diverse). Questo è il modo più veloce per far comunicare due processi (es. uno scrive un file di log, l'altro lo legge e lo invia a una dashboard).

---

## 2. ConfigMap: Separare il Codice dalla Configurazione

In Kubernetes, una **ConfigMap** è l'oggetto dedicato a separare i dati di configurazione dall'immagine del container. Questo permette di mantenere le applicazioni "agnostiche" rispetto all'ambiente in cui girano.

## Il problema dell'Hard-coding

Senza le ConfigMap, saresti costretto a:

1. Inserire file di configurazione dentro l'immagine Docker.
2. Ricreare l'immagine ogni volta che un parametro (es. un indirizzo IP o una porta) cambia.
3. Gestire decine di immagini diverse per scenari diversi.

**La soluzione di Kubernetes:** Iniettare la configurazione a "runtime" (durante l'avvio del container).

---

## Come si inietta la configurazione?

Esistono tre modi principali per passare i dati di una ConfigMap a un Pod:

### A. Variabili d'Ambiente (Singole)

Ideale per singoli parametri come nomi di database o livelli di log.

```yaml
env:
  - name: SENSOR_ID
    valueFrom:
      configMapKeyRef:
        name: iot-config
        key: sensor_id

```

### B. Variabili d'Ambiente (In blocco)

Utile per importare decine di parametri in un colpo solo. Tutti i dati della ConfigMap diventano variabili d'ambiente nel container.

```yaml
envFrom:
  - configMapRef:
      name: full-app-config

```

### C. File in un Volume (Config Injection)

Questo è il metodo più potente. Kubernetes crea dei file reali all'interno di una cartella nel container. Ogni "chiave" della ConfigMap diventa un nome file, e il "valore" diventa il contenuto del file.

* **Caso d'uso:** File di configurazione complessi (es. `nginx.conf`, `settings.json`, `prometheus.yml`).

---

## Anatomia di una ConfigMap (Esempio pratico)

Ecco come appare un file manifest per una ConfigMap che gestisce un servizio di monitoraggio per Digital Twin:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: digital-twin-settings
data:
  # Coppie chiave-valore semplici
  sampling_rate: "5s"
  mqtt_broker_url: "tcp://broker.local:1883"
  
  # Interi file di configurazione
  ui_settings.json: |
    {
      "theme": "dark",
      "refreshInterval": 5000,
      "showDebug": true
    }

```

---

## Aggiornamenti "a caldo" (Hot Reload)

Una caratteristica avanzata delle ConfigMap montate come **volumi** è che se modifichi la ConfigMap nel cluster (`kubectl edit configmap...`), Kubernetes aggiornerà automaticamente i file all'interno del container (dopo un breve ritardo).

*Nota: Se invece usi le variabili d'ambiente, dovrai riavviare il Pod per leggere i nuovi valori.*

---

## Analisi Teorica: Sicurezza e Best Practices

* **ConfigMap vs Secrets:** Le ConfigMap **non sono criptate**. Sono pensate per dati pubblici (porte, URL, nomi). Per password, chiavi API o certificati, Kubernetes mette a disposizione un oggetto simile chiamato **Secret**.
* **Immutabilità:** Nelle versioni recenti di K8s, puoi segnare una ConfigMap come `immutable: true`. Questo impedisce modifiche accidentali e migliora le performance del cluster.

---

### 3. Utilizzo nel Pod (tramite Volumi e Env)

In questo esempio, usiamo sia un volume (per i dati persistenti) sia la ConfigMap (per le impostazioni).

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: backend-app
spec:
  containers:
  - name: server
    image: my-app:v1
    # 1. Iniettiamo la ConfigMap come variabili d'ambiente
    envFrom:
    - configMapRef:
        name: app-config
    
    # 2. Montiamo un volume per i dati persistenti
    volumeMounts:
    - name: storage-volume
      mountPath: /data/db  # Cartella interna al container
      
  volumes:
  - name: storage-volume
    hostPath:
      path: /mnt/data      # Cartella fisica sulla nostra VM

```
---




