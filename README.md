# Ygam - E2E Encrypted Instant Messaging Server

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.1.2-green.svg)
![Tests](https://github.com/your-username/ygam/actions/workflows/tests.yml/badge.svg)
![Coverage](https://img.shields.io/codecov/c/github/your-username/ygam)
![CodeQL](https://github.com/your-username/ygam/actions/workflows/codeql.yml/badge.svg)
![Docker](https://github.com/your-username/ygam/actions/workflows/docker-build.yml/badge.svg)

**Ygam** is a privacy-focused open source instant messaging server. The server acts solely as a gateway: all messages are end-to-end encrypted and **automatically deleted** once delivered. Host your own zero-knowledge messaging infrastructure.

## 🚀 Quick Start

### Docker Installation (Recommended)

**Deploy your own Ygam server in 3 commands:**

```bash
# 1. Clone and navigate
git clone https://github.com/your-username/ygam.git && cd ygam

# 2. Configure environment (edit SECRET_KEY and passwords)
cp .env.exemple .env && nano .env

# 3. Launch all services (Flask + MySQL + Redis)
docker-compose up -d
```

**Your API is now running at `http://localhost:5000`**

Check health: `curl http://localhost:5000/health`

View logs: `docker-compose logs -f web`

Stop services: `docker-compose down`

### Manual Installation

**Prerequisites:** Python 3.8+, MySQL 8.0+

```bash
# Clone and setup
git clone https://github.com/your-username/ygam.git
cd ygam
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Configure environment
cp .env.exemple .env
# Edit .env with your database credentials

# Initialize database
mysql -u root -p
CREATE DATABASE ygam CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ygam_admin'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON ygam.* TO 'ygam_admin'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Run the server
python app.py
```

## 🎯 Core Philosophy

- **Zero Knowledge**: Server cannot read your messages
- **Ephemeral**: Encrypted messages deleted immediately after delivery
- **Self-Hosted**: Run your own messaging infrastructure
- **Open Source**: Transparent and auditable code

## ✨ Key Features

### 🔐 End-to-End Encryption
- Messages encrypted client-side before transmission
- Server only sees encrypted data
- Only sender and recipient can decrypt messages

### 🗑️ Auto-Deletion
- Encrypted messages **automatically deleted** from database after delivery
- No persistent message history on server
- Maximum privacy protection

### 💾 Client-Side Encrypted Storage
- Messages stored in **encrypted local SQLite database** (client-side)
- Users control their own data
- History managed locally

### 🔑 Dual JWT System
Innovative authentication with two tokens:

- **Access Token**: 10-minute lifetime
  - Authenticates API requests
  - Minimizes exposure window

- **Refresh Token**: 90-day lifetime
  - Automatically renews Access Token
  - Users stay connected for 90 days

### 🛡️ Enhanced Security
- **Instant revocation**: Account deactivation at any time
- **Device tracking**: Per-device session management

## 📖 Architecture

### Message Flow

```
[Client A]              [Server]              [Client B]
    |                       |                       |
    | 1. E2E Encrypt        |                       |
    |---------------------> |                       |
    |                       | 2. Temp Storage       |
    |                       | 3. Notify             |
    |                       |---------------------> |
    |                       | 4. Retrieve           |
    |                       | <-------------------- |
    |                       | 5. AUTO-DELETE        |
    |                       |                       |
```

### JWT Authentication Flow

```
[Client]               [Server]
    |                      |
    | 1. Login             |
    |--------------------> |
    | 2. Access (10min)    |
    |    + Refresh (90d)   |
    | <------------------- |
    | 3. API Requests      |
    |    (Access Token)    |
    | <------------------> |
    | 4. Access Expired    |
    |    (after 10min)     |
    | 5. Refresh Token     |
    |--------------------> |
    | 6. New Access Token  |
    | <------------------- |
```

## 📋 Roadmap

### Phase 0 - Self-Hosting Ready (v0.1) 🐳 ✅ COMPLETED
**Goal:** Déploiement serveur en 2 minutes

- [X] Create `requirements.txt` with all dependencies
- [X] Create `Dockerfile` (Python + Flask + MySQL client)
- [X] Create `docker-compose.yml` (Flask + MySQL + Redis)
- [X] Create `.env.exemple` template
- [X] Database initialization script (auto-create tables)
- [X] Quick start documentation (3 commands max)
- [X] Fix security issue on `/` route (remove password exposure)

### Phase 1 - Server Gateway (v0.2) 🔐
**Goal:** Serveur passerelle fonctionnel avec auto-destruction

#### 1.1 - Database Models ✅ (Already done)
- [x] User model with Argon2 hashing
- [x] Role model (RBAC)
- [x] Message model (encrypted binary content)
- [x] Token model (JWT with device tracking)
- [x] Log model (audit trail)

#### 1.2 - Authentication System
**Dependencies:** `pip install Flask-JWT-Extended PyJWT`

- [X] Install Flask-JWT-Extended
- [X] POST `/auth/register` - User registration (hash password with Argon2)
- [X] POST `/auth/login` - Login with dual JWT:
  - Access token (10 min) - for API calls
  - Refresh token (90 days) - stored hashed in Token table
  - Return both tokens + device_id
- [X] POST `/auth/refresh` - Exchange refresh token for new access token
- [X] POST `/auth/logout` - Mark token as revoked in database
- [X] Create `@jwt_required` decorator - JWT validation middleware
  - Verify token signature
  - Check token not expired
  - Check token not revoked in database

**Testing:** Use curl/Postman to register → login → call protected route

#### 1.3 - Messaging Gateway API
**Prerequisites:** Authentication must work (need @token_required)

- [ ] POST `/messages/send` - Store encrypted message
  - Protected with `@token_required`
  - Accept `Content` as base64-encoded encrypted bytes
  - Store as LargeBinary in database
  - Return message_id
- [ ] GET `/messages/pending` - Retrieve pending messages
  - Protected with `@token_required`
  - Return only messages where `Id_user_receiver = current_user.id`
  - Return encrypted content as base64
- [ ] POST `/messages/ack/:id` - Mark as delivered → **REAL DELETE**
  - Protected with `@token_required`
  - Verify current_user is the receiver
  - **CRITICAL:** `db.session.delete(message)` (not just flag!)
  - Log deletion in Log table (audit trail)
- [ ] Background job: Auto-delete undelivered messages after 7 days
  - Use APScheduler (simple) or Celery (production)
  - Query messages where `Date < now() - 7 days AND Is_delivered = False`
  - Delete from database

**Testing:** Send message → retrieve → ack → verify it's deleted from DB

#### 1.4 - User Management
**Prerequisites:** Authentication must work

- [ ] GET `/users/me` - Current user profile (protected route)
- [ ] PATCH `/users/me` - Update profile (email, username)
- [ ] GET `/users/search?q=username` - Find users by username (for contacts)
  - Return id, username, email only (NOT password!)
- [ ] DELETE `/users/me` - Account deletion
  - Soft delete (set Is_activated = False) OR hard delete
  - Revoke all user tokens
  - Log action in audit trail

#### 1.5 - Security Hardening
- [ ] Install `Flask-Limiter` - Rate limiting
  - 5 requests/minute on /auth/login (prevent brute force)
  - 100 requests/hour on /messages/* (prevent spam)
- [ ] Install `marshmallow` or `pydantic` - Input validation
  - Validate all POST/PATCH request bodies
  - Sanitize inputs (prevent injection)
- [ ] Configure CORS (`Flask-CORS`)
  - Allow only your client origins
- [ ] Health check endpoint GET `/health`
  - Returns: `{"status": "ok", "db": "connected", "timestamp": "..."}`
  - Public (no auth required)

### Phase 2 - Real-Time Messaging (v0.5) ⚡
**Goal:** Messagerie instantanée temps réel

**WebSocket Server (Socket.IO)**
- [ ] Real-time message delivery (push to recipient)
- [ ] Online/offline status
- [ ] Typing indicators
- [ ] Message delivery confirmations
- [ ] Connection management (reconnect logic)

**Presence System**
- [ ] Last seen timestamp
- [ ] Online indicator
- [ ] Redis for presence caching

**Push Notifications (optional)**
- [ ] FCM/APNS integration for mobile
- [ ] Silent push for wake-up (encrypted payload)

### Phase 3 - Reference Client (v1.0) 📱
**Goal:** Client de référence avec stockage local chiffré

**Python CLI Client (Reference Implementation)**
- [ ] E2E encryption implementation (Signal Protocol or libsodium)
- [ ] Local SQLite database (encrypted with SQLCipher)
- [ ] Key exchange (Diffie-Hellman or pre-keys)
- [ ] Send/receive messages
- [ ] WebSocket connection handler
- [ ] Auto-sync on reconnect

**Client Features**
- [ ] Contact management
- [ ] Message history (local only)
- [ ] Search in local messages
- [ ] Export/import encrypted backup
- [ ] Multi-device key sync

**Documentation**
- [ ] Client SDK documentation
- [ ] E2E encryption protocol specification
- [ ] API usage examples

### Phase 4 - Group Messaging (v1.5) 👥
**Goal:** Conversations de groupe chiffrées

**Group Models & API**
- [ ] Group creation/deletion
- [ ] Add/remove members
- [ ] Admin/member roles
- [ ] Group metadata encryption

**Group E2E Encryption**
- [ ] Sender keys protocol (Signal groups style)
- [ ] Key rotation on member changes
- [ ] Server-side group message relay (still encrypted)

**Client Updates**
- [ ] Group UI in reference client
- [ ] Group key management
- [ ] Member list sync

### Phase 5 - Advanced Features (v2.0+) ✨

**Multi-Device Support**
- [ ] Device management UI
- [ ] Cross-device message sync (encrypted)
- [ ] QR code pairing (like WhatsApp Web)

**Rich Messaging**
- [ ] E2E encrypted file sharing (images, videos, docs)
- [ ] Voice messages (encrypted audio files)
- [ ] Message reactions & read receipts
- [ ] Message editing & deletion

**Admin Dashboard**
- [ ] Server metrics (users, messages/day, storage)
- [ ] User management (ban/suspend)
- [ ] Audit logs viewer
- [ ] Zero-knowledge guarantee: no message content visible

### Phase 6 - Cross-Platform GUI (v3.0+) 🚀
**Goal:** Une app web transformée en app desktop & mobile

> **Strategy:** Web-first approach - un seul codebase réutilisé partout

#### 6.1 - Web Application (Foundation)
- [ ] Choose framework (React, Vue, Svelte, or Vanilla JS)
- [ ] Web UI for messaging (chat interface)
- [ ] Authentication flow (login/register)
- [ ] Contact list & search
- [ ] Message encryption/decryption (client-side with libsodium.js)
- [ ] Local encrypted storage (IndexedDB with encryption)
- [ ] WebSocket connection for real-time messaging
- [ ] PWA support (Progressive Web App)

#### 6.2 - Desktop App with Electron
**Prerequisites:** Web app must work

- [ ] Electron wrapper configuration
- [ ] Native system tray integration
- [ ] Desktop notifications
- [ ] Auto-start on boot (optional)
- [ ] Auto-update mechanism
- [ ] Build scripts for Windows/Mac/Linux
- [ ] Code signing (for distribution)

#### 6.3 - Android App (Web-to-Mobile)
**Choose ONE approach:**

**Option A: Capacitor** (recommended - easier)
- [ ] Wrap web app with Capacitor
- [ ] Android native plugins (notifications, storage)
- [ ] APK build configuration
- [ ] Google Play Store preparation

**Option B: React Native** (if using React)
- [ ] Port web components to React Native
- [ ] Native Android modules
- [ ] Play Store deployment

**Common tasks:**
- [ ] Push notification integration (FCM)
- [ ] Contact book integration
- [ ] Background service for message sync
- [ ] App signing & distribution

#### 6.4 - Voice & Video Calls (Optional)
- [ ] WebRTC signaling server
- [ ] E2E encrypted voice calls (P2P)
- [ ] E2E encrypted video calls (P2P)
- [ ] Screen sharing (desktop only)

### Phase 7 - Federation (Future Vision) 🌐

- [ ] Server-to-server federation (like Matrix/XMPP)
- [ ] Cross-server messaging
- [ ] Distributed architecture
- [ ] ActivityPub integration (optional)

## 🧪 Testing & CI/CD

### Running Tests Locally

The project includes a comprehensive test suite with 130+ tests covering:
- Authentication & authorization
- JWT token management
- Database models & relationships
- Middleware & security
- API routes & endpoints

**Quick start:**
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Or use the convenience script
./run_tests.sh
./run_tests.sh coverage
```

See `tests/README.md` for detailed testing documentation.

### Continuous Integration

The project uses GitHub Actions for automated testing and quality checks:

#### 🔄 **Tests Workflow** (`.github/workflows/tests.yml`)
Runs on every push and pull request:
- **Multi-Python Testing**: Tests on Python 3.10, 3.11, and 3.12
- **Code Coverage**: Generates coverage reports (85-90% coverage)
- **Code Quality**: Black, isort, and flake8 linting
- **Security Scan**: Safety and Bandit security checks

#### 🔒 **CodeQL Analysis** (`.github/workflows/codeql.yml`)
Security scanning for vulnerabilities:
- Runs on push, PR, and weekly schedule
- Analyzes Python and JavaScript code
- Integrates with GitHub Security tab

#### 🐳 **Docker Build** (`.github/workflows/docker-build.yml`)
Automated Docker image building:
- Builds on push to main/master
- Pushes to Docker Hub (requires secrets)
- Vulnerability scanning with Trivy

### CI/CD Status

All workflows must pass before merging pull requests:
- ✅ Tests on Python 3.10, 3.11, 3.12
- ✅ Code coverage > 80%
- ✅ Security scans pass
- ✅ Code quality checks pass

### Setting Up CI/CD

1. **Update badge URLs** in README.md:
   - Replace `your-username` with your GitHub username
   - Replace `ygam` with your repository name

2. **Optional: Codecov integration**:
   - Sign up at [codecov.io](https://codecov.io)
   - Add repository
   - No token needed for public repos

3. **Optional: Docker Hub**:
   - Add secrets to GitHub repository:
     - `DOCKER_USERNAME`: Your Docker Hub username
     - `DOCKER_PASSWORD`: Docker Hub access token

4. **Branch protection** (recommended):
   ```
   Settings → Branches → Add rule
   ✓ Require status checks to pass
   ✓ Require branches to be up to date
   Select: test, coverage, lint, security
   ```

## 📄 License

This project is licensed under the **MIT License**. See `LICENSE` file for details.

---

**⚠️ Disclaimer**: This software is provided "as is", without warranty of any kind. While we've taken care to secure the application, no system is completely infallible. Use at your own risk and audit the code before production deployment.

---

Made with privacy in mind
