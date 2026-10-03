"""
Flask application for the Community Store (ResidenceHub): page routes, JSON APIs
for auth, products, cart, orders, payments, wallet, profiles, reviews, bulletin and
notifications, all backed by the existing MySQL `residencehub` database.
"""
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, abort
from db import get_connection
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from verification import generate_verification_token, send_verification_email, send_password_reset_email
from uuid import uuid4
from datetime import datetime, timedelta
from functools import wraps
from decimal import Decimal
import os, json, secrets, jwt, re, mimetypes

load_dotenv()
BASE_DIR=os.path.dirname(os.path.abspath(__file__))
backendApp=Flask(__name__)
backendApp.config.update(
    SECRET_KEY=os.getenv("FLASK_SECRET_KEY") or os.getenv("JWT_SECRET") or secrets.token_urlsafe(32),
    MAX_CONTENT_LENGTH=int(os.getenv("MAX_UPLOAD_MB","10"))*1024*1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE","false").lower()=="true",
)
JWT_SECRET=os.getenv("JWT_SECRET", backendApp.config["SECRET_KEY"])
JWT_EXPIRES_MINUTES=int(os.getenv("JWT_EXPIRES_MINUTES","60"))
ALLOWED_EXTENSIONS={"png","jpg","jpeg","gif","webp"}
ALLOWED_MIMES={"image/png","image/jpeg","image/gif","image/webp"}
DELIVERY_FEE=Decimal("25.00")

# Current UTC timestamp used for token expiry and record timestamps.
def now(): return datetime.utcnow()

CSRF_EXEMPT_PATHS={"/api/auth/login","/api/auth/register","/api/auth/resend-verification"}
CSRF_METHODS={"POST","PUT","PATCH","DELETE"}

@backendApp.before_request
def protect_state_changing_requests():
    if request.method not in CSRF_METHODS or request.path in CSRF_EXEMPT_PATHS: return
    cookie=request.cookies.get("csrf_token")
    header=request.headers.get("X-CSRF-Token")
    if not cookie or not header or not secrets.compare_digest(cookie,header):
        return jsonify(error="Invalid or missing CSRF token"),403

@backendApp.after_request
def add_security_headers(response):
    if not request.cookies.get("csrf_token"):
        response.set_cookie("csrf_token",secrets.token_urlsafe(32),secure=backendApp.config["SESSION_COOKIE_SECURE"],httponly=False,samesite="Lax")
    response.headers.setdefault("X-Content-Type-Options","nosniff")
    response.headers.setdefault("X-Frame-Options","DENY")
    response.headers.setdefault("Referrer-Policy","strict-origin-when-cross-origin")
    return response
# Return a date/datetime as an ISO-8601 string, passing other values through unchanged.
def iso(v): return v.isoformat() if hasattr(v,"isoformat") else v
# Normalise a Decimal/None database amount into a JSON-safe float.
def money(v): return float(v) if isinstance(v, Decimal) else float(v or 0)

# Open a MySQL connection and return (connection, dictionary cursor).
def db_cursor():
    conn=get_connection(); return conn, conn.cursor(dictionary=True)

# Commit or roll back, then always close the cursor and connection.
def close(conn, cur, commit=False):
    try:
        if commit: conn.commit()
        else: conn.rollback()
    finally:
        cur.close(); conn.close()

# Resolve the signed-in user from the Flask session, falling back to a JWT Bearer token. Returns
# the user row or None.
def current_user():
    uid=session.get("user_id")
    if uid:
        conn,cur=db_cursor()
        cur.execute("SELECT * FROM users WHERE id=%s",(uid,)); user=cur.fetchone()
        close(conn,cur)
        if user: return user
    auth=request.headers.get("Authorization","")
    if auth.startswith("Bearer "):
        try:
            payload=jwt.decode(auth[7:],JWT_SECRET,algorithms=["HS256"])
            conn,cur=db_cursor(); cur.execute("SELECT * FROM users WHERE id=%s",(payload["user_id"],)); user=cur.fetchone(); close(conn,cur)
            return user
        except jwt.PyJWTError: return None
    return None

# Decorator: reject unauthenticated requests with 401, otherwise pass the user row as the
# handler's first argument.
def require_auth(fn):
    @wraps(fn)
    # Inner wrapper that performs the check before delegating to the decorated view.
    def wrapped(*a,**kw):
        user=current_user()
        if not user: return jsonify(error="Authentication required"),401
        return fn(user,*a,**kw)
    return wrapped

# ResidenceHub source of truth: auth.js defines student/resident/vendor/faculty;
# products.js creates products for any authenticated user, and sellerStats explicitly
# says any logged-in user can sell. Preserve that exact multi-role rule.
def can_sell(user): return user is not None

# Check a submitted password against the stored hash, supporting both Werkzeug hashes and the
# legacy scrypt scheme.
def verify_user_password(user, password):
    if user.get("password_scheme") == "legacy_scrypt":
        import hashlib, hmac
        try:
            candidate=hashlib.scrypt(password.encode(),salt=str(user.get("password_salt") or "").encode(),n=16384,r=8,p=1,dklen=64).hex()
            return hmac.compare_digest(candidate,str(user.get("password_hash") or ""))
        except Exception:
            return False
    return check_password_hash(user.get("password_hash",""), password)

# Decorator: allow the request only when the user is permitted to sell, else 403.
def require_seller(fn):
    @wraps(fn)
    # Inner wrapper that performs the check before delegating to the decorated view.
    def wrapped(user,*a,**kw):
        if not can_sell(user): return jsonify(error="Seller permission required"),403
        return fn(user,*a,**kw)
    return wrapped

# Require email verification for account access.
def verification_required(user):
    return bool(user and int(user.get("is_verified") or 0) == 1)

