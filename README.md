# Ygam - E2E Encrypted Instant Messaging Server

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.1.2-green.svg)

**Ygam** is a privacy-focused open source instant messaging server. The server acts solely as a gateway: all messages are end-to-end encrypted and **automatically deleted** once delivered. Host your own zero-knowledge messaging infrastructure.

## 🚀 Quick Start

### Docker Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/ygam.git
cd ygam

# Configure environment variables
cp .env.example .env
# Edit .env with your configuration

# Launch with Docker Compose
docker-compose up -d
```

Your API will be available at `http://localhost:5000`

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
cp .env.example .env
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
- **Hashed tokens**: JWTs stored hashed in database
- **Instant revocation**: Account deactivation at any time
- **Argon2 hashing**: State-of-the-art password hashing
- **Device tracking**: Per-device session management
- **Audit logs**: Complete action traceability

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

### Data Models

- **User**: User accounts with Argon2 hashing
- **Role**: RBAC system
- **Message**: Encrypted messages (deleted after delivery)
- **Token**: JWT management with revocation
- **Log**: Complete audit trail

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | *(required)* |
| `DB_HOST` | MySQL host | localhost |
| `DB_PORT` | MySQL port | 3306 |
| `DB_NAME` | Database name | ygam |
| `DB_USER` | MySQL user | ygam_admin |
| `DB_PASSWORD` | MySQL password | *(required)* |

### JWT Customization

Modify token lifetimes in `config.py`:
```python
ACCESS_TOKEN_EXPIRY = 10   # minutes
REFRESH_TOKEN_EXPIRY = 90  # days
```

## 🛡️ Security

### Implemented Best Practices

✅ End-to-end encryption (E2E)
✅ Argon2 password hashing
✅ Hashed JWT storage
✅ Short-lived access tokens (10 min)
✅ Message auto-deletion
✅ Complete audit logging
✅ Input validation and sanitization

### Production Deployment Recommendations

- Use **HTTPS** in production (Let's Encrypt)
- Configure a **firewall** (ufw, iptables)
- Change **all default keys and passwords**
- Use a **reverse proxy** (Nginx, Caddy)
- Enable **monitoring and alerts**
- Perform **regular backups**

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please follow PEP 8 style guidelines and include tests for new features.

## 📋 Roadmap

- [ ] Complete REST API (auth, messaging routes)
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Reference client implementation
- [ ] WebSocket support for real-time messaging
- [ ] Push notifications
- [ ] Multi-device support
- [ ] Admin dashboard
- [ ] Group messaging
- [ ] E2E encrypted audio/video calls

## 📄 License

This project is licensed under the **MIT License**. See `LICENSE` file for details.

---

**⚠️ Disclaimer**: This software is provided "as is", without warranty of any kind. While we've taken care to secure the application, no system is completely infallible. Use at your own risk and audit the code before production deployment.

---

Made with privacy in mind
