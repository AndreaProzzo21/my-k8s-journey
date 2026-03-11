# Health Checks & Resource Management

In questo modulo approfondiamo come Kubernetes monitora la salute delle applicazioni e come possiamo assicurarci che ogni Pod abbia le risorse necessarie per operare senza disturbare il resto del cluster.

## 1. Le Probes: Il "Battito Cardiaco" dei Pod

Le Probe sono controlli periodici effettuati dalla Kubelet sul container. Esistono due tipi principali (più uno opzionale):

### 🟢 Readiness Probe (Sei pronto?)

Indica se il container è pronto a ricevere traffico.

* **Cosa succede:** Se la probe fallisce, il Pod viene rimosso dagli endpoint dei Service. Nessun utente verrà inviato a un Pod che sta ancora caricando dati o configurazioni.
* **Caso d'uso:** Un'app che impiega 30 secondi per connettersi al database all'avvio.

### 🔴 Liveness Probe (Sei vivo?)

Indica se il container è in uno stato di salute tale da poter continuare a girare.

* **Cosa succede:** Se la sonda fallisce, Kubernetes **uccide il container e lo riavvia** seguendo la sua *restartPolicy*.
* **Caso d'uso:** Un'app che va in "deadlock" (si blocca internamente ma il processo risulta ancora attivo).

### 🟡 Startup Probe (Ti stai accendendo?)

Usata per applicazioni molto lente ad avviarsi. Disabilita le altre due probes finché l'app non è partita, evitando che la *Liveness* uccida il container prima ancora che abbia finito il boot.

---

## 2. Meccanismi di Controllo

Kubernetes può controllare la salute in tre modi:

1. **HTTP GET:** Controlla se una pagina web risponde (es. `/healthz`).
2. **TCP Socket:** Controlla se una porta specifica è aperta.
3. **Exec Action:** Esegue un comando dentro il container (es. `cat /tmp/healthy`).

---

## 3. Manifest Completo: Risorse + Probes

Ecco un esempio di come appare un Manifest che integra sia il controllo delle risorse (visto in precedenza) che i controlli di salute.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: digital-twin-sensor
  labels:
    app: iot-collector
spec:
  containers:
  - name: sensor-app
    image: my-iot-app:v2
    
    # --- GESTIONE RISORSE ---
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"

    # --- CONTROLLI DI SALUTE ---
    # Controlla se l'app è pronta a ricevere dati, primo check dopo 2 secondi e successivi ogni 5
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 2
      periodSeconds: 5

    # Riavvia il container se non risponde per 3 volte consecutive
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 15
      periodSeconds: 10
      failureThreshold: 3

```

---

## Analisi Teorica: Perché usarli insieme?

L'unione di **Resource Control** e **Probes** crea un sistema resiliente:

1. **Prevenzione del Crash**: I `limits` impediscono a un bug di memoria di consumare tutto il nodo.
2. **Auto-ripristino**: Se il limite di memoria viene superato (OOM), il container crasha; la `livenessProbe` assicura che Kubernetes si accorga se l'app è "congelata" prima ancora di crashare.
3. **Zero Downtime**: La `readinessProbe` garantisce che un nuovo Pod non riceva traffico finché non è pronto al 100%, evitando errori 502/504 agli utenti o ai sensori IoT.

---