# Validate an upload's extension and MIME type against the allowed image types.
def allowed_file(f):
    ext=f.filename.rsplit(".",1)[-1].lower() if "." in f.filename else ""
    mime=(f.mimetype or mimetypes.guess_type(f.filename)[0] or "").lower()
    return ext in ALLOWED_EXTENSIONS and mime in ALLOWED_MIMES

# Validate and store an uploaded image under static/uploads/<folder> and return its relative path.
def save_image(f, folder):
    if not f or not f.filename or not allowed_file(f): raise ValueError("Only PNG, JPG, JPEG, GIF and WEBP images are allowed")
    ext=f.filename.rsplit(".",1)[-1].lower()
    name=f"{uuid4().hex}.{ext}"
    path=os.path.join(BASE_DIR,"static","uploads",folder)
    os.makedirs(path,exist_ok=True)
    f.save(os.path.join(path,name))
    return f"uploads/{folder}/{name}"

# Fetch all images for a product, primary image first, then sort order.
def product_images(cur,pid):
    cur.execute("SELECT id,image_url,sort_order,is_primary FROM product_images WHERE product_id=%s ORDER BY is_primary DESC,sort_order,id",(pid,))
    return cur.fetchall()

# Build the full JSON representation of a product row: seller summary, sizes, colours, images and
# numeric price.
def serialize_product(cur,row):
    if not row:return None
    cur.execute("SELECT id,name,business_name,role,residence FROM users WHERE id=%s",(row["seller_id"],)); seller=cur.fetchone()
    cur.execute("SELECT size FROM product_sizes WHERE product_id=%s ORDER BY id",(row["id"],)); sizes=[r["size"] for r in cur.fetchall()]
    cur.execute("SELECT color FROM product_colors WHERE product_id=%s ORDER BY id",(row["id"],)); colors=[r["color"] for r in cur.fetchall()]
    d=dict(row); d["price"]=money(d.get("price")); d["images"]=product_images(cur,row["id"]); d["sizes"]=sizes; d["colors"]=colors
    d["seller"]={"id":seller["id"],"name":seller.get("business_name") or seller["name"],"role":seller["role"],"residence":seller.get("residence")} if seller else None
    d["created_at"]=iso(d.get("created_at")); return d

# Insert an in-app notification row for a user.
def notify(cur,user_id,title,message,kind="info",link=None):
    cur.execute("INSERT INTO notifications (user_id,title,message,kind,link) VALUES (%s,%s,%s,%s,%s)",(user_id,title,message,kind,link))

# Render a Jinja template with the given context (single place for page rendering).
def page(name, **ctx): return render_template(name, **ctx)

@backendApp.get("/")
# GET / - render the Community Store landing page.
def home(): return page("home.html")
@backendApp.get("/marketplace")
# GET /marketplace - render the product browsing page.
def marketplace(): return page("marketplace.html")
@backendApp.get("/product/<int:product_id>")
# GET /product/<id> - render the product detail page.
def product_page(product_id): return page("product.html",product_id=product_id)
@backendApp.get("/cart")
# GET /cart - render the shopping cart page.
def cart_page(): return page("cart.html")
@backendApp.get("/orders")
# GET /orders - render the buyer/seller orders page.
def orders_page(): return page("orders.html")
@backendApp.get("/wallet")
# GET /wallet - render the wallet page.
def wallet_page(): return page("wallet.html")
@backendApp.get("/profile")
# GET /profile - render the current user's profile page.
def profile_page(): return page("profile.html")
@backendApp.get("/bulletin")
# GET /bulletin - render the community bulletin page.
def bulletin_page(): return page("bulletin.html")
@backendApp.get("/seller/dashboard")
# GET /seller/dashboard - render the seller dashboard.
def seller_dashboard_page(): return page("seller_dashboard.html")
@backendApp.get("/seller/products/new")
# GET /seller/products/new - render an empty product form.
def add_product_page(): return page("product_form.html",product_id=None)
@backendApp.get("/seller/products/<int:product_id>/edit")
# GET /seller/products/<id>/edit - render the product form for an existing listing.
def edit_product_page(product_id): return page("product_form.html",product_id=product_id)
@backendApp.get("/login")
# GET /login - render the login page.
def login_page(): return page("login.html")
@backendApp.get("/register")
# GET /register - render the unified registration page.
def register_page(): return page("register.html")
@backendApp.get("/password_reset")
# GET /password_reset - render the 'request a reset link' page.
def password_reset_page(): return page("password_reset.html")
@backendApp.get("/reset-password")
# GET /reset-password - render the new-password form for a reset token.
def reset_password_page(): return page("reset_password.html",token=request.args.get("token",""))
@backendApp.get("/verify/<token>")
def verify_email(token):
    conn,cur=db_cursor()
    cur.execute("SELECT id,email,token_expires_at FROM users WHERE verification_token=%s",(token,)); u=cur.fetchone()
    if not u or not u["token_expires_at"] or u["token_expires_at"]<now():
        close(conn,cur)
        return page("verification_failed.html",reason="invalid")
    cur.execute("UPDATE users SET is_verified=1,verification_token=NULL,token_expires_at=NULL WHERE id=%s",(u["id"],))
    close(conn,cur,True)
    return page("verification_success.html")

@backendApp.post("/api/auth/resend-verification")
def resend_verification():
    data=request.get_json(silent=True) or request.form
    email=str(data.get("email") or "").strip().lower()
    if not email:
        return jsonify(error="Email is required"),400
    conn,cur=db_cursor()
    cur.execute("SELECT id,email,is_verified FROM users WHERE LOWER(email)=%s",(email,))
    user=cur.fetchone()
    if not user:
        close(conn,cur)
        return jsonify(ok=True,message="If an unverified account exists, a new verification email has been sent.")
    if int(user.get("is_verified") or 0)==1:
        close(conn,cur)
        return jsonify(ok=True,message="This account is already verified.")
    token=generate_verification_token()
    expiry=now()+timedelta(minutes=15)
    cur.execute("UPDATE users SET verification_token=%s,token_expires_at=%s WHERE id=%s",(token,expiry,user["id"]))
    close(conn,cur,True)
    link=request.url_root.rstrip("/")+"/verify/"+token
    try:
        sent=send_verification_email(user["email"],link)
    except Exception as exc:
        print("VERIFICATION EMAIL ERROR:",repr(exc))
        sent=False
    if not sent:
        print("[DEV VERIFICATION LINK]",link)
    return jsonify(ok=True,message="If the account is unverified, a new verification email has been sent.")





