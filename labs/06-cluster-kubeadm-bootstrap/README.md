# 📑 Guida al Bootstrap Manuale: Kubernetes "From Scratch" (kubeadm)

Dopo aver sperimentato con soluzioni pronte all'uso come **Minikube**, questa guida documenta il passaggio a un utilizzo **serio e professionale** di Kubernetes. L'obiettivo è abbandonare gli automatismi per costruire un cluster multi-nodo partendo da macchine Linux vergini, comprendendo ogni singolo componente del Control Plane e dei nodi Worker.

---

## 1. Architettura dell'Ambiente (VirtualBox)

Per emulare un ambiente di produzione, configuriamo le VM in modo che abbiano risorse reali e visibilità di rete completa.

* **Master Node**: 2 vCPU (requisito minimo `kubeadm`), 2GB RAM.
* **Worker Node**: 1 o 2 vCPU, 2GB RAM.
* **Rete**: Impostare la scheda su **Scheda con bridge (Bridge Adapter)**. In "Avanzate", impostare Modalità promiscua su **Permetti tutto**. Questo garantisce che ogni nodo riceva un IP reale dalla tua LAN.
* **OS**: Ubuntu Server 22.04 LTS (installazione minimal consigliata).

---

## 2. Accesso e Identità di Rete

Sono stati eseguiti i seguenti passaggi su **tutti i nodi** per garantire una comunicazione fluida.

### Abilitare SSH

Essenziale per gestire il cluster comodamente dal terminale preferito senza usare l'interfaccia di VirtualBox.

```bash
sudo apt update && sudo apt install openssh-server -y
sudo systemctl enable --now ssh

```

### Hostname Univoci

Identificare chiaramente chi è il Master e chi il Worker.

```bash
# SUL MASTER
sudo hostnamectl set-hostname k8s-master

# SUL WORKER
sudo hostnamectl set-hostname k8s-worker-1

```

### Risoluzione Nomi (DNS Locale)

Modifica `/etc/hosts` su **tutti i nodi**. In Kubernetes, i nodi devono potersi contattare per nome, non solo per IP.

```bash
sudo nano /etc/hosts
# Sostituisci con i tuoi IP reali:
192.168.1.50 k8s-master
192.168.1.51 k8s-worker-1

```

---

## 3. Hardening del Sistema Operativo

Kubernetes richiede un controllo totale sulle risorse. Dobbiamo disabilitare i meccanismi che interferirebbero con lo scheduler.

### Disabilitazione Swap (Mandatorio)

Se lo swap è attivo, le performance dei container diventano imprevedibili e il `kubelet` non partirà.

```bash
sudo swapoff -a
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab

```

### Configurazione Moduli Kernel

Carichiamo i moduli necessari per gestire il traffico di rete dei container (overlay) e il filtraggio dei pacchetti (bridge).

```bash
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

```

### Parametri di Rete (IP Forwarding)

Abilitiamo il passaggio del traffico tra i nodi e i Pod, permettendo a `iptables` di vedere il traffico bridge.

```bash
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sudo sysctl --system

```

---

## 4. Container Runtime (containerd)

A differenza di Minikube che gestisce tutto internamente, qui installiamo e configuriamo `containerd` come motore di esecuzione standard.

```bash
sudo apt-get update && sudo apt-get install -y containerd

# Genera configurazione di default
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml

# Configurazione Cgroup con Systemd (Punto critico per la stabilità)
sudo sed -i 's/SystemdCgroup \= false/SystemdCgroup \= true/g' /etc/containerd/config.toml
sudo systemctl restart containerd

```

> **Nota**: Impostare `SystemdCgroup = true` è vitale. Se il runtime e il sistema operativo usano driver diversi per i cgroups, il nodo inizierà a lanciare errori di memoria e crashare sotto carico.

---

## 5. Installazione Strumenti Kubernetes

Installiamo il "trittico" fondamentale su tutti i nodi.

```bash
# Aggiunta delle chiavi e dei repository ufficiali
sudo mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Installazione binari
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl

```

---

## 6. Inizializzazione del Cluster

### Step 1: Sul MASTER

Inizializziamo il piano di controllo. L'argomento `--pod-network-cidr` è specifico per il plugin di rete che useremo (Flannel).

```bash
sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address=<IP-DEL-MASTER>

```

**Configurazione accesso CLI per proprio utente:**

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

```

### Step 2: Installazione Network Plugin (Flannel)

Senza questo, i Pod non possono comunicare tra loro e il DNS interno non funzionerà.

```bash
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml

```

### Step 3: Sul WORKER

Copiare comando `kubeadm join` generato dal master alla fine dell'init e lanciarlo sul worker:

```bash
sudo kubeadm join <IP-MASTER>:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>

```

---

## 7. Verifica dello Stato

Dal **Master**, controlla che tutti i nodi siano in stato `Ready`:

```bash
kubectl get nodes -o wide

```
---

## 8. Validazione Operativa e Stress Test

Una volta che i nodi risultano `Ready`, è fondamentale verificare che il cluster gestisca correttamente il ciclo di vita delle applicazioni.

### A. Test di Deployment e Creazione Pod

Creiamo un deployment Nginx per verificare che l'immagine venga scaricata e il container avviato correttamente.

```bash
kubectl create deployment test-nginx --image=nginx
kubectl get pods -w

```

### B. Test di Scaling (Verifica dell'Orchestratore)

Verifichiamo che il cluster sia in grado di distribuire il carico su più repliche e, potenzialmente, su diversi nodi.

```bash
# Scaliamo da 1 a 4 repliche
kubectl scale deployment test-nginx --replicas=4

# Verifichiamo la distribuzione sui nodi
kubectl get pods -o wide

```

*In questo step, ci assicuriamo che i Pod vengano assegnati correttamente sia al Master (se abilitato) che ai Worker.*

### C. Test di Rete Interna (CoreDNS)

Verifichiamo che i Pod possano risolversi a vicenda.

```bash
kubectl run busybox --image=busybox --restart=Never -it -- rm -f /etc/hosts
# Dentro il pod:
nslookup kubernetes.default

```

### D. Pulizia dei Test

Una volta confermato il corretto funzionamento:

```bash
kubectl delete deployment test-nginx

```

**Cluster configurato e validato correttamente.** Ora il sistema è pronto per ospitare carichi di lavoro reali e complessi.
