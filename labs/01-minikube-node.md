# Lab 01: Setup del Laboratorio e Deploy del primo Pod

Questo primo laboratorio è stato dedicato alla configurazione dell'ambiente di lavoro e alla verifica delle funzionalità core di **Kubernetes**. L'obiettivo era creare un ambiente isolato, riproducibile e leggero per iniziare a testare i concetti di orchestrazione.

## L'Architettura del Laboratorio

Per garantire la massima pulizia sul computer ospite (Host), abbiamo deciso di non installare Kubernetes direttamente sul sistema operativo principale, ma di utilizzare una **Virtual Machine** dedicata su **VirtualBox**.

Le scelte tecniche principali sono state:

* **OS:** Ubuntu Server 22.04 LTS (scelto per la sua leggerezza e stabilità).
* **Risorse:** 2 CPU e 4GB di RAM (requisiti minimi per far girare il control plane di K8s senza rallentamenti).
* **Network:** Configurazione in **Bridge Mode** per permettere alla VM di avere un proprio IP nella rete locale, facilitando l'accesso via SSH da terminali esterni (come WSL2).

## Strumenti Installati

Il setup ha previsto l'installazione di tre componenti fondamentali:

1. **Docker Engine:** Utilizzato come runtime per i container.
2. **Minikube:** La soluzione scelta per far girare un cluster Kubernetes a nodo singolo in locale. È stato avviato con il comando `minikube start --driver=docker`, una scelta che permette di far girare Kubernetes all'interno di un container Docker, ottimizzando le performance della VM.
3. **kubectl:** Il tool a riga di comando necessario per interagire con il cluster e inviare i file di configurazione.

## Il Primo Test: Nginx Pod

Come test di validazione, abbiamo effettuato il deploy di un server web **Nginx**. Invece di utilizzare comandi imperativi, abbiamo preferito un approccio dichiarativo scrivendo il nostro primo file **Manifest**.

### Il file `pod-manifest.yaml`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-test
spec:
  containers:
  - name: nginx
    image: nginx:1.14.2
    ports:
    - containerPort: 80

```

### Processo di Verifica

Dopo aver applicato il file con il comando `kubectl apply -f pod-manifest.yaml`, abbiamo verificato lo stato del sistema:

* **Stato del Pod:** Controllato tramite `kubectl get pods` per assicurarci che il container fosse in stato *Running*.
* **Connettività:** Abbiamo testato il raggiungimento del server web tramite il **Port Forwarding**:
```bash
kubectl port-forward nginx-test 8080:80

```

Effettuando una `curl` verso `localhost:8080`, abbiamo ricevuto correttamente la pagina di default di Nginx, confermando che il cluster è operativo e configurato correttamente.

---
