# Final Integrated University Web

One Flask/Python + MySQL application. University Web remains the architecture/security foundation; ResidenceHub supplies marketplace business behavior.

## Start
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python migrate_database.py
python import_supplied_residencehub_data.py
python app.py
```

Open `http://127.0.0.1:5000`.

## MySQL Workbench
1. Start MySQL 8.
2. Open Workbench and verify the connection.
3. Create a user/database or allow the migration to create the tables in `residencehub`.
4. Put the matching values in `backend/.env`.
5. Run `python migrate_database.py`; this is safer than running the original destructive supplied SQL.
6. Refresh schemas and verify `users`, `products`, `product_images`, `user_images`, `cart_items`, `orders`, `order_items`, `transactions`, `reviews`, `bulletin_posts`, `notifications`.

## Seller permission matrix
| Role | Can buy | Can sell |
|---|---|---|
| student | Yes | Yes |
| resident | Yes | Yes |
| vendor | Yes | Yes |
| faculty | Yes | Yes |

This matches the actual ResidenceHub implementation: any authenticated role can create/manage its own products.

## Image capacity
`product_images` is one-row-per-image with no artificial 15-image cap. The UI/backend accepts 1, 5, 15, 20, 50+ images subject only to normal request/server storage limits.


## Current application workflow

ResidenceHub is a single Flask + MySQL application. The active frontend uses `backend/static/js/unified.js` and `backend/static/css/unified.css`; older frontend assets are retained under `backend/static/legacy/` for reference but are not loaded by the active templates.

### Local setup

1. Create/activate a Python virtual environment inside `backend`.
2. Install dependencies with `pip install -r requirements.txt`.
3. Create `backend/.env` from `.env.example` and set the local MySQL connection values.
4. Create/update the schema with `python migrate_database.py` (non-destructive).
5. Start the app with `python app.py`.
6. Open `http://127.0.0.1:5000`.

Email verification is enabled in the application. If SMTP variables are not configured locally, the account is still created safely and the verification link is printed to the server console for local testing only. Production deployments must configure SMTP.

### Production

Use the included `Procfile` with Gunicorn rather than Flask's development server. Set stable `FLASK_SECRET_KEY` and `JWT_SECRET`, enable `SESSION_COOKIE_SECURE=true` behind HTTPS, configure MySQL, configure SMTP, and never commit `.env` or credentials.

The standalone `database.sql` contains the current core schema. `backend/migrate_database.py` remains the source of truth for non-destructive upgrades and legacy-data import.
