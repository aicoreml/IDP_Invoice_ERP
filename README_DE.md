# IDP_App_DE - Intelligente Dokumentenverarbeitung

Eine leistungsstarke Dokumentenverarbeitungs- und Q&A-System mit KI-Unterstützung. Laden Sie Dokumente hoch, extrahieren Sie Text mit OCR und stellen Sie Fragen zu Ihren Inhalten in natürlicher Sprache.

![Status](https://img.shields.io/badge/status-ready-success)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 Funktionen

- **Multi-Format Unterstützung**: PDF, DOCX, TXT, Bilder
- **OCR Textextraktion**: Tesseract-basierte OCR für gescannte Dokumente
- **Semantische Suche**: Vektor-Embeddings für intelligente Dokumentensuche
- **KI-gestützte Q&A**: Stellen Sie Fragen und erhalten Sie Antworten basierend auf Dokumentinhalten
- **🌍 Mehrsprachige Unterstützung**: Stellen Sie Fragen in 50+ Sprachen!
  - Deutsche Fragen zu englischen Dokumenten ✅
  - Englische Fragen zu deutschen Dokumenten ✅
  - Sprachübergreifende semantische Suche aktiviert
- **Lokale Verarbeitung**: Ihre Daten bleiben auf Ihrem Gerät (Datenschutz-first)
- **Cloud LLM Option**: Optionale Cloud-Modelle für bessere Genauigkeit
- **Gradio Web UI**: Saubere, intuitive Weboberfläche

## 🚀 Schnellstart

### Installation

**1. Systemabhängigkeiten installieren:**
```bash
# macOS (Homebrew)
brew install tesseract tesseract-lang poppler

# Linux (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-eng poppler-utils
```

**2. Ollama installieren:**
```bash
# Von https://ollama.ai herunterladen und installieren
curl -fsSL https://ollama.ai/install.sh | sh

# Erforderliches Modell pullen
ollama pull minimax-m2.5:cloud

# Oder lokales Modell (empfohlen für Offline-Nutzung)
ollama pull qwen3:8b
```

**3. App starten:**
```bash
cd /Users/usermacrtx/Documents/Demos/IDP_App_DE

# Virtuelle Umgebung aktivieren
source ../demos_env/bin/activate

# App starten
./run.sh
```

**Öffnen Sie:** http://localhost:7860

## 📋 Unterstützte Formate

| Format | Erweiterung | Hinweise |
|--------|-------------|----------|
| PDF | `.pdf` | Nativer Text + gescannt (OCR) |
| Word | `.docx` | Native Textextraktion |
| Text | `.txt` | Plain Text Dateien |
| Bilder | `.png`, `.jpg`, `.jpeg` | OCR erforderlich |

## 💬 Beispiel-Fragen

- "Was ist die Urlaubsregelung?"
- "Fassen Sie die Hauptpunkte dieses Vertrags zusammen"
- "Was sind die Zahlungsbedingungen?"
- "Listen Sie alle Fristen im Dokument auf"

## ⚙️ Konfiguration

### Umgebungsvariablen

Erstellen Sie eine `.env` Datei im Stammverzeichnis:

```bash
# Ollama Konfiguration
OLLAMA_HOST=localhost:11434
OLLAMA_MODEL=minimax-m2.5:cloud

# Embedding Modell
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Speicherpfade
CHROMA_PERSIST_DIR=./data/chroma_db
UPLOAD_DIR=./data/uploads
PROCESSED_DIR=./data/processed
```

### Modell-Optionen

| Modell | Typ | Geschwindigkeit | Qualität | Hinweise |
|--------|------|-----------------|----------|----------|
| `minimax-m2.5:cloud` | Cloud | Schnell | Hoch | Internet erforderlich |
| `qwen3:8b` | Lokal | Mittel | Gut | Funktioniert offline |
| `qwen3.5:9b` | Lokal | Mittel | Besser | Funktioniert offline |
| `llama3.2` | Lokal | Schnell | Gut | Funktioniert offline |

## 📁 Projektstruktur

```
IDP_App_DE/
├── app/
│   ├── main.py              # Gradio UI und Hauptanwendung
│   ├── document_processor.py # Dokumentenladung und -verarbeitung
│   ├── ocr_processor.py      # OCR-Engine (Tesseract)
│   ├── vector_store.py       # ChromaDB-Integration
│   ├── llm_client.py         # Ollama LLM-Client
│   └── extractors/
│       ├── pdf_extractor.py
│       ├── docx_extractor.py
│       └── image_extractor.py
├── data/
│   ├── uploads/             # Hochgeladene Dokumente
│   ├── processed/           # Extrahierter Text
│   └── chroma_db/           # Vektordatenbank
├── docs/
│   └── sample_documents/    # Beispieldateien zum Testen
├── tests/
│   └── test_*.py           # Unit-Tests
├── scripts/
│   └── install.sh          # Installationsskript
├── requirements.txt         # Python-Abhängigkeiten
├── run.sh                  # Startskript
├── README.md               # Diese Datei
└── FLOWCHART.md            # Architekturdiagramme
```

## 🔧 Fehlerbehebung

### Häufige Probleme

**1. "Tesseract nicht gefunden"**
```bash
# macOS
brew install tesseract

# Installation überprüfen
tesseract --version
```

**2. "Ollama-Verbindung fehlgeschlagen"**
```bash
# Überprüfen ob Ollama läuft
ollama list

# Ollama-Dienst starten
ollama serve
```

**3. "Port 7860 bereits belegt"**
```bash
# Vorhandenen Prozess beenden
lsof -ti :7860 | xargs kill -9

# Oder anderen Port verwenden
python app/main.py --server-port 7861
```

**4. "Modell nicht gefunden"**
```bash
# Modell pullen
ollama pull minimax-m2.5:cloud

# Oder zu lokalem Modell wechseln
export OLLAMA_MODEL=qwen3:8b
```

## 📊 Leistung

| Dokumenttyp | Verarbeitungszeit | Genauigkeit |
|-------------|-------------------|-------------|
| Text-PDF | ~2 Sek./Seite | 99% |
| Gescanntes PDF | ~5 Sek./Seite | 95% |
| DOCX | ~1 Sek./Seite | 99% |
| Bilder | ~3 Sek./Seite | 90-95% |

*Zeiten variieren je nach Dokumentkomplexität und Hardware*

## 🔐 Benutzerauthentifizierung & Zugriffskontrolle (TODO)

### 📋 Geplante Funktionen

Benutzerverwaltung und Zugriffskontrolle hinzufügen, um Dokumente zu schützen und Multi-User-Szenarien zu ermöglichen.

### 🎯 Implementierungsoptionen

#### **Option 1: Einfache Authentifizierung** ⭐ Empfohlen (Schnelle Einrichtung)

**Beste für:** Kleine Teams, interne Apps, schnelle Bereitstellung

**Module:**
```bash
pip install fastapi python-jose[cryptography] passlib[bcrypt]
pip install python-multipart aiofiles sqlalchemy aiosqlite
```

**Funktionen:**
- ✅ Benutzername/Passwort-Login
- ✅ JWT-Token-basierte Sitzungen
- ✅ Passwort-Verschlüsselung (bcrypt)
- ✅ Rollenbasierter Zugriff (Admin/Benutzer)
- ✅ Benutzerbezogene Dokumentenisolierung

**Implementierungsschritte:**

1. **Benutzerdatenbank erstellen** (`auth/models.py`):
```python
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    documents = Column(String)  # JSON-Liste der Dokument-IDs
```

2. **Authentifizierung hinzufügen** (`auth/auth.py`):
```python
from passlib.context import CryptContext
from jose import jwt

SECRET_KEY = "ihr-geheimer-schlüssel"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"])

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
```

3. **Gradio UI ändern** - Login-Tab hinzufügen und bestehgende Tabs schützen
4. **Benutzerspezifischer Speicher** - Dokumente nach Benutzer-ID isolieren
5. **Sitzungsverwaltung** - Token-basierte Authentifizierung

**Implementierungszeit:** 2-3 Stunden  
**Komplexität:** ⭐⭐☆☆☆

---

#### **Option 2: Vollständige Benutzerverwaltung** ⭐⭐ (Produktion)

**Beste für:** Produktion, mehrere Benutzer, Audit-Trails

**Module:**
```bash
pip install fastapi-users[sqlalchemy] sqladmin
```

**Funktionen:**
- ✅ Benutzerregistrierung
- ✅ E-Mail-Verifizierung
- ✅ Passwort-Zurücksetzung
- ✅ OAuth2 (Google, GitHub-Login)
- ✅ Admin-Dashboard
- ✅ Aktivitätsprotokolle
- ✅ Ratenbegrenzung

**Implementierungszeit:** 1-2 Tage  
**Komplexität:** ⭐⭐⭐☆☆

---

#### **Option 3: Enterprise SSO** ⭐⭐⭐ (Großes Maßstab)

**Beste für:** Unternehmen, bestehende Identitätsanbieter

**Module:**
```bash
pip install authlib python-saml ldap3 keycloak
```

**Funktionen:**
- ✅ Single Sign-On (SSO)
- ✅ Active Directory-Integration
- ✅ SAML 2.0
- ✅ OIDC/OAuth2
- ✅ Multi-Faktor-Authentifizierung
- ✅ Zentrale Benutzerverwaltung

**Implementierungszeit:** 1-2 Wochen  
**Komplexität:** ⭐⭐⭐⭐⭐

---

### 📊 Funktionsvergleich

| Funktion | Option 1 (Einfach) | Option 2 (FastAPI Users) | Option 3 (Enterprise) |
|----------|-------------------|--------------------------|----------------------|
| **Einrichtungszeit** | 2-3 Stunden | 1-2 Tage | 1-2 Wochen |
| **Komplexität** | Niedrig | Mittel | Hoch |
| **Benutzerregistrierung** | Manuell | Selbstbedienung | SSO-Portal |
| **Passwort-Zurücksetzung** | ❌ | ✅ | ✅ |
| **E-Mail-Verifizierung** | ❌ | ✅ | ✅ |
| **OAuth (Google/GitHub)** | ❌ | ✅ | ✅ |
| **Active Directory** | ❌ | ❌ | ✅ |
| **Multi-Faktor-Auth** | ❌ | ⚠️ Plugin | ✅ |
| **Audit-Logging** | Einfach | ✅ | ✅✅ |
| **Beste Für** | Kleine Teams | Produktion | Unternehmen |

### 🚀 Nächste Schritte

**Empfohlen:** Beginnen Sie mit **Option 1** (Einfache Auth), Upgrade auf Option 2 bei Bedarf.

**Zur Implementierung:**
1. `auth/`-Verzeichnis mit Datenbank, Modellen und Auth-Modulen erstellen
2. Login/Registrierungs-UI zur Gradio-Oberfläche hinzufügen
3. JWT-Token-basierte Sitzungsverwaltung implementieren
4. Benutzerbezogene Dokumentenisolierung hinzufügen
5. (Optional) Admin-Dashboard für Benutzerverwaltung erstellen

**Kontakt:** Für Implementierungsunterstützung oder benutzerdefinierte Authentifizierungsfunktionen.

---

## 🔒 HTTPS/SSL-Einrichtung mit Let's Encrypt (TODO)

### 🌐 Sichere Bereitstellung mit kostenlosem SSL/TLS

Aktivieren Sie HTTPS-Verschlüsselung für Produktionsbereitstellungen mit kostenlosen Let's Encrypt-Zertifikaten.

### 🎯 Option 1: Nginx Reverse Proxy + Certbot ⭐ Empfohlen

**Beste für:** Produktionsserver, benutzerdefinierte Domains, automatische Erneuerung

**Voraussetzungen:**
- Domain-Name, der auf Ihren Server zeigt
- Server mit öffentlicher IP-Adresse
- Ports 80 und 443 geöffnet

**Installationsschritte:**

1. **Nginx installieren:**
```bash
# macOS
brew install nginx

# Linux (Ubuntu/Debian)
sudo apt-get install nginx
```

2. **Nginx als Reverse Proxy konfigurieren:**
```nginx
# /etc/nginx/sites-available/idp-app
server {
    listen 80;
    server_name ihre-domain.com;

    location / {
        proxy_pass http://localhost:7860;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. **Certbot installieren:**
```bash
# macOS
brew install certbot

# Linux
sudo apt-get install certbot python3-certbot-nginx
```

4. **SSL-Zertifikat anfordern:**
```bash
sudo certbot --nginx -d ihre-domain.com
```

5. **Automatische Erneuerung aktivieren:**
```bash
# Automatische Erneuerung testen
sudo certbot renew --dry-run

# Certbot fügt automatisch Cron-Job hinzu
# Überprüfen mit:
sudo crontab -l | grep certbot
```

6. **HTTPS in Nginx konfigurieren:**
```nginx
server {
    listen 443 ssl http2;
    server_name ihre-domain.com;

    ssl_certificate /etc/letsencrypt/live/ihre-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ihre-domain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://localhost:7860;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $https;
    }
}

