# Accesso ed Isolamento: Ingress & Network Policies

Mentre i Service risolvono il problema della connettività interna, la gestione professionale di un cluster richiede di rispondere a due domande critiche:

1. **Esposizione**: Come posso esporre decine di servizi web usando un unico punto di accesso e certificati SSL? (**Ingress**)
2. **Sicurezza**: Come posso impedire che un Pod compromesso scansioni l'intera rete interna? O in generale come regolare/isolare la comunicazione tra pods? (**Network Policies**)

---

## 1. Ingress: Il "Vigile Urbano" del Cluster (Layer 7)

L'**Ingress** non è un servizio, ma un insieme di regole che permette a un **Ingress Controller** (es. Nginx, Traefik, HAProxy) di smistare il traffico HTTP/HTTPS esterno verso i Service interni.

### Perché è meglio del NodePort?

* **Virtual Hosting**: Puoi gestire più domini (`app1.com`, `app2.com`) sullo stesso IP.
* **Path Routing**: Puoi mappare percorsi diversi (`/api` vs `/dashboard`) a servizi diversi.
* **SSL Termination**: Gestisci i certificati TLS in un unico punto invece che in ogni singolo Pod.

### Esempio di Manifest Ingress

Nell'ottica del nostro lab, ecco come esporremmo Grafana e una ipotetica API:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: factory-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: monitoring.pdm.it
    http:
      paths:
      - path: /grafana
        pathType: Prefix
        backend:
          service:
            name: grafana-service
            port:
              number: 3000
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: inference-service
            port:
              number: 5000

```

---

## 2. Network Policies: Sicurezza "Zero Trust"

In Kubernetes, il networking è **aperto di default**. Una **Network Policy** è un firewall basato su etichette (Labels) che permette di isolare i Pod.

### Logica di funzionamento

* **Isolamento**: Un Pod non è isolato finché non esiste una Network Policy che lo seleziona. Una volta selezionato, rifiuta tutto il traffico tranne quello esplicitamente permesso.
* **Selettori**: Si basano su `podSelector` (quali Pod proteggere) e regole di `ingress/egress` (chi può parlare con loro).

### Case Study Lab 05: Proteggere il Database InfluxDB

Vogliamo impedire che i Simulatori o il Broker MQTT possano parlare direttamente con InfluxDB. Solo il `monitoring-worker` deve avere l'accesso.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: influxdb-allow-monitoring
spec:
  podSelector:
    matchLabels:
      app: influxdb           # Bersaglio: Proteggiamo InfluxDB
  policyTypes:
  - Ingress                   # Controlliamo il traffico in entrata
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: monitoring-worker # Sorgente: Permesso solo al worker
    ports:
    - protocol: TCP
      port: 8086               # Porta specifica

```

---

## 3. Differenze Chiave e Sinergia

Questa tabella mette a confronto i tre pilastri fondamentali, evidenziando come passiamo dal "far parlare i Pod" al "proteggerli".

| Concetto | Livello OSI | Focus | Applicazione Tipica |
| --- | --- | --- | --- |
| **Service** | Layer 4 (Transport) | **Connettività Interna** | Fornire un IP statico e bilanciare il traffico tra i Pod di uno stesso gruppo (Service Discovery). |
| **Ingress** | Layer 7 (Application) | **Esposizione Esterna** | Gestire l'accesso dal mondo esterno tramite domini (es. `mia-app.it`), rotte URL e certificati HTTPS. |
| **Network Policy** | Layer 3/4 (Network/Transport) | **Isolamento e Sicurezza** | Definire "chi può parlare con chi" all'interno del cluster (Firewall granulare tra Pod). |

### Il Flusso di una richiesta sicura:

1. **Esterno** -> Richiesta su `monitoring.pdm.it/grafana`.
2. **Ingress Controller** -> Riceve la richiesta, termina l'SSL e la inoltra al `grafana-service`.
3. **Network Policy** -> Controlla se l'Ingress Controller ha il permesso di parlare con il Pod di Grafana.
4. **Grafana Pod** -> Tenta di leggere da InfluxDB; la Network Policy di InfluxDB verifica che Grafana sia autorizzato.

---

## 4. Considerazioni Finali per il Laboratorio

* **Il Controller è necessario**: L'Ingress YAML è solo una "configurazione". Senza un Ingress Controller installato (es. `minikube addons enable ingress`), non succederà nulla.
* **CNI Plugin**: Le Network Policies richiedono un plugin di rete specifico (come Calico o Cilium). Su Minikube standard spesso non filtrano traffico a meno di configurazioni specifiche.
* **Default Deny**: La strategia più sicura è creare una policy "Deny All" per il namespace e aprire solo i flussi strettamente necessari (Principio del minimo privilegio).

---

### Filosofia del Networking: Abilitazione, Organizzazione e Restrizione

Per comprendere appieno l'ecosistema di rete in Kubernetes, è utile osservare come i tre componenti principali interagiscano secondo una gerarchia di responsabilità:

1. **Il Service è l'elemento abilitante**: Rappresenta il presupposto fondamentale per la comunicazione. Senza di esso, i microservizi rimarrebbero isolati nel loro ciclo di vita effimero; il Service fornisce l'identità stabile (DNS e IP) necessaria affinché i componenti possano trovarsi e interagire.
2. **L'Ingress è l'elemento organizzativo**: Agisce come il punto di controllo superiore che gestisce la complessità dell'esposizione verso l'esterno. Centralizzando il routing basato su domini, percorsi URL e la terminazione SSL, trasforma un insieme di servizi sparsi in un'architettura web coerente e professionale.
3. **La Network Policy è l'elemento restrittivo**: Mentre i primi due si occupano di "aprire" canali di comunicazione, la Network Policy applica il rigore della sicurezza secondo il **principio del minimo privilegio**. Definisce i confini invalicabili all'interno del cluster, assicurando che ogni Pod possa parlare esclusivamente con chi è strettamente necessario alla sua funzione, riducendo drasticamente la superficie di attacco.

---

