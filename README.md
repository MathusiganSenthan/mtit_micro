# Bookstore Microservices

A FastAPI microservices project with 6 independent services and a single API gateway.

---

## Architecture

```
Client
  └── API Gateway         :8000   (routes all requests)
        ├── auth-service  :8001   (register, login, JWT)
        ├── user-service  :8002   (user profiles)
        ├── product-service :8003 (book catalog)
        ├── order-service :8004   (place & track orders)
  ├── notification-service :8005 (email alerts, logs)
  └── feedback-service :8006 (ratings and reviews)
```

Each service has its own database and shares only the `SECRET_KEY` for JWT verification.

---

## Services

| Service               | Port | Database        | Responsibility                        |
|-----------------------|------|-----------------|---------------------------------------|
| api-gateway           | 8000 | —               | Reverse proxy, single entry point     |
| auth-service          | 8001 | auth_db         | Register, login, JWT issue/refresh    |
| user-service          | 8002 | user_db         | User profiles (CRUD)                  |
| product-service       | 8003 | product_db      | Book catalog, stock management        |
| order-service         | 8004 | order_db        | Place orders, status transitions      |
| notification-service  | 8005 | notification_db | Email notifications, audit log        |
| feedback-service      | 8006 | feedback_db     | Ratings and product feedback          |

---

## Prerequisites

- Python 3.11+
- PostgreSQL running locally (optional for local demo)

---

## Database Setup

### Option A: PostgreSQL (production-like)

Create one database per service in PostgreSQL:

```sql
CREATE DATABASE auth_db;
CREATE DATABASE user_db;
CREATE DATABASE product_db;
CREATE DATABASE order_db;
CREATE DATABASE notification_db;
CREATE DATABASE feedback_db;
```

### Option B: SQLite (quick local setup)

For a laptop demo, each service can use local SQLite without installing PostgreSQL.
This repository already supports SQLite URLs like:

```env
DATABASE_URL=sqlite:///./auth_db.db
```

---

## Environment Variables

Each service has a `.env` file. You can copy each `.env.example` and adjust values:

```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/<service_db>
SECRET_KEY=your-long-random-secret-same-across-all-services
```

> **Important:** `SECRET_KEY` must be the **same value** in every service —
> it is used by all services to verify JWTs issued by auth-service.

---

## Running All Services

Open a terminal for each service and run:

```bash
# 1. Auth Service
cd auth-service
pip install -r requirements.txt
uvicorn app.main:app --port 8001 --reload

# 2. User Service
cd user-service
pip install -r requirements.txt
uvicorn app.main:app --port 8002 --reload

# 3. Product Service
cd product-service
pip install -r requirements.txt
uvicorn app.main:app --port 8003 --reload

# 4. Order Service
cd order-service
pip install -r requirements.txt
uvicorn app.main:app --port 8004 --reload

# 5. Notification Service
cd notification-service
pip install -r requirements.txt
uvicorn app.main:app --port 8005 --reload

# 6. Feedback Service
cd feedback-service
pip install -r requirements.txt
uvicorn app.main:app --port 8006 --reload

# 7. API Gateway (start last)
cd api-gateway
pip install -r requirements.txt
uvicorn app.main:app --port 8000 --reload
```

### Windows one-command start/stop

```powershell
./scripts/run-all.ps1
./scripts/stop-all.ps1
```

Tables are created automatically on first startup via `Base.metadata.create_all()`.

---

## Gateway Utility Endpoints

These endpoints help with assignment demo screenshots and environment checks.

| Method | Path                 | Description                                      |
|--------|----------------------|--------------------------------------------------|
| GET    | /gateway/services    | Shows registered service prefixes and base URLs  |
| GET    | /gateway/health      | Aggregated health status across all services     |
| GET    | /gateway/docs        | Direct docs and gateway docs URLs per service    |

---

## API Reference

All requests go through **`http://localhost:8000`**.

### Auth

| Method | Path                  | Auth | Description           |
|--------|-----------------------|------|-----------------------|
| POST   | /auth/register        | No   | Create account        |
| POST   | /auth/login           | No   | Login, get tokens     |
| POST   | /auth/refresh         | No   | Refresh access token  |

