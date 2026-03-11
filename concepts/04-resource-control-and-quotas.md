# Resource Control: Requests e Limits

In Kubernetes, la gestione delle risorse non è opzionale se si vuole un cluster stabile. Poiché i Pod condividono i nodi fisici, dobbiamo stabilire delle regole per evitare che un processo consumi tutta la CPU o la RAM disponibile, affamando gli altri (**Noisy Neighbor problem**).

Le risorse principali che gestiamo sono **CPU** (misurata in millicore) e **Memory** (misurata in Byte/MiB).

## 1. Requests (Il Minimo Garantito)

La `request` è la quantità di risorse che Kubernetes **garantisce** al Pod.

* **Cosa succede:** Lo Scheduler guarda questo valore per decidere su quale nodo piazzare il Pod. Se un nodo ha solo 200MB di RAM libera e il tuo Pod ne richiede 300MB, lo Scheduler non lo metterà lì.
* **Metafora:** È come prenotare un tavolo al ristorante. Anche se non hai ancora iniziato a mangiare, quel posto è riservato per te.

## 2. Limits (Il Tetto Massimo)

Il `limit` è la quantità massima di risorse che il Pod può consumare.

* **Cosa succede:** Impedisce al Pod di andare "fuori giri".
* **Gestione del superamento:**
* **CPU:** Se il Pod cerca di usare più CPU del limite, Kubernetes lo **rallenta** (throttling), ma non lo uccide.
* **Memory:** Se il Pod cerca di usare più RAM del limite, Kubernetes lo **uccide** immediatamente con un errore di **OOMKilled** (Out Of Memory Killed). La RAM non può essere "rallentata" come la CPU.



## Esempio di Manifest YAML

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: digital-twin-engine
  namespace: demo
spec:
  containers:
  - name: simulation-container
    image: my-twin-image:latest
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"    # 250 millicore (1/4 di una CPU)
      limits:
        memory: "128Mi"
        cpu: "500m"    # 500 millicore (1/2 CPU)

```

## 3. Resource Quotas (A livello di Namespace)

Mentre Requests e Limits lavorano sui singoli Pod, le **ResourceQuotas** lavorano sul "quartiere" (Namespace).

* Puoi definire che il namespace `sviluppo` non può superare in totale 4 CPU e 8GiB di RAM.
* Se provi a creare un Pod che farebbe sforare questo totale, l'API Server rifiuterà la richiesta.

---

## Perché i Resource Control sono vitali? (Oltre i Digital Twin)

Configurare `requests` e `limits` non serve solo a far girare bene una singola applicazione, ma è una strategia di **sopravvivenza del cluster**. Ecco perché sono fondamentali in ogni scenario industriale e di produzione:

### 1. Prevedibilità e "Capacity Planning"

Senza le `requests`, lo Scheduler di Kubernetes lavora alla cieca.

* **Nel Digital Twin:** Sai esattamente quanti "gemelli" puoi ospitare (Risorse Totali / Requests).
* **In Generale:** Eviti il fenomeno del **Bin Packing** inefficiente. Se dichiari ciò che ti serve, Kubernetes può distribuire i carichi in modo intelligente, evitando che un nodo sia sovraccarico mentre un altro è vuoto.

### 2. Protezione dal "Noisy Neighbor" (Vicinato Rumoroso)

In un cluster condiviso, un Pod senza limiti è un pericolo per tutti gli altri.

* **Safety:** Se un algoritmo di simulazione o un processo va in loop infinito, il `limit` sulla CPU impedisce a quel Pod di "rubare" cicli di calcolo agli altri.
* **Business Continuity:** Grazie ai limiti, un errore nel codice di un microservizio secondario non potrà mai far crashare i servizi critici (come i sensori IoT o i database) che girano sullo stesso nodo.

### 3. Stabilità del Nodo (Prevenzione dell'OOMKilled)

La RAM è una risorsa "non comprimibile": se finisce, il sistema deve uccidere qualcosa.

* **Affidabilità:** Impostando i `limits` di memoria, Kubernetes ucciderà il singolo Pod che sta esagerando (**OOMKill**) *prima* che la memoria del nodo si esaurisca completamente, salvaguardando la stabilità del sistema operativo e di Kubernetes stesso.

### 4. Ottimizzazione dei Costi (FinOps)

In ambienti Cloud (AWS, Azure, Google Cloud), le risorse costano.

* **Cost Control:** Definire correttamente le risorse permette di utilizzare istanze più piccole o di sfruttare l'**Horizontal Pod Autoscaler**. Se i tuoi Pod dichiarano con precisione cosa consumano, il cluster può scalare verso il basso quando non c'è carico, facendoti risparmiare sui costi dell'infrastruttura.

> **In sintesi:** I Resource Control trasformano un cluster da un insieme caotico di container a un'orchestra orchestrata, dove ogni componente ha il suo spazio garantito e non può danneggiare gli altri.

---