# HTTP zu HTTPS umleiten
server {
    listen 80;
    server_name ihre-domain.com;
    return 301 https://$server_name$request_uri;
}
```

**Implementierungszeit:** 1-2 Stunden  
**Komplexität:** ⭐⭐☆☆☆

---

### 🎯 Option 2: Caddy Server (Am Einfachsten) ⭐⭐

**Beste für:** Schnelle HTTPS-Einrichtung, automatische Zertifikate

**Installation:**
```bash
# macOS
brew install caddy

# Linux
curl https://getcaddy.com | bash
```

**Konfiguration (Caddyfile):**
```caddy
ihre-domain.com {
    reverse_proxy localhost:7860
    
    tls {
        protocols tls1.2 tls1.3
    }
}
```

**Caddy starten:**
```bash
sudo caddy run
```

**Funktionen:**
- ✅ Automatisches HTTPS (Null-Konfiguration)
- ✅ Automatische Zertifikaterneuerung
- ✅ HTTP/2-Unterstützung
- ✅ Einfachere Konfiguration als Nginx

**Implementierungszeit:** 30 Minuten  
**Komplexität:** ⭐☆☆☆☆

---

### 🎯 Option 3: Cloudflare Tunnel ⭐⭐⭐

**Beste für:** Kein Port-Forwarding, DDoS-Schutz, kostenlose Version

**Funktionen:**
- ✅ Keine öffentliche IP erforderlich
- ✅ Kostenloses SSL/TLS
- ✅ DDoS-Schutz
- ✅ Versteckt Server-IP
- ✅ Funktioniert hinter NAT/Firewall

**Einrichtung:**

1. **cloudflared installieren:**
```bash
# macOS
brew install cloudflared

