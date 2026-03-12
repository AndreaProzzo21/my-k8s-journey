# 🧠 ML Models Directory

Questa cartella è destinata a contenere i modelli di Machine Learning pre-addestrati necessari per il corretto funzionamento dell'**Inference Service**.

### ⚠️ Importante

Per motivi di spazio e gestione delle versioni, i file `.pkl` non sono inclusi in questa repository. Devono essere copiati manualmente in questa posizione prima di eseguire il comando `docker build`.

## 📂 Struttura e Nomenclatura dei File

Il servizio di inferenza si aspetta i seguenti file con nomi **case-sensitive** precisi. Assicurati che i tuoi modelli esportati corrispondano allo schema seguente:

| Nome File | Tipo di Modello | Descrizione |
| --- | --- | --- |
| `classifier_state_v2.pkl` | **Random Forest / XGBoost** | Classificatore per lo stato della pompa (Healthy, Warning, Faulty). |
| `regressor_health_v2.pkl` | **Regression (Linear/RF)** | Regressore per il calcolo dello Score di Salute (0-100%). |
| `scaler_v2.pkl` | **StandardScaler** | Scaler utilizzato per la normalizzazione dei dati in ingresso. |
| `label_encoder_v2.pkl` | **LabelEncoder** | Encoder per decodificare le classi predette dal classificatore. |

## 🛠️ Come aggiungere i modelli

1. Genera i modelli tramite il notebook/script di training.
2. Copia i 4 file sopra elencati in questa cartella (`~/pdm-project/models/`).
3. Esegui la build dell'immagine Docker dell'inference dalla root del progetto:
```bash
docker build -t pdm-inference:v1 -f inference/Dockerfile .

```

## 🔍 Logica di Caricamento

All'avvio dell'Inference Service, il `Predictor` caricherà questi file dalla directory `/app/models/` (percorso interno al container). Se uno dei file è mancante o ha un nome errato, il servizio loggherà un errore critico e si arresterà per evitare previsioni inconsistenti.

---

