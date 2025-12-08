# db.py
# -------------------------------------
# Conexión a MySQL (Clever Cloud)
# -------------------------------------

from sqlalchemy import create_engine

# --------------------------------------------------------
# 🔧 PON TUS DATOS REALES AQUI
# --------------------------------------------------------

USER = "uenzqgunbvjgknad"
PASSWORD = "8WzopsyqtDhBI7ZPnVQU"
HOST = "bbg3b0loqlocqhpufv6m-mysql.services.clever-cloud.com"             # ej: xxxxxx.clever-cloud.com
DATABASE = "bbg3b0loqlocqhpufv6m"
PORT = 3306                  # MySQL usa 3306

# --------------------------------------------------------
# 🔗 Crear motor SQLAlchemy
# --------------------------------------------------------
engine = create_engine(
    f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}",
    pool_pre_ping=True
)


# notifications.py
import requests

TELEGRAM_TOKEN = "8476867150:AAEP1mvaHz04oHYoEV0S8EgCpiEjU4hOQc0"
CHAT_ID = "2090371962"

def enviar_notificacion(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje
    }
    requests.post(url, json=payload)

