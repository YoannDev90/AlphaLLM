#!/bin/bash

# ==============================================================================
# Deployment script for AlphaLLM
# ==============================================================================

if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "❌ Error: Missing .env file."
    exit 1
fi

if [ "$DEPLOY_REMOTE_HOST" == "votre_ip_ou_domaine" ] || [ -z "$DEPLOY_REMOTE_HOST" ]; then
    echo "❌ Error: You must configure your IP address or domain in the .env file"
    exit 1
fi

REMOTE_USER="${DEPLOY_REMOTE_USER:-user}"
REMOTE_HOST="${DEPLOY_REMOTE_HOST}"
REMOTE_DIR="${DEPLOY_REMOTE_DIR:-/.alphallm}"
SERVICE_NAME="${DEPLOY_SERVICE_NAME:-alphallm.service}"

if [ -z "$SSHPASS" ]; then
    read -sp "🔑 Enter the SSH password for ${REMOTE_USER}@${REMOTE_HOST}: " SSH_PASSWORD
    echo ""
    export SSHPASS="$SSH_PASSWORD"
fi

echo "🔄 Updating the list of commands in the README..."
python3 scripts/generate_docs.py

run_ssh() {
    if command -v sshpass >/dev/null 2>&1; then
        sshpass -e ssh -o StrictHostKeyChecking=no "$@"
    else
        ssh -o StrictHostKeyChecking=no "$@"
    fi
}

run_rsync() {
    if command -v sshpass >/dev/null 2>&1; then
        sshpass -e rsync -avz --delete -e "ssh -o StrictHostKeyChecking=no" "$@"
    else
        rsync -avz --delete -e "ssh -o StrictHostKeyChecking=no" "$@"
    fi
}

echo "------------------------------------------------------------"
echo "🚀 Deployment on ${REMOTE_HOST}"
echo "------------------------------------------------------------"

echo "📂 Preparing the remote directory..."
run_ssh "${REMOTE_USER}@${REMOTE_HOST}" "echo '$SSHPASS' | sudo -S mkdir -p ${REMOTE_DIR} && echo '$SSHPASS' | sudo -S chown ${REMOTE_USER}:${REMOTE_USER} ${REMOTE_DIR}"

echo "📤 Transferring files..."
# TODO : make this more robust by excluding .git and .gitignore content
run_rsync \
    --exclude '.git/' \
    --exclude '.venv/' \
    --exclude '__pycache__/' \
    --exclude '.ruff_cache/' \
    --exclude 'data/' \
    ./ "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"

echo "⚙️  Maintenance on the server..."
run_ssh "${REMOTE_USER}@${REMOTE_HOST}" "SSHPASS='$SSHPASS' REMOTE_DIR='$REMOTE_DIR' SERVICE_NAME='$SERVICE_NAME' REMOTE_USER_ESC='$REMOTE_USER' bash -s" << 'REMOTE_COMMANDS'
    set -e
    cd "${REMOTE_DIR}"
    
    if [ ! -d ".venv" ]; then 
        python3 -m venv .venv
    fi
    
    echo "🚀 Installing dependencies with uv..."
    ./.venv/bin/python -m pip install --quiet --upgrade uv
    ./.venv/bin/python -m uv pip install -r requirements.txt
    
    if [ -f "$SERVICE_NAME" ]; then
        echo "📜 Dynamic service configuration..."
        REMOTE_GROUP_ESC="$REMOTE_USER_ESC"
        
        sed -i "s/^User=.*/User=$REMOTE_USER_ESC/" "$SERVICE_NAME"
        sed -i "s/^Group=.*/Group=$REMOTE_GROUP_ESC/" "$SERVICE_NAME"
        sed -i "s|^WorkingDirectory=.*|WorkingDirectory=$REMOTE_DIR|" "$SERVICE_NAME"
        sed -i "s|^ExecStart=.*|ExecStart=$REMOTE_DIR/.venv/bin/python main.py|" "$SERVICE_NAME"
        
        echo "📂 Setting up the service..."
        echo "$SSHPASS" | sudo -S cp "$SERVICE_NAME" /etc/systemd/system/
        echo "$SSHPASS" | sudo -S systemctl daemon-reload
        echo "$SSHPASS" | sudo -S systemctl enable "$SERVICE_NAME"
    fi
    
    echo "🔄 Restarting the service..."
    echo "$SSHPASS" | sudo -S systemctl restart "$SERVICE_NAME"
    
    echo "------------------------------------------------------------"
    echo "✅ Deployment completed !"
    echo "------------------------------------------------------------"
REMOTE_COMMANDS
