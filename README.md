# OJS Multi-Site Docker Deployment

Deploy multiple Open Journal Systems (OJS) 3.5+ instances on a single VPS using Docker Compose, MariaDB, and Traefik v2/v3 as a reverse proxy with automatic SSL.

## Features

- **Multi-Site Support:** Host multiple journals on different domains/subdomains (e.g., `ejournal1.example.com`, `ejournal2.example.org`) on one server.
- **Automated SSL:** Traefik handles Let's Encrypt certificates automatically.
- **Isolation:** Each OJS instance runs in its own container with a dedicated MariaDB database.
- **Scripted Deployment:** `deploy.py` automates the setup of new instances from a template.
- **OJS 3.5+ Compatible:** Uses MariaDB 12.1.x and PHP 8.x optimizations.

---

## Prerequisites

- Docker & Docker Compose installed
- A domain name pointing to your VPS IP
- Port 80 and 443 open

---

## 1. Initial Setup

### Create External Network

Create the network that Traefik and all OJS instances will use to communicate:

```bash
docker network create intranet
```

### Start Traefik Proxy

The `traefik` directory contains the reverse proxy configuration.

1.  Navigate to the directory:
    ```bash
    cd traefik
    ```
2.  Configure your email for SSL certificates:
    ```bash
    vim .env
    # Set ACME_EMAIL=your-email@example.com
    ```
3.  Create the certificate storage file with secure permissions:
    ```bash
    touch acme.json
    chmod 600 acme.json
    ```
4.  Start Traefik:
    ```bash
    docker compose up -d
    ```

---

## 2. Deploying a New Journal

Use the `deploy.sh` script to create a fresh OJS instance.

**Usage:**

```bash
./deploy.py <domain> [locale] [email]
```

**Example:**
To deploy `ejournal.example.com`:

```bash
./deploy.py journal.example.com
```

**What the script does:**

1.  Creates a new directory `ejournal` (extracted from subdomain).
2.  Copies the `journal/` template to `ejournal/`.
3.  Configures `ejournal/.env` and `ejournal/volumes/config/config.inc.php` with the domain.
4.  Renames Docker services (e.g., `journal-ejournal`, `db-ejournal`) to prevent name collisions.
5.  Sets correct permissions (`www-data` for files, `mysql` for database).

---

## 3. Starting the Journal

After running the deployment script:

1.  Enter the new directory:
    ```bash
    cd ejournal
    ```
2.  Start the containers:
    ```bash
    docker compose up -d
    ```
3.  Access your site at `https://ejournal.example.com`.

---

## Directory Structure

```
├── deploy.sh              # Main deployment script
├── traefik/
│   ├── compose.yml        # Traefik reverse proxy configuration
│   ├── .env               # Traefik environment variables
│   └── acme.json          # SSL certificates (generated)
│
├── journal/               # TEMPLATE DIRECTORY (Do not run directly)
│   ├── compose.yml        # Template Compose file
│   ├── .env               # Template Environment file
│   └── volumes/           # Template Config/Data
│
└── [subdomain]/           # GENERATED INSTANCES (e.g., ejournal)
    ├── compose.yml        # Configured OJS + MariaDB
    ├── .env               # Configured environment variables
    └── volumes/           # Persistent data (db, files, public)
```

---

## Troubleshooting

### Permissions Issues

If you encounter write errors (e.g., cannot upload files), fixing permissions usually resolves it. The deployment script attempts this automatically, but you can run it manually:

```bash
# In the site directory
sudo chown -R 33:33 volumes/files volumes/public volumes/config
sudo chown -R 999:999 volumes/db
```

### Database Errors

- **OJS 3.5+ requires MariaDB/MySQL.** Do not use PostgreSQL with OJS 3.5.
- If you see `Connection refused`, ensure the `db` service is running and `DB_HOST` in `.env` matches the service name in `compose.yml`.

### SSL Issues

- Check Traefik logs: `docker logs traefik`
- Ensure your domain points to the server IP.
- Ensure `acme.json` has `600` permissions.

---

## License

Project structure and scripts licensed under MIT. OJS is licensed under GNU GPL v3.