**Register:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret123"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret123"}'
```

---

### Users

| Method | Path           | Auth | Description            |
|--------|----------------|------|------------------------|
| POST   | /users/me      | Yes  | Create profile         |
| GET    | /users/me      | Yes  | Get my profile         |
| PATCH  | /users/me      | Yes  | Update my profile      |
| DELETE | /users/me      | Yes  | Delete my profile      |
| GET    | /users/{id}    | No   | Get profile by user ID |

```bash
curl -X POST http://localhost:8000/users/me \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Jane Doe", "phone": "+94771234567", "address": "Colombo, Sri Lanka"}'
```

---

### Products

| Method | Path                         | Auth | Description         |
|--------|------------------------------|------|---------------------|
| GET    | /products                    | No   | List books (paged)  |
| GET    | /products/{id}               | No   | Get one book        |
| POST   | /products                    | Yes  | Add a book          |
| PATCH  | /products/{id}               | Yes  | Update a book       |
| PATCH  | /products/{id}/stock         | Yes  | Adjust stock        |
| DELETE | /products/{id}               | Yes  | Deactivate a book   |

```bash
# List with search + category filter
curl "http://localhost:8000/products?search=python&category=technology&page=1&page_size=10"

# Add a book
curl -X POST http://localhost:8000/products \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Clean Code",
    "author": "Robert C. Martin",
    "isbn": "9780132350884",
    "price": 29.99,
    "stock": 50,
    "category": "technology"
  }'
```

---

### Orders

| Method | Path                         | Auth | Description              |
|--------|------------------------------|------|--------------------------|
| POST   | /orders                      | Yes  | Place an order           |
| GET    | /orders                      | Yes  | List my orders (paged)   |
| GET    | /orders/{id}                 | Yes  | Get one order            |
| PATCH  | /orders/{id}/status          | Yes  | Update order status      |

**Status transitions:**
```
pending → confirmed → shipped → delivered
pending → cancelled
confirmed → cancelled
```

```bash
curl -X POST http://localhost:8000/orders \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"product_id": "<product_uuid>", "quantity": 2}
    ],
    "shipping_address": "123 Main St, Colombo"
  }'
```

---

### Notifications

| Method | Path                         | Auth | Description                      |
|--------|------------------------------|------|----------------------------------|
| GET    | /notifications/me            | Yes  | List my notifications            |
| GET    | /notifications/{id}          | Yes  | Get one notification             |

> `/notifications/send` is an **internal** endpoint called by order-service.
> It is not meant to be exposed through the gateway.

---

## Inter-Service Communication

```
order-service
  ├── GET  product-service/products/{id}      — validate product & price
  ├── PATCH product-service/products/{id}/stock — deduct stock on order
  └── POST notification-service/notifications/send — trigger email
```

All inter-service calls are synchronous HTTP via `httpx`.

---

## Project Structure

```
bookstore/
├── api-gateway/
│   ├── app/
│   │   ├── main.py
│   │   └── routes.py
│   ├── .env
│   └── requirements.txt
│
├── auth-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/auth.py
│   │   ├── models/user.py
│   │   ├── schemas/user.py
│   │   ├── services/auth.py
│   │   ├── core/{config,database,security}.py
│   │   └── dependencies.py
│   ├── .env
│   └── requirements.txt
│
├── user-service/          # same structure
├── product-service/       # same structure
├── order-service/         # same structure
├── notification-service/  # same structure + core/mailer.py
└── README.md
```

---

## Interactive API Docs

Each service exposes Swagger UI at `/docs`:

| Service              | Docs URL                          |
|----------------------|-----------------------------------|
| API Gateway          | http://localhost:8000/docs        |
| Auth Service         | http://localhost:8001/docs        |
| User Service         | http://localhost:8002/docs        |
| Product Service      | http://localhost:8003/docs        |
| Order Service        | http://localhost:8004/docs        |
| Notification Service | http://localhost:8005/docs        |

---

## Production Notes

- Replace `Base.metadata.create_all()` with **Alembic** migrations per service.
- Use a proper secrets manager (AWS SSM, Vault) instead of `.env` files.
- Add an API key or internal mTLS to protect inter-service endpoints like `/notifications/send`.
- Consider moving to an async message queue (Redis Streams, RabbitMQ) for notifications to decouple services.
- Add rate limiting at the gateway level (e.g. `slowapi`).