@backendApp.post("/api/auth/register")
# POST /api/auth/register - create a role-based account and send an email verification link.
def register():
    data = request.get_json(silent=True) or request.form

    role = str(data.get("role", "")).lower()

    if role not in {"student", "resident", "vendor", "faculty"}:
        return jsonify(
            error="role must be student, resident, vendor or faculty"
        ), 400

    name = (
        data.get("businessName")
        if role == "vendor"
        else data.get("name")
    ) or data.get("name")

    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not name or not email or not password or len(password) < 8:
        return jsonify(
            error="Name, valid email and password of at least 8 characters are required"
        ), 400

    if data.get("confirmPassword", password) != password:
        return jsonify(error="Passwords do not match"), 400

    conn, cur = db_cursor()
    _registration_token=generate_verification_token()

    try:
        cur.execute("""
            INSERT INTO users(
                role,
                name,
                username,
                email,
                password_hash,
                password_salt,
                password_scheme,
                cellphone,
                business_name,
                registration_number,
                residence,
                address,
                is_verified,
                verification_token,
                token_expires_at
            )
            VALUES(
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
        """, (
            role,
            name,
            str(
                data.get("username") or email.split("@")[0]
            ).lower(),
            email,
            generate_password_hash(password),
            "",
            "werkzeug",
            data.get("cellphone"),
            data.get("businessName") if role == "vendor" else None,
            data.get("registrationNumber"),
            data.get("residence"),
            data.get("address"),
            0,      # Require email verification before login
            _registration_token,
            now() + timedelta(minutes=15)
        ))

        uid = cur.lastrowid
        close(conn, cur, True)

    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()

        print("REGISTRATION DATABASE ERROR:", repr(e))
        return jsonify(error=str(e)), 500

    verification_link=request.url_root.rstrip("/")+"/verify/"+str(_registration_token)
    try:
        sent=send_verification_email(email,verification_link)
    except Exception as exc:
        print("VERIFICATION EMAIL ERROR:",repr(exc))
        sent=False
    if not sent:
        print("[DEV VERIFICATION LINK]",verification_link)
    return jsonify(
        ok=True,
        message="Account created. Check your email to verify your account before signing in.",
        user_id=uid,
        verification_required=True
    ), 201
   




@backendApp.post("/api/auth/login")
# POST /api/auth/login - authenticate by email or username, start a session and return a JWT plus
# the public user object.
def login():
    data=request.get_json(silent=True) or request.form; ident=str(data.get("identifier") or data.get("email") or "").lower().strip(); password=data.get("password","")
    conn,cur=db_cursor(); cur.execute("SELECT * FROM users WHERE LOWER(email)=%s OR LOWER(username)=%s",(ident,ident)); user=cur.fetchone(); close(conn,cur)
    if not user or not verify_user_password(user,password): return jsonify(error="Invalid credentials"),401
    if not verification_required(user): return jsonify(error="Please verify your email before logging in"),403
    session.clear(); session["user_id"]=user["id"]; session.permanent=True
    token=jwt.encode({"user_id":user["id"],"email":user["email"],"role":user["role"],"exp":now()+timedelta(minutes=JWT_EXPIRES_MINUTES)},JWT_SECRET,algorithm="HS256")
    return jsonify(ok=True,token=token,user=public_user(user))

@backendApp.post("/api/auth/logout")
# POST /api/auth/logout - clear the session.
def logout(): session.clear(); return jsonify(ok=True)

# Strip a user row down to the fields that are safe to expose to the client.
def public_user(u):
    return {"id":u["id"],"role":u["role"],"name":u["name"],"username":u.get("username"),"email":u.get("email"),"cellphone":u.get("cellphone"),"business_name":u.get("business_name"),"residence":u.get("residence"),"address":u.get("address"),"profile_image_url":u.get("profile_image_url"),"can_sell":can_sell(u)}

@backendApp.get("/api/auth/me")
@require_auth
# GET /api/auth/me - return the authenticated user's public profile.
def me(user): return jsonify(user=public_user(user))

@backendApp.post("/api/auth/request-reset")
# POST /api/auth/request-reset - create a one-hour reset token and email it. Always answers the
# same way so accounts cannot be enumerated.
def request_reset():
    data=request.get_json(silent=True) or request.form; ident=str(data.get("identifier") or data.get("email") or "").lower().strip()
    conn,cur=db_cursor(); cur.execute("SELECT id,email FROM users WHERE LOWER(email)=%s OR LOWER(username)=%s",(ident,ident)); user=cur.fetchone()
    if user:
        token=secrets.token_urlsafe(32); cur.execute("INSERT INTO password_resets(token,user_id,expires_at) VALUES(%s,%s,%s)",(token,user["id"],now()+timedelta(hours=1)))
        close(conn,cur,True); send_password_reset_email(user["email"],request.url_root.rstrip("/")+"/reset-password?token="+token)
    else: close(conn,cur)
    return jsonify(ok=True,message="If the account exists, a reset email has been sent.")

