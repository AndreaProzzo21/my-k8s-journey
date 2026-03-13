# Kubernetes Services: Networking & Service Discovery

## 1. Il Problema: L'Effimerità dei Pod

In Kubernetes, i Pod sono progettati per essere temporanei. Se un Pod muore, un controller (come il Deployment) ne crea uno nuovo.

* Ogni nuovo Pod riceve un **indirizzo IP dinamico**.
* È impossibile configurare un client (es. un frontend) affinché punti direttamente all'IP di un Pod, perché quell'IP cambierà.

**La Soluzione:** Il **Service**. Un'astrazione che definisce un set logico di Pod e una politica per accedervi. Il Service fornisce un **IP statico** e un **nome DNS** che rimangono invariati per tutta la vita del servizio.

---

## 2. Anatomia di un Service (Labels & Selectors)

Il legame tra un Service e i Pod non è basato sull'IP, ma sulle **Labels**.

* **Labels**: Etichette applicate ai Pod (es. `app: backend`).
* **Selector**: Filtro definito nel Service per trovare i Pod da servire.
* **Endpoints**: Kubernetes crea automaticamente un oggetto "Endpoints" che contiene la lista aggiornata degli IP dei Pod che corrispondono al selettore.

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

## 3. Tipologie di Service (Service Types)

Esistono quattro modi principali per esporre un servizio, a seconda di dove si trova il client.

### A. ClusterIP (Default)

Esprime il servizio solo **all'interno del cluster**. È il tipo più comune, usato per la comunicazione tra microservizi interni (es. un Monitoring-Worker che parla con InfluxDB).

* **IP:** Virtuale, raggiungibile solo internamente.

### B. NodePort

Espone il servizio su una **porta specifica di ogni Nodo** del cluster. Rende il servizio raggiungibile dall'esterno usando `<IP-del-Nodo>:<NodePort>`.

* **Range porte:** 30000 - 32767.
* **Uso:** Lab, test, o quando non si ha un Load Balancer cloud.

### C. LoadBalancer

Utilizzato in ambienti Cloud (AWS, GCP, Azure). Il provider crea un Load Balancer reale che instrada il traffico verso i nodi.

* **IP:** Pubblico, fornito dal Cloud Provider.

### D. ExternalName

Mappa un servizio a un nome DNS esterno (es. `my-db.external.com`) invece che a un selettore di Pod. Non c'è proxying di traffico, è solo un redirect a livello DNS.

---

## 4. Port Mapping: Chi parla con chi?

È fondamentale distinguere le tre tipologie di porte:

1. **`port`**: La porta su cui il Service è raggiungibile all'interno del cluster.
2. **`targetPort`**: La porta su cui l'applicazione è in esecuzione dentro il container.
3. **`nodePort`**: La porta esterna (solo per tipo NodePort) su cui i client esterni possono connettersi.

```text
Traffic Flow (NodePort):
Client -> [Node IP]:[nodePort] -> [Service IP]:[port] -> [Pod IP]:[targetPort]

```

---

## 5. Service Discovery & DNS Interno

Kubernetes include un componente chiamato **CoreDNS**. Ogni volta che crei un Service, viene registrata una voce DNS automatica.

Se il tuo servizio si chiama `influxdb-service` nel namespace `default`, gli altri Pod possono contattarlo semplicemente usando:

* `http://influxdb-service` (se sono nello stesso namespace).
* `http://influxdb-service.default.svc.cluster.local` (nome completo FQDN).

---

## 6. Best Practices & Troubleshooting

### Best Practices

* **Usa nomi per le porte**: Invece di `targetPort: 8080`, definisci un `name: http-web` nel Pod e usa `targetPort: http-web` nel Service. Rende il codice più flessibile.
* **Evita Session Affinity se non necessaria**: Kubernetes distribuisce il traffico in modo casuale (Round Robin). Se il tuo servizio è stateless, non forzare l'affinità del client a un singolo Pod.

### Troubleshooting comuni

* **"Connection Refused"**: Controlla che la `targetPort` nel Service corrisponda esattamente alla `containerPort` definita nel Deployment.
* **"No Endpoints"**: Se `kubectl get endpoints` è vuoto, significa che il `selector` del Service non corrisponde a nessuna `label` dei Pod. Verifica i typos!
* **DNS failure**: Prova a fare un `nslookup <nome-servizio>` dall'interno di un Pod per verificare se il CoreDNS sta funzionando.

---

