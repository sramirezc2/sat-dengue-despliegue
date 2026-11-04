#!/usr/bin/env bash
# Arranque de la instancia EC2. Se pasa como user-data al lanzarla.
#
# La instancia se configura sola: no hace falta entrar por SSH, que en AWS
# Academy ademas suele estar cerrado. Al terminar deja la aplicacion corriendo
# y el servicio systemd habilitado, de modo que cuando el laboratorio detenga y
# vuelva a arrancar la instancia, el tablero vuelve sin intervencion.
#
# Variables que se pueden fijar antes de lanzar (todas tienen default):
#   REPOSITORIO   URL del repositorio a clonar
#   RAMA          rama a desplegar
#   BUCKET        bucket de S3 con los resultados publicados
#   PUERTO        puerto publico
set -euxo pipefail

REPOSITORIO="${REPOSITORIO:-https://github.com/sramirezc2/sat-dengue-despliegue.git}"
RAMA="${RAMA:-main}"
BUCKET="${BUCKET:-}"
PUERTO="${PUERTO:-80}"
DESTINO=/opt/sat-dengue
REGISTRO=/var/log/arranque-sat.log

exec > >(tee -a "$REGISTRO") 2>&1
echo "=== arranque $(date -Is)"

# ---------------------------------------------------------------- paquetes
dnf install -y docker git
systemctl enable --now docker
usermod -aG docker ec2-user

# Compose v2 como plugin de docker; Amazon Linux 2023 no lo trae.
ARQ=$(uname -m)
mkdir -p /usr/libexec/docker/cli-plugins
curl -fsSL "https://github.com/docker/compose/releases/download/v2.39.1/docker-compose-linux-${ARQ}" \
  -o /usr/libexec/docker/cli-plugins/docker-compose
chmod +x /usr/libexec/docker/cli-plugins/docker-compose
docker compose version

# ----------------------------------------------------------------- codigo
if [ -d "$DESTINO/.git" ]; then
  git -C "$DESTINO" fetch --depth 1 origin "$RAMA"
  git -C "$DESTINO" reset --hard "origin/$RAMA"
else
  git clone --depth 1 --branch "$RAMA" "$REPOSITORIO" "$DESTINO"
fi

# ---------------------------------------------------------- configuracion
# La IP publica se usa como origen autorizado de CORS. El navegador habla con
# el mismo origen a traves del proxy, asi que esto es solo defensa en
# profundidad por si alguien consulta la API desde otro lado.
TOKEN=$(curl -fsS -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 300" || echo "")
IP=$(curl -fsS -H "X-aws-ec2-metadata-token: $TOKEN" \
  "http://169.254.169.254/latest/meta-data/public-ipv4" || echo "")
REGION=$(curl -fsS -H "X-aws-ec2-metadata-token: $TOKEN" \
  "http://169.254.169.254/latest/meta-data/placement/region" || echo "us-east-1")

cp "$DESTINO/.env.example" "$DESTINO/.env"
{
  echo "SATD_ENTORNO=aws"
  echo "PUERTO_PUBLICO=${PUERTO}"
  echo "AWS_DEFAULT_REGION=${REGION}"
  echo "SATD_BUCKET_S3=${BUCKET}"
  echo "SATD_SINCRONIZAR_AL_ARRANCAR=$([ -n "$BUCKET" ] && echo true || echo false)"
  echo "SATD_ORIGENES_CORS=http://${IP}"
} >> "$DESTINO/.env"

# -------------------------------------------------------------- servicio
install -m 0644 "$DESTINO/scripts/sat-dengue.service" /etc/systemd/system/sat-dengue.service
systemctl daemon-reload
systemctl enable sat-dengue

# La primera construccion se hace aqui y no dentro del servicio, para que un
# fallo de compilacion quede en este registro y no en el journal del servicio.
cd "$DESTINO"
docker compose -f docker/docker-compose.yml --env-file .env build
systemctl start sat-dengue

# -------------------------------------------------------- comprobacion
for intento in $(seq 1 30); do
  if curl -fsS "http://localhost:${PUERTO}/api/salud" > /dev/null; then
    echo "=== la aplicacion responde en http://${IP}:${PUERTO}"
    curl -fsS "http://localhost:${PUERTO}/api/salud"
    exit 0
  fi
  echo "esperando a que levante ($intento/30)"
  sleep 10
done

echo "=== la aplicacion no respondio a tiempo; revisar docker compose logs"
docker compose -f docker/docker-compose.yml --env-file .env ps
exit 1