@backendApp.post("/api/auth/perform-reset")
# POST /api/auth/perform-reset - consume a valid reset token and set the new password hash.
def perform_reset():
    data=request.get_json(silent=True) or request.form; token=data.get("token",""); password=data.get("password","")
    if len(password)<8:return jsonify(error="Password must be at least 8 characters"),400
    conn,cur=db_cursor(); cur.execute("SELECT * FROM password_resets WHERE token=%s AND used=0 AND expires_at>%s",(token,now())); r=cur.fetchone()
    if not r: close(conn,cur); return jsonify(error="Invalid or expired reset token"),400
    cur.execute("UPDATE users SET password_hash=%s,password_scheme='werkzeug',password_salt='' WHERE id=%s",(generate_password_hash(password),r["user_id"])); cur.execute("UPDATE password_resets SET used=1 WHERE token=%s",(token,))
    close(conn,cur,True); return jsonify(ok=True)

@backendApp.get("/api/products")
# GET /api/products - list active products with optional search, category, condition and residence
# filters.
def list_products():
    q=request.args.get("q","").strip(); category=request.args.get("category"); condition=request.args.get("condition"); residence=request.args.get("residence")
    conn,cur=db_cursor(); sql="SELECT * FROM products WHERE status='active'"; params=[]
    if q: sql+=" AND (name LIKE %s OR description LIKE %s)"; params += [f"%{q}%",f"%{q}%"]
    if category: sql+=" AND category=%s"; params.append(category)
    if condition: sql+=" AND condition_tag=%s"; params.append(condition)
    if residence: sql+=" AND residence=%s"; params.append(residence)
    sql+=" ORDER BY created_at DESC"; cur.execute(sql,tuple(params)); rows=cur.fetchall(); result=[serialize_product(cur,r) for r in rows]; close(conn,cur)
    return jsonify(products=result)

@backendApp.get("/api/products/categories")
# GET /api/products/categories - list categories with their active product counts.
def categories():
    conn,cur=db_cursor(); cur.execute("SELECT category,COUNT(*) count FROM products WHERE status='active' GROUP BY category ORDER BY category"); rows=cur.fetchall(); close(conn,cur); return jsonify(categories=rows)

@backendApp.get("/api/products/<int:product_id>")
# GET /api/products/<id> - return one serialized product, or 404.
def get_product(product_id):
    conn,cur=db_cursor(); cur.execute("SELECT * FROM products WHERE id=%s",(product_id,)); row=cur.fetchone(); result=serialize_product(cur,row); close(conn,cur)
    if not result:return jsonify(error="Product not found"),404
    return jsonify(product=result)

@backendApp.post("/api/products")
@require_auth
@require_seller
# POST /api/products - create a listing owned by the current user, with sizes, colours and
# uploaded images.
def create_product(user):
    if not verification_required(user): return jsonify(error="Verify your account before selling"),403
    name=request.form.get("name","").strip(); category=request.form.get("category","").strip()
    try: price=Decimal(request.form.get("price","0")); stock=int(request.form.get("stock","0"))
    except: return jsonify(error="Invalid price or stock"),400
    if not name or not category or price<0 or stock<0:return jsonify(error="Name, category, non-negative price and stock are required"),400
    conn,cur=db_cursor()
    try:
        cur.execute("""INSERT INTO products(seller_id,name,category,residence,price,stock,description,condition_tag,status)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'active')""",(user["id"],name,category,request.form.get("residence"),price,stock,request.form.get("description"),request.form.get("condition_tag")))
        pid=cur.lastrowid
        sizes=json.loads(request.form.get("sizes","[]")); colors=json.loads(request.form.get("colors","[]"))
        for x in sizes: cur.execute("INSERT INTO product_sizes(product_id,size) VALUES(%s,%s)",(pid,str(x)))
        for x in colors: cur.execute("INSERT INTO product_colors(product_id,color) VALUES(%s,%s)",(pid,str(x)))
        for idx,f in enumerate(request.files.getlist("images")):
            if not f or not f.filename: continue
            path=save_image(f,"products"); cur.execute("INSERT INTO product_images(product_id,image_url,sort_order,is_primary) VALUES(%s,%s,%s,%s)",(pid,path,idx,1 if idx==0 else 0))
        notify(cur,user["id"],"Product published",f"{name} is now listed.","product",f"/product/{pid}")
        close(conn,cur,True); return jsonify(ok=True,product_id=pid),201
    except ValueError as e: conn.rollback(); cur.close(); conn.close(); return jsonify(error=str(e)),400
    except Exception as e: conn.rollback(); cur.close(); conn.close(); return jsonify(error="Could not create product"),500

# Fetch a product only if it belongs to the given user (ownership check).
def owned_product(cur,pid,uid):
    cur.execute("SELECT * FROM products WHERE id=%s AND seller_id=%s",(pid,uid)); return cur.fetchone()

@backendApp.put("/api/products/<int:product_id>")
@require_auth
@require_seller
# PUT /api/products/<id> - update allowed fields on a listing the user owns.
def update_product(user,product_id):
    data=request.get_json(silent=True) or request.form
    conn,cur=db_cursor(); p=owned_product(cur,product_id,user["id"])
    if not p: close(conn,cur); return jsonify(error="Product not found or not owned by you"),404
    allowed=["name","category","residence","description","condition_tag","status"]; updates=[]; params=[]
    for k in allowed:
        if k in data: updates.append(f"{k}=%s"); params.append(data[k])
    if "price" in data: updates.append("price=%s"); params.append(Decimal(str(data["price"])))
    if "stock" in data: updates.append("stock=%s"); params.append(int(data["stock"]))
    if updates: cur.execute("UPDATE products SET "+",".join(updates)+" WHERE id=%s",tuple(params+[product_id]))
    close(conn,cur,True); return jsonify(ok=True)

@backendApp.delete("/api/products/<int:product_id>")
@require_auth
@require_seller
# DELETE /api/products/<id> - archive (soft delete) a listing the user owns.
def delete_product(user,product_id):
    conn,cur=db_cursor(); cur.execute("UPDATE products SET status='archived' WHERE id=%s AND seller_id=%s",(product_id,user["id"])); ok=cur.rowcount; close(conn,cur,True)
    return (jsonify(ok=True),200) if ok else (jsonify(error="Product not found or not owned by you"),404)

