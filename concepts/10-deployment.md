# Deployment: Il Supervisore delle Applicazioni

Il **Deployment** è un oggetto di livello superiore che gestisce il ciclo di vita dei Pod. Non si occupa solo di farli partire, ma di garantire che restino vivi, di scalarli e di aggiornarli senza interruzioni. In Kubernetes, i Pod sono considerati effimeri: possono morire o essere distrutti in qualsiasi momento. Un deployment agisce come un supervisore che garantisce costantemente il mantenimento dello Stato Desiderato.

## 1. L'Architettura a "Cipolla": Deployment e ReplicaSet

Quando crei un Deployment, Kubernetes crea automaticamente un **ReplicaSet**.

* **ReplicaSet**: Ha un solo compito, assicurarsi che ci sia il numero esatto di Pod richiesti (es. "voglio 3 pod").
* **Deployment**: Gestisce i ReplicaSet. Quando aggiorni l'app, il Deployment crea un *nuovo* ReplicaSet e spegne gradualmente quello *vecchio* (**Rolling Update**).

---

## 2. Anatomia del Manifest (Le "Due Facce")

Il manifest di un Deployment sembra complesso perché contiene al suo interno il "modello" del Pod che deve creare.

```yaml
apiVersion: apps/v1        # Nota: api differente (apps/v1)
kind: Deployment
metadata:
  name: sensor-deployment  # Nome del Deployment
spec:
  replicas: 3              # QUANTI Pod vogliamo
  selector:
    matchLabels:
      app: iot-sensor      # QUALE etichetta deve monitorare
  
  template:                # --- IL MODELLO DEL POD ---
    metadata:
      labels:
        app: iot-sensor    # Deve corrispondere al selector sopra!
    spec:
      containers:
      - name: sensor
        image: my-python-sensor:v1

```

> **Perché due metadata/spec?**
> 1. Il primo blocco `metadata/spec` definisce le impostazioni del **Deployment** (quante repliche, quali selettori).
> 2. Il secondo blocco (sotto `template`) definisce come devono essere fatti i **Pod** che verranno generati.
> 
> 

---

## 3. Concetti Operativi Fondamentali

### A. Scaling (Scalabilità)

Puoi aumentare o diminuire la potenza del tuo reparto in un istante. Se il carico aumenta, passi da 3 a 10 sensori con un comando:

```bash
kubectl scale deployment sensor-deployment --replicas=10

```

### B. Rolling Update (Aggiornamento senza downtime)

Se vuoi cambiare l'immagine del sensore dalla `v1` alla `v2`:

1. Il Deployment crea un nuovo Pod `v2`.
2. Appena il `v2` è pronto (passa la Probe), spegne un `v1`.
3. Continua così finché tutti i Pod sono `v2`.

### C. Rollout & Rollback

Se la versione `v2` ha un bug, puoi tornare indietro istantaneamente:

```bash
# Controlla la cronologia delle versioni
kubectl rollout history deployment sensor-deployment

# Torna alla versione precedente
kubectl rollout undo deployment sensor-deployment

```

---

## 4. Comandi "Salva-Vita" da Terminale

| Comando | Descrizione |
| --- | --- |
| `kubectl get deploy` | Mostra lo stato dei Deployment e se le repliche sono pronte. |
| `kubectl describe deploy [nome]` | Fondamentale per vedere PERCHÉ un aggiornamento è bloccato. |
| `kubectl edit deploy [nome]` | Apre lo YAML "al volo" per cambiare repliche o immagini. |
| `kubectl rollout status deploy [nome]` | Monitora in tempo reale l'andamento di un aggiornamento. |

---

## Analisi Teorica: Il "Self-Healing"

La caratteristica più potente è l'**auto-riparazione**. Se un nodo della tua VM crasha e si porta via i Pod, il Deployment si accorge che il numero di Pod con l'etichetta `app: iot-sensor` è sceso a zero.
Immediatamente, ne ordina la creazione di nuovi su un nodo sano per riportare il conteggio a 3. **Tu non devi fare nulla.**

---

