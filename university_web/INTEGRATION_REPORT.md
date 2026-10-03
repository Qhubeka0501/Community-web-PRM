# University Web + ResidenceHub Integration Report

## Inspection checkpoint
### University Web
- Flask/Python foundation in `backend/`, with `app.py`, `db.py`, `verification.py`, Jinja templates and static assets.
- MySQL access already used `mysql.connector`.
- Existing security included Werkzeug password hashing, JWT generation, verification tokens, email verification and password reset.
- Existing role model was split across `residence_buyers` and `residence_sellers`.
- Existing seller product routes used `products`, `product_sizes`, `product_colors` and relational `product_images`.
- Existing UI design language uses navy `#1e3a8a`, gold `#f59e0b`, white cards and responsive navigation.

### ResidenceHub
- Node HTTP backend with SQLite was inspected as the functionality/business-rule source.
- Meaningful features: 4 registration roles, auth, sessions, password reset, marketplace, categories/search, product CRUD, cart grouped by seller, checkout, demo payment, wallet, transactions, reviews, profiles, bulletin, seller dashboard.
- The supplied code has **no notification route/table**, so a unified MySQL notification system was added to satisfy the requested functional navigation.
- `products.js` creates products after authentication only; it does not check role.
- `orders.js` explicitly documents seller statistics as available to **any logged-in user because any role can sell**.
- Therefore the exact seller rule is: **student, resident, vendor and faculty can sell; users can both buy and sell.**

## Feature gap actions
| Feature | University Web | ResidenceHub | Final action |
|---|---|---|---|
| Flask/MySQL | Existing | No | Preserve University |
| Auth/security | Stronger base | Separate SQLite/session system | Unified |
| Roles | buyer/seller tables | 4 roles | Unified 4 roles |
| Email verification | Existing | No equivalent | Preserve/improve |
| Password reset | Existing | Existing | Preserve University email flow |
| Marketplace | Partial | Strong | Integrated |
| Multi-image products | Relational | Seed only | Unlimited relational images |
| Cart/orders | Partial | Strong | Integrated |
| Payments | Partial | Demo | Secure demo flow, no card storage |
| Wallet | No coherent route | Existing | Integrated |
| Reviews | No complete route | Existing | Integrated |
| Bulletin | No complete route | Existing | Integrated |
| Profile images | Limited | schema support | Integrated |
| Notifications | Partial/absent | Absent | Added unified system |

## Database decision
The original supplied ResidenceHub SQL drops tables. It is retained only as source material and is **not** the migration used by the final app.
`backend/migrate_database.py` is non-destructive and creates missing unified tables.
Legacy University `residence_buyers`/`residence_sellers` are imported when safely mappable, without deleting them.
Supplied ResidenceHub records can be imported with `backend/import_supplied_residencehub_data.py`, which maps by email/name instead of assuming IDs.

## Security decisions
- MySQL parameterized queries.
- HTTP-only, SameSite sessions.
- JWT compatibility retained for API Authorization header.
- Backend ownership checks for products, images, cart, orders, bulletin and profiles.
- Seller rule enforced centrally without changing the actual ResidenceHub multi-role rule.
- MIME/extension/size checks, unique filenames and fixed upload directories.
- Card numbers are validated only for demo flow and never stored.
- Email credentials only from environment variables.
- Original `.env` was removed from the deliverable.

## Assumptions
- The development MySQL server is not available in the uploaded files, so migration execution against a live database was not performed.
- The supplied ResidenceHub password hashes are Node `scrypt`; the final app includes compatible verification for `legacy_scrypt` records and upgrades a password to Werkzeug hashing on reset.
- Existing University legacy table schemas may vary; migration only imports columns it can safely identify.

## Manual setup
1. Create MySQL database/server access.
2. Copy `.env.example` to `.env` and fill secrets.
3. `pip install -r requirements.txt`
4. `python migrate_database.py`
5. Optional: `python import_supplied_residencehub_data.py`
6. `python app.py`