@backendApp.post("/api/products/<int:product_id>/images")
@require_auth
@require_seller
# POST /api/products/<id>/images - append extra images to an owned listing.
def add_product_images(user,product_id):
    conn,cur=db_cursor()
    if not owned_product(cur,product_id,user["id"]): close(conn,cur); return jsonify(error="Product not found or not owned by you"),404
    cur.execute("SELECT COALESCE(MAX(sort_order),-1)+1 n FROM product_images WHERE product_id=%s",(product_id,)); start=cur.fetchone()["n"]
    try:
        added=0
        for i,f in enumerate(request.files.getlist("images")):
            if f and f.filename:
                path=save_image(f,"products"); cur.execute("INSERT INTO product_images(product_id,image_url,sort_order,is_primary) VALUES(%s,%s,%s,0)",(product_id,path,start+i)); added+=1
        close(conn,cur,True); return jsonify(ok=True,added=added)
    except ValueError as e: conn.rollback(); cur.close(); conn.close(); return jsonify(error=str(e)),400

@backendApp.delete("/api/products/<int:product_id>/images/<int:image_id>")
@require_auth
@require_seller
# DELETE /api/products/<id>/images/<image_id> - remove one image from an owned listing.
def delete_product_image(user,product_id,image_id):
    conn,cur=db_cursor()
    if not owned_product(cur,product_id,user["id"]): close(conn,cur); return jsonify(error="Product not found or not owned by you"),404
    cur.execute("DELETE FROM product_images WHERE id=%s AND product_id=%s",(image_id,product_id)); close(conn,cur,True); return jsonify(ok=True)

@backendApp.post("/api/products/<int:product_id>/images/<int:image_id>/primary")
@require_auth
@require_seller
# POST /api/products/<id>/images/<image_id>/primary - make one image the listing's primary image.
def primary_product_image(user,product_id,image_id):
    conn,cur=db_cursor()
    if not owned_product(cur,product_id,user["id"]): close(conn,cur); return jsonify(error="Product not found or not owned by you"),404
    cur.execute("UPDATE product_images SET is_primary=0 WHERE product_id=%s",(product_id,)); cur.execute("UPDATE product_images SET is_primary=1 WHERE id=%s AND product_id=%s",(image_id,product_id)); close(conn,cur,True); return jsonify(ok=True)

@backendApp.get("/api/seller/products")
@require_auth
@require_seller
# GET /api/seller/products - list every listing belonging to the current seller.
def my_products(user):
    conn,cur=db_cursor(); cur.execute("SELECT * FROM products WHERE seller_id=%s ORDER BY created_at DESC",(user["id"],)); rows=[serialize_product(cur,r) for r in cur.fetchall()]; close(conn,cur); return jsonify(products=rows)

# Build the cart response: items grouped per seller, per-seller subtotals, delivery fee, total and
# item count.
def cart_payload(uid):
    conn,cur=db_cursor(); cur.execute("""SELECT ci.id cart_item_id,ci.quantity,p.* FROM cart_items ci JOIN products p ON p.id=ci.product_id WHERE ci.user_id=%s ORDER BY ci.created_at""",(uid,))
    rows=cur.fetchall(); groups={}; subtotal=Decimal("0")
    for r in rows:
        p=serialize_product(cur,r); line=Decimal(str(r["price"]))*r["quantity"]; sid=p["seller"]["id"]; g=groups.setdefault(sid,{"seller":p["seller"],"items":[],"subtotal":Decimal("0")}); g["items"].append({"cartItemId":r["cart_item_id"],"quantity":r["quantity"],"product":p,"lineTotal":money(line)}); g["subtotal"]+=line; subtotal+=line
    out=[] 
    for g in groups.values(): g["subtotal"]=money(g["subtotal"]); out.append(g)
    fee=DELIVERY_FEE*len(out); total=subtotal+fee; close(conn,cur)
    return {"groups":out,"subtotal":money(subtotal),"deliveryFee":money(fee),"total":money(total),"itemCount":sum(r["quantity"] for r in rows)}

@backendApp.get("/api/cart")
@require_auth
# GET /api/cart - return the current user's cart.
def get_cart(user): return jsonify(cart_payload(user["id"]))

@backendApp.post("/api/cart/items")
@require_auth
# POST /api/cart/items - add a product to the cart (blocks own products and over-stock
# quantities).
def add_cart(user):
    data=request.get_json(silent=True) or request.form
    try: pid=int(data.get("productId")); qty=max(1,int(data.get("quantity",1)))
    except:return jsonify(error="Invalid product or quantity"),400
    conn,cur=db_cursor(); cur.execute("SELECT seller_id,stock,status FROM products WHERE id=%s",(pid,)); p=cur.fetchone()
    if not p or p["status"]!="active": close(conn,cur); return jsonify(error="Product not found"),404
    if p["seller_id"]==user["id"]:close(conn,cur); return jsonify(error="You cannot buy your own product"),400
    if p["stock"]<qty:close(conn,cur); return jsonify(error="Not enough stock"),400
    cur.execute("INSERT INTO cart_items(user_id,product_id,quantity) VALUES(%s,%s,%s) ON DUPLICATE KEY UPDATE quantity=quantity+VALUES(quantity)",(user["id"],pid,qty)); close(conn,cur,True); return jsonify(cart_payload(user["id"]))

