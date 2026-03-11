# Persistent Volumes (PV) e Claims (PVC): La Persistenza dei Dati

In Kubernetes, i container sono per definizione **effimeri**: se un Pod viene rimosso, tutti i dati salvati al suo interno vengono persi. Per gestire dati che devono sopravvivere al ciclo di vita dei Pod (come log industriali, database o configurazioni del broker MQTT), Kubernetes utilizza un sistema di astrazione dello storage.

## 1. Il Sistema a due livelli: PV e PVC

Kubernetes separa la fornitura dell'hardware dalla richiesta dell'applicazione:

* **Persistent Volume (PV)**: È la risorsa fisica (un disco SSD, una cartella su un NAS, uno storage cloud). È un oggetto del cluster che esiste indipendentemente dai Pod.
* **Persistent Volume Claim (PVC)**: È la richiesta di storage da parte di un utente. È come un "ticket" che dice: *"Ho bisogno di 1GB di spazio con permessi di scrittura"*.

**Analogie**: Se il **PV** è la "casa" (l'asset fisico), la **PVC** è il "contratto di affitto" (il diritto di usare quella casa).

---

## 2. Modalità di Accesso (Access Modes)

Ogni volume deve definire come i Pod possono interagire con esso:

1. **ReadWriteOnce (RWO)**: Il volume può essere montato in lettura/scrittura da **un solo nodo** alla volta. (Ideale per Database).
2. **ReadOnlyMany (ROX)**: Il volume può essere letto da **molti nodi** contemporaneamente. (Ideale per file di configurazione condivisi).
3. **ReadWriteMany (RWX)**: Il volume può essere letto/scritto da **molti nodi** contemporaneamente. (Richiede storage di rete come NFS).

---

## 3. Esempio Pratico: Configurare lo Storage

### Step 1: Definizione del volume fisico (Persistent Volume)

In Minikube, possiamo simulare un PV usando una cartella del nodo.

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: sensor-pv
spec:
  capacity:
    storage: 1Gi              # Dimensione del disco
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: "/mnt/data"         # Percorso reale sul nodo

```

### Step 2: La richiesta dell'app (Persistent Volume Claim)

L'applicazione non punta direttamente al PV, ma "emette" un claim. Kubernetes cercherà un PV che soddisfi questi requisiti.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: sensor-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Mi          # Chiedo 500MB (pescherà dal PV da 1GB)

```

### Step 3: Utilizzo nel Pod

Il Pod monta la **PVC**, non il PV.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sensor-pod
spec:
  containers:
  - name: sensor-app
    image: my-python-sensor:v1
    volumeMounts:
    - name: data-storage
      mountPath: /data        # Cartella interna al container
  volumes:
  - name: data-storage
    persistentVolumeClaim:
      claimName: sensor-pvc   # Si collega alla richiesta fatta sopra

```

---

## 4. Lifecycle e Reclaim Policy

Cosa succede ai dati sul disco quando cancelliamo la PVC? Questo è definito dalla **Reclaim Policy** nel PV:

* **Retain**: Il volume (PV) resta nel cluster ma è segnato come "Released". I dati sono ancora lì, ma il PV non è riutilizzabile finché l'admin non interviene manualmente. (Massima sicurezza).
* **Delete**: Il volume fisico viene rimosso non appena la PVC viene cancellata. (Tipico dei sistemi Cloud per risparmiare costi).

---

## Perché è meglio di `hostPath`?

1. **Astrazione**: Lo sviluppatore non ha bisogno di sapere *dove* o *cos'è* il disco fisico. Chiede solo "spazio" tramite la PVC.
2. **Portabilità**: Se sposti la tua app da Minikube a AWS, non devi cambiare il Pod. Cambierai solo il PV, ma la PVC resterà la stessa.
3. **Sicurezza**: Impedisce al Pod di avere accesso a tutto il filesystem dell'host, limitandolo solo allo spazio assegnato.

---

