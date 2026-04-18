#!/bin/bash

# --- CONFIGURAZIONE (Modifica se necessario) ---
SERVICE_NAME="pwned_robot"
PROJECT_DIR="/home/ubuntu/bot/pwned_robot"           # Cartella dove sta il main.py
VENV_DIR="$PROJECT_DIR/venv"              # Cartella del Virtual Environment
PYTHON_EXEC="$VENV_DIR/bin/python"        # Eseguibile Python del venv
PIP_EXEC="$VENV_DIR/bin/pip"             # pip del venv
MAIN_SCRIPT="main.py"                     # File principale del bot
BOT_USER="ubuntu"                         # Utente Linux che eseguirà il bot
ENV_FILE="$PROJECT_DIR/.env"             # File variabili d'ambiente
# -----------------------------------------------

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════╗${NC}"
echo -e "${CYAN}║      PWNED ROBOT — SERVICE SETUP     ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════╝${NC}"
echo ""

# 1. Controllo privilegi di root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Errore: devi eseguire questo script con sudo.${NC}"
  echo "  Usa: sudo bash setup_service.sh"
  exit 1
fi

# 2. Verifica esistenza del file principale
if [ ! -f "$PROJECT_DIR/$MAIN_SCRIPT" ]; then
  echo -e "${RED}Errore: $MAIN_SCRIPT non trovato in $PROJECT_DIR${NC}"
  echo "  Assicurati che il progetto sia già nella cartella corretta."
  exit 1
fi

# 3. Verifica presenza di requirements.txt
if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
  echo -e "${RED}Errore: requirements.txt non trovato in $PROJECT_DIR${NC}"
  exit 1
fi

# 4. Verifica disponibilità di python3
if ! command -v python3 &> /dev/null; then
  echo -e "${RED}Errore: python3 non trovato.${NC}"
  echo "  Installa con: sudo apt install python3 python3-venv python3-pip"
  exit 1
fi

echo -e "${GREEN}[1/6] Prerequisiti verificati.${NC}"

# 5. Assicura che la cartella del progetto sia di proprietà dell'utente bot
#    (necessario se i file sono stati copiati da root)
echo "Impostazione proprietà di $PROJECT_DIR → $BOT_USER..."
chown -R "$BOT_USER:$BOT_USER" "$PROJECT_DIR"

# 6. Crea il virtual environment se non esiste
if [ ! -d "$VENV_DIR" ]; then
  echo "Creazione virtual environment in $VENV_DIR..."
  sudo -u "$BOT_USER" python3 -m venv "$VENV_DIR"
  if [ $? -ne 0 ]; then
    echo -e "${RED}Errore: impossibile creare il virtual environment.${NC}"
    echo "  Installa python3-venv con: sudo apt install python3-venv"
    exit 1
  fi
  echo -e "${GREEN}[2/6] Virtual environment creato.${NC}"
else
  echo -e "${GREEN}[2/6] Virtual environment già esistente — riutilizzato.${NC}"
fi

# 6. Installa / aggiorna le dipendenze
echo "Installazione dipendenze da requirements.txt..."
sudo -u "$BOT_USER" "$PIP_EXEC" install --upgrade pip -q
sudo -u "$BOT_USER" "$PIP_EXEC" install -r "$PROJECT_DIR/requirements.txt" -q
if [ $? -ne 0 ]; then
  echo -e "${RED}Errore durante l'installazione delle dipendenze.${NC}"
  exit 1
fi
echo -e "${GREEN}[3/6] Dipendenze installate.${NC}"

# 7. Verifica database.sql e schema
if [ -f "$PROJECT_DIR/database.sql" ]; then
  echo -e "${YELLOW}[!] Ricordati di caricare lo schema del database se non l'hai ancora fatto:${NC}"
  echo "      mysql -u root -p < $PROJECT_DIR/database.sql"
fi

# 8. Verifica presenza .env
if [ ! -f "$ENV_FILE" ]; then
  echo -e "${YELLOW}[4/6] Attenzione: file .env non trovato in $PROJECT_DIR${NC}"
  if [ -f "$PROJECT_DIR/.env.example" ]; then
    echo "  Copia il template e compila le variabili:"
    echo "    cp $PROJECT_DIR/.env.example $PROJECT_DIR/.env"
    echo "    nano $PROJECT_DIR/.env"
  else
    echo "  Crea il file .env con le variabili necessarie prima di avviare il servizio."
  fi
  echo ""
else
  echo -e "${GREEN}[4/6] File .env trovato.${NC}"
fi

# 9. Scrittura del file .service
echo "Creazione del file di servizio /etc/systemd/system/$SERVICE_NAME.service..."

cat <<EOF > /etc/systemd/system/$SERVICE_NAME.service
[Unit]
Description=Pwned Robot — Telegram breach-check bot
Documentation=https://github.com/garboh/pwned-robot
After=network.target mysql.service redis.service
Requires=mysql.service
Wants=redis.service

[Service]
User=$BOT_USER
Group=$BOT_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_EXEC $MAIN_SCRIPT
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=5

# Mantiene i log leggibili da journalctl
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Variabili ambiente
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=-$ENV_FILE

# Hardening di sicurezza
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$PROJECT_DIR

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}[5/6] File di servizio creato.${NC}"

# 10. Attivazione e avvio del servizio
echo "Ricaricamento demone systemd..."
systemctl daemon-reload

echo "Abilitazione avvio automatico al boot..."
systemctl enable "$SERVICE_NAME"

echo "Avvio del servizio..."
systemctl restart "$SERVICE_NAME"

# 11. Verifica finale
sleep 2
echo -e "${GREEN}[6/6] Installazione completata.${NC}"
echo ""
echo -e "${CYAN}╔══════════════════════════════════════╗${NC}"
echo -e "${CYAN}║          STATO DEL SERVIZIO          ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════╝${NC}"
systemctl status "$SERVICE_NAME" --no-pager
echo ""
echo -e "  Log in tempo reale : ${GREEN}sudo journalctl -u $SERVICE_NAME -f${NC}"
echo -e "  Riavvia il servizio: ${GREEN}sudo systemctl restart $SERVICE_NAME${NC}"
echo -e "  Ferma il servizio  : ${GREEN}sudo systemctl stop $SERVICE_NAME${NC}"
echo -e "  Disabilita boot    : ${GREEN}sudo systemctl disable $SERVICE_NAME${NC}"