@backendApp.put("/api/cart/items/<int:item_id>")
@require_auth
# PUT /api/cart/items/<id> - change a cart line quantity, removing the line when it reaches zero.
def update_cart(user,item_id):
    data=request.get_json(silent=True) or request.form; qty=int(data.get("quantity",0)); conn,cur=db_cursor(); cur.execute("SELECT ci.*,p.stock FROM cart_items ci JOIN products p ON p.id=ci.product_id WHERE ci.id=%s AND ci.user_id=%s",(item_id,user["id"])); item=cur.fetchone()
    if not item:close(conn,cur); return jsonify(error="Cart item not found"),404
    if qty<=0:cur.execute("DELETE FROM cart_items WHERE id=%s",(item_id,))
    elif qty>item["stock"]:close(conn,cur); return jsonify(error="Not enough stock"),400
    else:cur.execute("UPDATE cart_items SET quantity=%s WHERE id=%s",(qty,item_id))
    close(conn,cur,True); return jsonify(cart_payload(user["id"]))

@backendApp.delete("/api/cart/items/<int:item_id>")
@require_auth
# DELETE /api/cart/items/<id> - remove a line from the cart.
def remove_cart(user,item_id):
    conn,cur=db_cursor(); cur.execute("DELETE FROM cart_items WHERE id=%s AND user_id=%s",(item_id,user["id"])); close(conn,cur,True); return jsonify(cart_payload(user["id"]))

@backendApp.post("/api/orders/checkout")
@require_auth
# POST /api/orders/checkout - turn the cart into one pending order per seller and return the new
# order ids and totals.
def checkout(user):
    cart=cart_payload(user["id"])
    if not cart["groups"]:return jsonify(error="Cart is empty"),400
    conn,cur=db_cursor()
    try:
        ids=[]
        for g in cart["groups"]:
            sub=sum(Decimal(str(x["lineTotal"])) for x in g["items"]); total=sub+DELIVERY_FEE
            cur.execute("INSERT INTO orders(buyer_id,seller_id,status,subtotal,delivery_fee,total) VALUES(%s,%s,'pending',%s,%s,%s)",(user["id"],g["seller"]["id"],sub,DELIVERY_FEE,total)); oid=cur.lastrowid; ids.append(oid)
            for item in g["items"]: cur.execute("INSERT INTO order_items(order_id,product_id,name,price,quantity) VALUES(%s,%s,%s,%s,%s)",(oid,item["product"]["id"],item["product"]["name"],item["product"]["price"],item["quantity"]))
        close(conn,cur,True); return jsonify(orderIds=ids,**{k:cart[k] for k in ("subtotal","deliveryFee","total")}),201
    except Exception: conn.rollback();cur.close();conn.close(); return jsonify(error="Checkout failed"),500

# Build the JSON representation of an order together with its line items.
def order_payload(cur,o):
    cur.execute("SELECT * FROM order_items WHERE order_id=%s",(o["id"],)); items=cur.fetchall()
    return {"id":o["id"],"status":o["status"],"subtotal":money(o["subtotal"]),"deliveryFee":money(o["delivery_fee"]),"total":money(o["total"]),"paymentMethod":o["payment_method"],"createdAt":iso(o["created_at"]),"items":[{"id":i["id"],"productId":i["product_id"],"name":i["name"],"price":money(i["price"]),"quantity":i["quantity"]} for i in items]}

@backendApp.get("/api/orders")
@require_auth
# GET /api/orders - list the user's orders as buyer, or as seller with ?as=seller.
def orders(user):
    as_seller=request.args.get("as")=="seller"; conn,cur=db_cursor(); cur.execute("SELECT * FROM orders WHERE "+("seller_id" if as_seller else "buyer_id")+"=%s ORDER BY created_at DESC",(user["id"],)); rows=[order_payload(cur,o) for o in cur.fetchall()]; close(conn,cur); return jsonify(orders=rows)

@backendApp.get("/api/orders/<int:order_id>")
@require_auth
# GET /api/orders/<id> - return a single order the user is buyer or seller of.
def get_order(user,order_id):
    conn,cur=db_cursor(); cur.execute("SELECT * FROM orders WHERE id=%s AND (buyer_id=%s OR seller_id=%s)",(order_id,user["id"],user["id"])); o=cur.fetchone()
    if not o:close(conn,cur); return jsonify(error="Order not found"),404
    result=order_payload(cur,o); close(conn,cur); return jsonify(order=result)

@backendApp.get("/api/orders/seller-stats")
@require_auth
@require_seller
# GET /api/orders/seller-stats - dashboard totals: orders, deliveries, active products and
# balances.
def seller_stats(user):
    conn,cur=db_cursor(); 
    cur.execute("SELECT COUNT(*) c FROM orders WHERE seller_id=%s",(user["id"],)); total=cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM orders WHERE seller_id=%s AND status='delivered'",(user["id"],)); deliveries=cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM products WHERE seller_id=%s AND status='active'",(user["id"],)); products=cur.fetchone()["c"]
    cur.execute("SELECT available_balance,pending_balance,balance FROM users WHERE id=%s",(user["id"],)); bal=cur.fetchone()
    close(conn,cur); return jsonify(totalOrders=total,deliveries=deliveries,myProducts=products,balance=money(bal["balance"]),availableBalance=money(bal["available_balance"]),pendingBalance=money(bal["pending_balance"]))

# Luhn checksum used to sanity-check a demo card number; no card data is stored.
def luhn(n):
    digits=[int(c) for c in str(n).replace(" ","") if c.isdigit()]
    if len(digits)<12:return False
    s=0
    for i,d in enumerate(digits[::-1]): s += d if i%2==0 else (d*2-9 if d*2>9 else d*2)
    return s%10==0

