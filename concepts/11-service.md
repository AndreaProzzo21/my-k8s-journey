# Kubernetes Services: Networking & Service Discovery

## 1. Il Problema: L'Effimerità dei Pod

In Kubernetes, i Pod sono progettati per essere temporanei. Se un Pod muore, un controller (come il Deployment) ne crea uno nuovo.

* Ogni nuovo Pod riceve un **indirizzo IP dinamico**.
* È impossibile configurare un client (es. un frontend) affinché punti direttamente all'IP di un Pod, perché quell'IP cambierà.

**La Soluzione:** Il **Service**. Un'astrazione che fornisce un **IP statico** (Virtual IP) e un **nome DNS** che rimangono invariati per tutta la vita del servizio, indipendentemente da quanti Pod vengano creati o distrutti.

---

## 2. Come funziona "Sotto il Cofano": Kube-Proxy ed Endpoints

Mentre il Service è un concetto logico, il lavoro sporco viene fatto da due componenti tecnici:

### A. Gli Endpoints

Ogni volta che crei un Service con un selettore, Kubernetes crea automaticamente un oggetto chiamato **Endpoints**. Questo oggetto contiene la lista in tempo reale degli indirizzi IP di tutti i Pod sani (Healty) che corrispondono alle etichette (`Labels`).

### B. Kube-Proxy: Il vigile urbano

In ogni nodo del cluster gira un componente chiamato **kube-proxy**. Il suo compito è monitorare il Control Plane per nuovi Service ed Endpoints.

* **IP Table Manager**: Kube-proxy aggiorna le regole di rete (solitamente tramite `iptables` o `IPVS`) su ogni nodo.
* **Load Balancing**: Quando un Pod tenta di connettersi all'IP del Service, kube-proxy intercetta la richiesta e agisce come un bilanciatore di carico (di default usa l'algoritmo **Round Robin**), smistando il traffico verso uno degli IP presenti nella lista degli Endpoints.

---

## 3. Anatomia di un Service (Labels & Selectors)

Il legame tra un Service e i Pod non è basato sull'IP, ma sulle **Labels**.

* **Labels**: Etichette applicate ai Pod (es. `app: backend`).
* **Selector**: Filtro definito nel Service per trovare i Pod da servire.

### Esempio di Manifest YAML

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-backend-service
spec:
  selector:
    app: api-server          # Cerca i Pod con questa label
  ports:
    - protocol: TCP
      port: 80               # Porta esposta dal Servizio (Cluster IP)
      targetPort: 8080       # Porta reale su cui il container è in ascolto

```

---

## 4. Tipologie di Service (Service Types)

### A. ClusterIP (Default)

Esprime il servizio solo **all'interno del cluster**. È il tipo più comune, usato per la comunicazione tra microservizi interni (es. un Monitoring-Worker che parla con InfluxDB).

### B. NodePort

Espone il servizio su una **porta specifica di ogni Nodo** (range 30000-32767). Rende il servizio raggiungibile dall'esterno usando `<IP-del-Nodo>:<NodePort>`.

### C. LoadBalancer

Utilizzato in Cloud. Il provider crea un Load Balancer reale con un **IP Pubblico** che instrada il traffico verso i nodi del cluster.

### D. ExternalName

Mappa un servizio a un nome DNS esterno (es. `db.azienda.it`). È un semplice alias DNS.

---

## 5. Port Mapping: Chi parla con chi?

1. **`port`**: Porta del Service (punto di ingresso interno).
2. **`targetPort`**: Porta del container nel Pod (dove gira l'app).
3. **`nodePort`**: Porta esterna sul nodo (solo per NodePort).

```text
Traffic Flow:
Pod A -> [Service DNS/IP]:[port] -> Kube-Proxy (Round Robin) -> [Pod B IP]:[targetPort]

```

---

## 6. Service Discovery & DNS Interno

Kubernetes include **CoreDNS**. Ogni Service riceve un record DNS:

* `http://nome-servizio` (stesso namespace).
* `http://nome-servizio.namespace.svc.cluster.local` (FQDN).

---

## 7. Best Practices & Troubleshooting

### Best Practices

* **Usa nomi per le porte**: Definisci `name: http-web` nel Pod e usa `targetPort: http-web` nel Service.
* **Healty Check**: Se un Pod fallisce il `readinessProbe`, Kubernetes lo rimuove automaticamente dagli Endpoints del Service, evitando che `kube-proxy` gli invii traffico.

### Troubleshooting comuni

* **"No Endpoints"**: Se `kubectl get endpoints` è vuoto, il `selector` non trova Pod con le label giuste.
* **Kube-Proxy lag**: In rari casi di cluster molto grandi, può esserci un piccolo ritardo nell'aggiornamento delle regole di rete.

---
