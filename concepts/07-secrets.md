# Secrets: Gestione dei Dati Sensibili

I **Secret** sono oggetti di Kubernetes progettati per memorizzare e gestire informazioni riservate, come password, token OAuth, chiavi API o certificati SSL. L'obiettivo è separare queste informazioni sensibili dal codice e dai manifest, riducendo il rischio di esposizioni accidentali.

## 1. Il mito della sicurezza: Base64 vs Encryption

È importante chiarire subito un punto che spesso trae in inganno:

* **Default (Base64)**: Di default, i dati in un Secret sono codificati in **Base64**. Questa **non è crittografia**, è solo un modo per gestire dati binari o stringhe con caratteri speciali. Chiunque abbia accesso al cluster può fare un `echo "stringa-base64" | base64 --decode` e leggere la password.
* **Encryption at Rest**: Per rendere i Secret davvero sicuri, bisogna abilitare l'**Encryption at Rest** a livello di `etcd` (il database di Kubernetes). In scenari cloud (AWS, Azure, Google), questo è spesso gestito dal provider, ma in locale va configurato.

---

## 2. Tipi di Secret

Kubernetes offre diverse "specializzazioni":

1. **Opaque**: Il tipo generico (chiave-valore) per password e configurazioni custom.
2. **kubernetes.io/dockerconfigjson**: Per memorizzare le credenziali di accesso a un registro Docker privato (es. Docker Hub privato).
3. **kubernetes.io/tls**: Specifico per certificati HTTPS.

---

## 3. Utilizzo nel Manifest (L'esempio del DB)

Immaginiamo di voler lanciare un database MySQL. Non vogliamo scrivere `MYSQL_ROOT_PASSWORD: "admin123"` nel Pod, perché chiunque legga lo YAML vedrebbe la password.

### Step A: Definizione del Secret

Puoi crearlo via YAML (i valori devono essere in Base64) o più comodamente via comando:

```bash
kubectl create secret generic db-credentials --from-literal=password=SuperSegreta123

```

### Step B: Iniezione nel Pod

Ecco come il container SQL "pesca" la password dal Secret:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mysql-db
spec:
  containers:
  - name: mysql
    image: mysql:8.0
    env:
    - name: MYSQL_ROOT_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-credentials  # Nome del Secret
          key: password         # Chiave dentro il Secret

```

---

## 4. Secret come Volumi (Esempio: API Key per Cloud Monitoring)

Oltre alle variabili d'ambiente, i Secret possono essere montati come file reali. Questo metodo è preferibile quando l'applicazione si aspetta di leggere le credenziali da un file specifico o quando dobbiamo gestire certificati (`.pem`, `.crt`).

### Scenario: Autenticazione verso un Cloud Provider

Immaginiamo un microservizio che invia i dati del nostro Digital Twin a una piattaforma esterna. La piattaforma richiede un file `api_key.json` salvato in una cartella sicura.

**Step A: Definizione del Secret (via YAML)**
Per inserire file complessi o stringhe nel manifest, usiamo la codifica Base64.
*Esempio: la stringa "key-reparto-produzione-2026" diventa `a2V5LXJlcGFydG8tcHJvZHV6aW9uZS0yMDI2`.*

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cloud-api-key
type: Opaque
data:
  api_key.json: a2V5LXJlcGFydG8tcHJvZHV6aW9uZS0yMDI2

```

**Step B: Montaggio nel Pod**
In questo caso, Kubernetes crea un file `/etc/api/api_key.json` che esiste solo nella RAM del nodo (**tmpfs**), garantendo massima velocità e sicurezza.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: telemetry-sender
spec:
  containers:
  - name: collector
    image: python:3.9-slim
    volumeMounts:
    - name: secret-storage
      mountPath: "/etc/api"
      readOnly: true  # Protegge il segreto da modifiche accidentali dell'app
  volumes:
  - name: secret-storage
    secret:
      secretName: cloud-api-key

```

### Vantaggi di questo approccio

* **Sicurezza Fisica**: Poiché il file risiede in `tmpfs`, non viene mai scritto sul disco rigido (SSD/HDD) del nodo. Se il server viene spento, il segreto svanisce.
* **Flessibilità**: Molti software professionali (come i database o i broker MQTT con TLS) non accettano password via variabile d'ambiente per motivi di sicurezza, ma richiedono obbligatoriamente un file su disco.
* **Update a caldo**: Se modifichi il valore del Secret nel cluster, Kubernetes aggiornerà il file dentro il container senza dover riavviare il Pod (a differenza delle variabili d'ambiente).

---

## Analisi Teorica: Perché non usare sempre le ConfigMap?

Potresti chiederti: *"Perché complicarsi la vita se la sicurezza base è simile?"*

1. **Controllo degli accessi (RBAC)**: In un team, puoi permettere agli sviluppatori di vedere le ConfigMap ma vietare la lettura dei Secret.
2. **Prevenzione**: Evita che le password finiscano accidentalmente nei log o nei sistemi di versionamento (Git) sotto forma di testo chiaro.

---