@backendApp.post("/api/payments/confirm")
@require_auth
# POST /api/payments/confirm - mark pending orders paid, decrement stock, clear the cart, record
# transactions and notify the seller.
def confirm_payment(user):
    data=request.get_json(silent=True) or request.form; ids=data.get("orderIds",[]); ids=[int(x) for x in ids] if isinstance(ids,list) else []
    if not ids:return jsonify(error="orderIds is required"),400
    method=data.get("method","card")
    if method=="card" and not luhn(data.get("cardNumber","")):return jsonify(error="Enter a valid card number"),400
    conn,cur=db_cursor()
    try:
        orders=[]
        for oid in ids:
            cur.execute("SELECT * FROM orders WHERE id=%s FOR UPDATE",(oid,)); o=cur.fetchone()
            if not o or o["buyer_id"]!=user["id"] or o["status"]!="pending": raise ValueError("Invalid pending order")
            cur.execute("SELECT oi.*,p.stock FROM order_items oi JOIN products p ON p.id=oi.product_id WHERE oi.order_id=%s FOR UPDATE",(oid,))
            items=cur.fetchall()
            for i in items:
                if i["stock"]<i["quantity"]: raise ValueError(f"Insufficient stock for {i['name']}")
            orders.append((o,items))
        for o,items in orders:
            cur.execute("UPDATE orders SET status='paid',payment_method=%s WHERE id=%s",(method,o["id"]))
            for i in items: cur.execute("UPDATE products SET stock=stock-%s WHERE id=%s",(i["quantity"],i["product_id"])); cur.execute("DELETE FROM cart_items WHERE user_id=%s AND product_id=%s",(user["id"],i["product_id"]))
            cur.execute("INSERT INTO transactions(user_id,type,amount,status,description) VALUES(%s,'purchase',%s,'completed',%s)",(user["id"],-o["total"],f"Order #{o['id']}"))
            cur.execute("INSERT INTO transactions(user_id,type,amount,status,description) VALUES(%s,'sale',%s,'completed',%s)",(o["seller_id"],o["subtotal"],f"Order #{o['id']} sale"))
            cur.execute("UPDATE users SET pending_balance=pending_balance+%s,balance=balance+%s WHERE id=%s",(o["subtotal"],o["subtotal"],o["seller_id"]))
            notify(cur,o["seller_id"],"New sale",f"Order #{o['id']} has been paid.","order",f"/orders?as=seller")
        notify(cur,user["id"],"Payment successful",f"{len(orders)} order(s) paid.","payment","/orders")
        close(conn,cur,True); return jsonify(ok=True,orderIds=ids)
    except ValueError as e:conn.rollback();cur.close();conn.close();return jsonify(error=str(e)),400
    except Exception:conn.rollback();cur.close();conn.close();return jsonify(error="Payment failed"),500

@backendApp.get("/api/wallet")
@require_auth
# GET /api/wallet - return balances plus recent transaction history.
def wallet(user):
    conn,cur=db_cursor(); cur.execute("SELECT balance,available_balance,pending_balance FROM users WHERE id=%s",(user["id"],)); b=cur.fetchone(); cur.execute("SELECT * FROM transactions WHERE user_id=%s ORDER BY created_at DESC LIMIT 50",(user["id"],)); tx=cur.fetchall(); close(conn,cur)
    return jsonify(balance=money(b["balance"]),availableBalance=money(b["available_balance"]),pendingBalance=money(b["pending_balance"]),transactions=[{"id":x["id"],"type":x["type"],"amount":money(x["amount"]),"status":x["status"],"description":x["description"],"createdAt":iso(x["created_at"])} for x in tx])

@backendApp.post("/api/wallet/deposit")
@require_auth
# POST /api/wallet/deposit - add funds and record a deposit transaction.
def deposit(user):
    data=request.get_json(silent=True) or request.form
    try: amount=Decimal(str(data.get("amount")))
    except:return jsonify(error="Invalid amount"),400
    if amount<=0:return jsonify(error="Invalid amount"),400
    conn,cur=db_cursor(); cur.execute("UPDATE users SET balance=balance+%s,available_balance=available_balance+%s WHERE id=%s",(amount,amount,user["id"])); cur.execute("INSERT INTO transactions(user_id,type,amount,status,description) VALUES(%s,'deposit',%s,'completed',%s)",(user["id"],amount,"Demo deposit")); close(conn,cur,True); return wallet(user)

@backendApp.post("/api/wallet/withdraw")
@require_auth
# POST /api/wallet/withdraw - withdraw funds when the available balance allows it.
def withdraw(user):
    data=request.get_json(silent=True) or request.form
    try: amount=Decimal(str(data.get("amount")))
    except:return jsonify(error="Invalid amount"),400
    conn,cur=db_cursor(); cur.execute("SELECT available_balance FROM users WHERE id=%s FOR UPDATE",(user["id"],)); b=cur.fetchone()
    if amount<=0 or b["available_balance"]<amount:close(conn,cur);return jsonify(error="Insufficient available balance"),400
    cur.execute("UPDATE users SET balance=balance-%s,available_balance=available_balance-%s WHERE id=%s",(amount,amount,user["id"]));cur.execute("INSERT INTO transactions(user_id,type,amount,status,description) VALUES(%s,'withdrawal',%s,'completed','Wallet withdrawal')",(user["id"],-amount));close(conn,cur,True);return wallet(user)

@backendApp.get("/api/users/me")
@require_auth
# GET /api/users/me - return the current user's own profile.
def my_profile(user): return jsonify(profile=public_user(user))

@backendApp.put("/api/users/me")
@require_auth
# PUT /api/users/me - update the user's own name, cellphone, address or residence.
def update_profile(user):
    data=request.get_json(silent=True) or request.form; allowed=["name","cellphone","address","residence"]; updates=[]; params=[]
    for k in allowed:
        if k in data:updates.append(f"{k}=%s");params.append(data[k])
    if not updates:return jsonify(error="No valid fields"),400
    conn,cur=db_cursor();cur.execute("UPDATE users SET "+",".join(updates)+" WHERE id=%s",tuple(params+[user["id"]]));close(conn,cur,True);return jsonify(ok=True)

