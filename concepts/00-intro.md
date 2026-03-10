# Introduzione a Kubernetes e Architettura del Cluster

## Perché Kubernetes (K8s)?

Passare da singoli container Docker a un sistema di produzione complesso introduce sfide di **scalabilità** e **resilienza**:

* **Limiti di Risorsa:** Una singola macchina (VM o Server) non può scalare all'infinito per limiti fisici di CPU/RAM.
* **Effimerità:** I container non sono "animali domestici" (pets), ma "bestiame" (cattle). Se uno muore, deve essere rimpiazzato istantaneamente senza intervento umano.
* **Orchestrazione:** Serve un sistema intelligente che gestisca il traffico, lo storage e il deployment su un parco macchine eterogeneo.

## Il concetto di "Desired State" (Stato Desiderato)

A differenza di Docker Compose, dove spesso impartiamo comandi imperativi ("fai questo"), K8s lavora in modalità **Dichiarativa**:

1. Noi definiamo lo **Stato Desiderato** in un file YAML (es: "Voglio 3 repliche del Digital Twin").
2. Kubernetes monitora costantemente lo **Stato Attuale**.
3. Se i due stati non coincidono (es: un Pod crasha e ne restano 2), K8s agisce per riportare il sistema allo stato desiderato. Questo ciclo è chiamato **Control Loop**.

## Concetti Chiave

* **Pod:** L'unità minima di deployment. È un "guscio" che ospita uno o più container. I container nello stesso Pod condividono lo stesso indirizzo IP (`localhost`) e possono scambiarsi file tramite volumi comuni.
* **Node:** Una macchina (virtuale o fisica) che mette a disposizione le proprie risorse al cluster.
* **Cluster:** L'insieme del "cervello" (Control Plane) e dei "muscoli" (Worker Nodes).

## Anatomia del Cluster

Un cluster K8s è diviso in due tipologie di nodi:

### 1. Controller Node (Control Plane)

È il centro di comando del cluster. Gestisce la logica decisionale e risponde agli eventi.

* **API Server:** L'unico componente con cui parliamo direttamente. È il "centralino" che riceve le richieste REST e le smista agli altri componenti.
* **etcd:** Un database key-value distribuito ad alta disponibilità. Memorizza l'intera configurazione del cluster. Se perdi etcd, perdi il cluster.
* **Scheduler:** Il "logistico". Guarda i requisiti del tuo Pod (quanta RAM serve?) e trova il nodo più scarico che può ospitarlo.
* **Controller Manager:** Include diversi controller (Node Controller, Replication Controller). È il responsabile del mantenimento del *Desired State*.
* **Cloud Controller Manager:** (Opzionale) Gestisce l'interazione con infrastrutture cloud (AWS, Azure, GCP) per bilanciatori di carico o storage.

### 2. Worker Node

Sono le macchine che eseguono effettivamente il carico di lavoro (i tuoi Pod).

* **Kubelet:** L'agente di bordo. Riceve gli ordini dall'API Server e si assicura che i container nel Pod siano sani (Healthy). Esegue i "Health Checks".
* **Container Runtime:** Il motore che avvia i container. Kubernetes oggi supporta diversi runtime tramite l'interfaccia CRI (Container Runtime Interface), come `containerd` o `CRI-O`.
* **Kube-proxy:** Il "vigile urbano" della rete. Gestisce le regole di networking (IP tables/IPVS) per far sì che ogni Pod possa parlare con gli altri, indipendentemente dal nodo in cui si trovano.

---

### La Gerarchia delle Astrazioni: Da Docker a Kubernetes

#### Livello 1: Il Container (L'Unità Esecutiva)

* **Tecnologia:** Docker / Containerd.
* **Cos'è:** Un pacchetto isolato che contiene il tuo codice, le librerie e le dipendenze.
* **Astrazione:** Astrae il **Software dal Sistema Operativo**. Non ti interessa più se il server ha Ubuntu o CentOS, il container girerà ovunque ci sia un "motore" (runtime).

#### Livello 2: Il Pod (L'Unità Atomica di K8s)

* **Tecnologia:** Kubernetes Object (`Kind: Pod`).
* **Cos'è:** Un "guscio" che avvolge uno o più container.
* **Astrazione:** Astrae la **Rete e lo Storage dai Container**. I container dentro un Pod condividono lo stesso indirizzo IP (`localhost`). Se hai un'app che scrive log e un altro processo che li invia a un database, mettendoli nello stesso Pod si vedono come se fossero sulla stessa macchina, anche se sono container separati.

#### Livello 3: Il Deployment (L'Astrazione del Ciclo di Vita)

* **Tecnologia:** Kubernetes Object (`Kind: Deployment`).
* **Cos'è:** Un manager che controlla i Pod.
* **Astrazione:** Astrae la **Disponibilità e l'Aggiornamento**. Qui non dici "avvia un Pod", ma dici "voglio che ci siano sempre 3 repliche di questo Pod". Il Deployment astrae il concetto di "mantenimento": se un nodo muore, il Deployment ricrea i Pod altrove. Se fai un update, gestisce lui la sostituzione graduale (Rolling Update).

#### Livello 4: Il Service (L'Astrazione della Rete)

* **Tecnologia:** Kubernetes Object (`Kind: Service`).
* **Cos'è:** Un IP statico e un DNS interno che punta a un gruppo di Pod.
* **Astrazione:** Astrae il **Puntamento (Discovery)**. Poiché i Pod vengono distrutti e ricreati continuamente con IP diversi, il Service funge da "centralino". Tu chiami il Service `my-api` e lui sa esattamente a quali Pod inviare il traffico, facendo anche da Load Balancer.

#### Livello 5: Il Nodo (L'Astrazione dell'Hardware)

* **Tecnologia:** Virtual Machine o Bare Metal.
* **Cos'è:** La macchina fisica o virtuale dove tutto "gira".
* **Astrazione:** Astrae la **Capacità Computazionale**. Per Kubernetes, un Nodo è solo un secchio di CPU e RAM. Lo Scheduler astrae la scelta della macchina: tu chiedi risorse, K8s decide dove metterle. Non devi più fare SSH in una specifica macchina per installare qualcosa.

#### Livello 6: Il Cluster (L'Infrastruttura Totale)

* **Tecnologia:** L'insieme di Control Plane + Nodi.
* **Cos'è:** L'intero ecosistema orchestrato.
* **Astrazione:** Astrae l'**Infrastruttura come un unico computer**. Gestisci l'intero parco macchine tramite un'unica API.

| Livello | Nome | Cosa risolve? |
| --- | --- | --- |
| **1** | **Container** | "Gira sulla mia macchina ma non sulla tua" |
| **2** | **Pod** | Gestione di processi correlati e networking locale |
| **3** | **Deployment** | "Se crasha chi lo riavvia?" e aggiornamenti software |
| **4** | **Service** | "Come trovo l'IP di un Pod che cambia sempre?" |
| **5** | **Node** | Gestione della CPU/RAM fisica |
| **6** | **Cluster** | Gestione dell'intero parco macchine come un'unica entità |

---