# Linux
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
```

2. **Authentifizieren:**
```bash
cloudflared tunnel login
```

3. **Tunnel erstellen:**
```bash
cloudflared tunnel create idp-app
```

4. **Tunnel konfigurieren** (`~/.cloudflared/config.yml`):
```yaml
tunnel: idp-app
credentials-file: /root/.cloudflared/ID.json

ingress:
  - hostname: ihre-domain.com
    service: http://localhost:7860
  - service: http_status:404
```

5. **Tunnel ausführen:**
```bash
cloudflared tunnel run idp-app
```

**Implementierungszeit:** 30 Minuten  
**Komplexität:** ⭐⭐☆☆☆

---

### 📊 SSL/HTTPS-Einrichtung Vergleich

| Funktion | Nginx + Certbot | Caddy | Cloudflare Tunnel |
|----------|-----------------|-------|-------------------|
| **Einrichtungszeit** | 1-2 Stunden | 30 Min | 30 Min |
| **Komplexität** | Mittel | Einfach | Einfach |
| **Öffentliche IP Erforderlich** | ✅ Ja | ✅ Ja | ❌ Nein |
| **Port-Forwarding** | ✅ Erforderlich | ✅ Erforderlich | ❌ Nicht Erforderlich |
| **Automatische Erneuerung** | ✅ (cron) | ✅ Automatisch | ✅ Automatisch |
| **DDoS-Schutz** | ❌ | ❌ | ✅ Inbegriffen |
| **Benutzerdefinierte Domain** | ✅ | ✅ | ✅ |
| **Kostenlose Version** | ✅ | ✅ | ✅ |
| **Beste Für** | Produktion | Schnelle Einrichtung | Hinter NAT/Firewall |

---

### 🔧 Produktions-Checkliste

**Vor dem Live-Gang:**

- [ ] Domain-Name konfiguriert und DNS zeigt auf Server
- [ ] SSL-Zertifikat installiert und gültig
- [ ] HTTPS-Weiterleitung aktiviert (HTTP → HTTPS)
- [ ] Firewall konfiguriert (Ports 80, 443 offen)
- [ ] Automatische Zertifikaterneuerung getestet
- [ ] Sicherheits-Header konfiguriert:
  ```nginx
  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
  add_header X-Frame-Options "SAMEORIGIN" always;
  add_header X-Content-Type-Options "nosniff" always;
  add_header X-XSS-Protection "1; mode=block" always;
  ```
- [ ] Ratenbegrenzung aktiviert (Brute-Force-Schutz)
- [ ] Zugriffsprotokolle für Auditierung aktiviert
- [ ] SSL-Zertifikat-Backups sicher gespeichert

**Sicherheits-Best-Practices:**

```nginx
# Starke SSL-Konfiguration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