@backendApp.post("/api/users/me/profile-image")
@require_auth
# POST /api/users/me/profile-image - upload and set the user's profile picture.
def profile_image(user):
    f=request.files.get("image")
    try:path=save_image(f,"users")
    except ValueError as e:return jsonify(error=str(e)),400
    conn,cur=db_cursor();cur.execute("UPDATE user_images SET is_primary=0 WHERE user_id=%s",(user["id"],));cur.execute("INSERT INTO user_images(user_id,image_url,image_type,is_primary) VALUES(%s,%s,'profile',1)",(user["id"],path));cur.execute("UPDATE users SET profile_image_url=%s WHERE id=%s",(path,user["id"]));close(conn,cur,True);return jsonify(ok=True,image_url=path)

@backendApp.get("/api/users/<int:user_id>")
# GET /api/users/<id> - public seller profile with average rating and reviews.
def public_profile(user_id):
    conn,cur=db_cursor();cur.execute("SELECT id,role,name,business_name,residence,address,profile_image_url FROM users WHERE id=%s",(user_id,));u=cur.fetchone()
    if not u:close(conn,cur);return jsonify(error="User not found"),404
    cur.execute("SELECT AVG(rating) avg,COUNT(*) count FROM reviews WHERE seller_id=%s",(user_id,));rating=cur.fetchone();cur.execute("SELECT * FROM reviews WHERE seller_id=%s ORDER BY created_at DESC",(user_id,));reviews=cur.fetchall();close(conn,cur)
    return jsonify(profile={**u,"rating":{"average":money(rating["avg"]) if rating["avg"] else 0,"count":rating["count"]},"reviews":[{"reviewerName":r["reviewer_name"],"rating":r["rating"],"comment":r["comment"],"createdAt":iso(r["created_at"])} for r in reviews]})

@backendApp.post("/api/users/<int:user_id>/reviews")
@require_auth
# POST /api/users/<id>/reviews - leave a 1-5 star review for another user.
def review_user(user,user_id):
    if user_id==user["id"]:return jsonify(error="You cannot review yourself"),400
    data=request.get_json(silent=True) or request.form; rating=int(data.get("rating",0)); comment=data.get("comment","")
    if rating<1 or rating>5:return jsonify(error="Rating must be 1-5"),400
    conn,cur=db_cursor();cur.execute("SELECT id FROM users WHERE id=%s",(user_id,))
    if not cur.fetchone():close(conn,cur);return jsonify(error="User not found"),404
    cur.execute("INSERT INTO reviews(seller_id,reviewer_id,reviewer_name,rating,comment) VALUES(%s,%s,%s,%s,%s)",(user_id,user["id"],user["name"],rating,comment));close(conn,cur,True);return jsonify(ok=True),201

@backendApp.get("/api/bulletin")
# GET /api/bulletin - list bulletin posts, optionally filtered by scope.
def bulletin():
    scope=request.args.get("scope","all"); conn,cur=db_cursor()
    if scope=="all":cur.execute("SELECT * FROM bulletin_posts ORDER BY created_at DESC")
    else:cur.execute("SELECT * FROM bulletin_posts WHERE scope=%s ORDER BY created_at DESC",(scope,))
    rows=cur.fetchall();close(conn,cur);return jsonify(posts=[{**r,"createdAt":iso(r.pop("created_at"))} for r in rows])

@backendApp.post("/api/bulletin")
@require_auth
# POST /api/bulletin - publish a bulletin post as the current user.
def create_bulletin(user):
    data=request.get_json(silent=True) or request.form; title=str(data.get("title","")).strip()
    if not title:return jsonify(error="Title is required"),400
    scope=data.get("scope","all")
    if scope not in {"all","broadcast","for_you"}:return jsonify(error="Invalid scope"),400
    conn,cur=db_cursor();cur.execute("INSERT INTO bulletin_posts(author_id,author_name,title,body,tag,scope) VALUES(%s,%s,%s,%s,%s,%s)",(user["id"],user["name"],title,data.get("body"),data.get("tag"),scope));close(conn,cur,True);return jsonify(ok=True),201

@backendApp.delete("/api/bulletin/<int:post_id>")
@require_auth
# DELETE /api/bulletin/<id> - delete a bulletin post the user authored.
def delete_bulletin(user,post_id):
    conn,cur=db_cursor();cur.execute("DELETE FROM bulletin_posts WHERE id=%s AND author_id=%s",(post_id,user["id"]));ok=cur.rowcount;close(conn,cur,True);return (jsonify(ok=True),200) if ok else (jsonify(error="Post not found or not owned by you"),404)

@backendApp.get("/api/notifications")
@require_auth
# GET /api/notifications - the user's 50 most recent notifications.
def notifications(user):
    conn,cur=db_cursor();cur.execute("SELECT * FROM notifications WHERE user_id=%s ORDER BY created_at DESC LIMIT 50",(user["id"],));rows=cur.fetchall();close(conn,cur);return jsonify(notifications=[{**r,"createdAt":iso(r.pop("created_at"))} for r in rows])

@backendApp.post("/api/notifications/<int:nid>/read")
@require_auth
# POST /api/notifications/<id>/read - mark one notification as read.
def read_notification(user,nid):
    conn,cur=db_cursor();cur.execute("UPDATE notifications SET is_read=1 WHERE id=%s AND user_id=%s",(nid,user["id"]));close(conn,cur,True);return jsonify(ok=True)

# Legacy aliases retained for University Web clients.
backendApp.add_url_rule("/seller/products","legacy_products_get",my_products,methods=["GET"])
backendApp.add_url_rule("/seller/products","legacy_products_post",create_product,methods=["POST"])

@backendApp.errorhandler(413)
# 413 handler: return a JSON error when an upload exceeds MAX_CONTENT_LENGTH.
def too_large(e): return jsonify(error="Upload is too large"),413

if __name__=="__main__":
    backendApp.run(host="0.0.0.0",port=int(os.getenv("PORT","5000")),debug=os.getenv("FLASK_DEBUG","false").lower()=="true")
