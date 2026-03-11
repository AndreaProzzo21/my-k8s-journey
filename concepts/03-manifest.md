# I Manifest in Kubernetes

In Kubernetes, non lavoriamo quasi mai con comandi diretti (approccio imperativo). Utilizziamo invece un **approccio dichiarativo**: scriviamo un file, chiamato **Manifest**, che descrive come vogliamo che sia il nostro sistema. Kubernetes si occuperà di far coincidere la realtà con quanto scritto nel file.

## 1. Cos'è un Manifest?

Un Manifest è un file in formato **YAML** che definisce un oggetto di Kubernetes (Pod, Service, Deployment, ecc.).

Ogni file manifest ha **quattro campi obbligatori** alla radice (Root level):

| Campo | Descrizione |
| --- | --- |
| `apiVersion` | La versione dell'API di Kubernetes che stiamo usando (es. `v1`, `apps/v1`). |
| `kind` | Il tipo di oggetto che vogliamo creare (es. `Pod`, `Service`, `Namespace`). |
| `metadata` | Dati che aiutano a identificare l'oggetto, come il `name`, i `namespace` e le `labels`. |
| `spec` | Il cuore del file: qui definiamo lo **stato desiderato** (es. quale immagine usare, quante risorse assegnare). |

---

## 2. Esempi Progressivi

### Livello 1: Il Pod Essenziale

Questo è il minimo indispensabile per far girare un container.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-server
  namespace: demo
  labels:
    app: frontend
spec:
  containers:
  - name: nginx-container
    image: nginx:1.25

```

* **Perché le Labels?** Le etichette (`labels`) sono fondamentali: serviranno in futuro ai *Service* per trovare i Pod corretti tra migliaia di altri.

---

### Livello 2: Configurazione e Variabili d'Ambiente
Un Pod spesso ha bisogno di informazioni esterne per funzionare (ad esempio, l'indirizzo di un database o una chiave API). Invece di scrivere queste info "dentro" il codice della tua app, le passiamo tramite il Manifest.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sensor-app
spec:
  containers:
  - name: collector
    image: my-sensor-app:v1
    env:                       # Passiamo variabili al container
    - name: LOG_LEVEL
      value: "DEBUG"
    - name: TARGET_URL
      value: "http://api.digitaltwin.local"
```

### Livello 3: Multi-Container (Sidecar Pattern)

In Kubernetes, un Pod può ospitare più di un container. Spesso si usa un container principale e uno di supporto (chiamato **Sidecar**), ad esempio per raccogliere i log o sincronizzare dati.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: complex-app
spec:
  containers:
  - name: main-app
    image: my-main-app:latest
    ports:
    - containerPort: 8080

  - name: log-exporter       # Container secondario (Sidecar)
    image: fluentd:latest
    resources:
      limits:
        memory: "50Mi"
        cpu: "100m"

```

---

## 3. Campi Chiave da ricordare

### Metadata

* **name:** Deve essere unico all'interno del namespace.
* **labels:** Coppie chiave-valore usate per raggruppare gli oggetti.

### Spec (Container)

* **image:** Il nome dell'immagine (solitamente da Docker Hub).
* **ports:** Specifica su quale porta il container è in ascolto (attenzione: questo ha un valore puramente informativo, non apre automaticamente la rete).
* **env:** Permette di passare variabili d'ambiente al container.

---

## 4. Comandi utili per i Manifest

* **Applicare un file:** `kubectl apply -f nomefile.yaml`
* **Vedere i dettagli (debug):** `kubectl describe pod nomepod`
* **Simulare l'applicazione (Dry Run):** `kubectl apply -f nomefile.yaml --dry-run=client` (utile per vedere se la sintassi è corretta senza creare nulla).

---

