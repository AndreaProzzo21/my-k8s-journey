# I Namespaces: Organizzare il Cluster

Immagina il tuo cluster Kubernetes come una grande città. Se tutti costruissero case ovunque senza regole, regnerebbe il caos. I **Namespaces** sono i "quartieri" della città: permettono di isolare gruppi di risorse all'interno dello stesso cluster fisico.

## Cos'è un Namespace?

Un Namespace è un **cluster virtuale** all'interno del cluster Kubernetes. Non è un isolamento fisico (i Pod possono girare sugli stessi nodi), ma un isolamento **logico**. Permette di dividere le risorse tra diversi utenti, progetti o ambienti (es. Sviluppo, Test, Produzione) evitando collisioni di nomi (puoi avere un Pod chiamato `api-server` in due namespace diversi).

## Perché usarli nel Digital Twin e IIoT?

In un contesto industriale, i Namespaces sono fondamentali per la segregazione dei domini:

* **Isolamento per Linea di Produzione:** `ns-linea-assemblaggio` vs `ns-linea-verniciatura`.
* **Isolamento per Funzione:** `ns-digital-twins` (modelli logici) vs `ns-edge-gateway` (comunicazione con i sensori).
* **Sicurezza:** Puoi dare i permessi di accesso (RBAC) a un manutentore solo per il namespace della sua area di competenza.

## I Namespaces di Default

Appena installato, K8s crea automaticamente alcuni "quartieri" predefiniti:

1. **`default`**: Il punto di atterraggio standard. Se non specifichi un namespace nel manifest, finisce qui.
2. **`kube-system`**: Il centro nevralgico. Qui risiedono i componenti del Control Plane (API Server, Scheduler) e i plugin di rete. **Regola d'oro: non deployare mai le tue app qui.**
3. **`kube-public`**: Contiene risorse che devono essere visibili a tutto il cluster senza autenticazione (usato raramente).
4. **`kube-node-lease`**: Contiene oggetti che monitorano l'heartbeat dei nodi per capire se sono ancora online.

## Gestione delle Risorse e Quote

Uno dei vantaggi principali dei Namespaces è la possibilità di limitare il "consumo" di ogni quartiere tramite le **ResourceQuotas**.

* Puoi decidere che il namespace `sviluppo` non può usare più di 4 core CPU in totale.
* Questo evita che un bug in un Digital Twin sperimentale mandi in crash l'intero cluster consumando tutte le risorse disponibili.

## Comandi Rapidi (Cheat Sheet)

### Esplorazione

```bash
# Elenca tutti i quartieri
kubectl get ns

# Elenca i Pod di un quartiere specifico
kubectl get pods -n <nome-namespace>

# Elenca TUTTI i Pod di TUTTI i namespace (utile per avere la panoramica totale)
kubectl get pods -A

```

### Creazione e Gestione

```bash
# Crea un namespace al volo (imperativo)
kubectl create ns produzione

# Crea un namespace tramite file (dichiarativo - consigliato per la tua repo)
# File: ns-twin.yaml
# kind: Namespace
# metadata:
#   name: digital-twin-lab
kubectl apply -f ns-twin.yaml

```

### Debug e Dettagli

```bash
# Guarda i dettagli (e le eventuali quote/limiti) di un namespace
kubectl describe ns <nome-namespace>

```

---

## Limitazioni Importanti

* **Isolamento di Rete:** Di default, un Pod nel namespace `A` può parlare con un Pod nel namespace `B`. Per impedirlo, servono le **NetworkPolicies** (argomento avanzato che vedremo più avanti).
* **Oggetti Globali:** Alcuni oggetti non appartengono ai namespace. Se fai `kubectl get nodes`, vedrai i nodi del cluster: i nodi sono risorse globali, così come i `PersistentVolumes` e i `CustomResourceDefinitions`.

---