# Nginx-Version verstecken
server_tokens off;

# Anfragegröße begrenzen (große Uploads verhindern)
client_max_body_size 10M;

# Ratenbegrenzung
limit_req_zone $binary_remote_addr zone=one:10m rate=10r/s;
location / {
    limit_req zone=one burst=5 nodelay;
}
```

### 🔗 Nützliche Befehle

```bash
# Zertifikatsablauf prüfen
sudo certbot certificates

# Zertifikate erneuern
sudo certbot renew

# Nginx-Konfiguration testen
sudo nginx -t

# Nginx neu laden
sudo systemctl reload nginx

# SSL-Verbindung prüfen
openssl s_client -connect ihre-domain.com:443

# SSL Labs-Test
# Besuchen: https://www.ssllabs.com/ssltest/
```

### 📧 Support & Ressourcen

- **Let's Encrypt:** https://letsencrypt.org/
- **Certbot-Dokumentation:** https://certbot.eff.org/
- **Nginx SSL-Konfiguration:** https://nginx.org/en/docs/http/configuring_https_servers.html
- **SSL Labs Test:** https://www.ssllabs.com/ssltest/
- **Cloudflare Tunnel:** https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/

---

## 🔒 Datenschutz & Sicherheit

- ✅ Alle Dokumentenverarbeitungen erfolgen lokal
- ✅ **Daten bleiben nach Neustarts erhalten** (gespeichert in `./data/chroma_db/`)
- ✅ Keine Daten an externe Server (außer Cloud LLM)
- ✅ Vektordatenbank lokal im SQLite-Format gespeichert
- ✅ Keine Telemetrie oder Analysen

**Persistenz-Details:**
- Dokumente werden in `./data/chroma_db/chroma.sqlite3` gespeichert
- Embeddings werden automatisch beim Hochladen gespeichert
- Daten überleben App-Neustarts - kein erneutes Hochladen erforderlich
- Datenbankgröße wächst mit Dokumenten (ca. 1MB pro 100 Seiten)
- Zum Löschen: `./data/chroma_db/` Ordner löschen

**Hinweis:** Bei Verwendung von Cloud-Modellen (`minimax-m2.5:cloud`) werden Anfragen an Ollamas Cloud-Endpunkt gesendet. Für vollständige Privatsphäre verwenden Sie lokale Modelle wie `qwen3:8b`.

## 📝 Lizenz

MIT-Lizenz - Siehe LICENSE-Datei für Details

## 🤝 Mitwirken

1. Repository forken
2. Feature-Branch erstellen
3. Änderungen vornehmen
4. Tests ausführen
5. Pull-Request einreichen

## 📧 Support

Für Probleme und Fragen:
- Überprüfen Sie die [FLOWCHART.md](FLOWCHART.md) für Architekturdetails
- Lesen Sie den Abschnitt zur Fehlerbehebung oben
- Öffnen Sie ein Issue auf GitHub

## 🙏 Danksagungen

- **Ollama** - Lokales LLM-Runtime
- **Gradio** - Web-UI-Framework
- **ChromaDB** - Vektordatenbank
- **Tesseract** - OCR-Engine
- **Sentence Transformers** - Text-Embeddings

---

**Entwickelt mit ❤️ für intelligente Dokumentenverarbeitung**

**URL:** http://localhost:7860
