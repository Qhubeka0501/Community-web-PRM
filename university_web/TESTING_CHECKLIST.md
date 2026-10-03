# ResidenceHub Local Testing Checklist

Run the application from `university_web/backend` after installing dependencies and configuring `.env`.

## 1. Start-up
- [ ] `python migrate_database.py` completes without errors.
- [ ] `python app.py` starts on port 5000.
- [ ] `http://127.0.0.1:5000/` opens the ResidenceHub Home page.
- [ ] Refreshing Home and clicking Home repeatedly always stays on the same Home page.

## 2. Navigation / UI
- [ ] ResidenceHub branding is consistent across pages.
- [ ] Home, Marketplace and Community navigation work.
- [ ] Selling is visible only to an authenticated user who can sell.
- [ ] Cart counter updates.
- [ ] Notifications open and close.
- [ ] Sign in / Sign out state changes correctly.
- [ ] Mobile navigation opens and closes.
- [ ] No browser `alert()` boxes are used for normal success/error feedback.

## 3. Registration and verification
- [ ] Register a new student account.
- [ ] Account is created with `is_verified = 0`.
- [ ] Verification pending page appears.
- [ ] If SMTP is not configured locally, the verification URL appears in the Flask console as `[DEV VERIFICATION LINK]`.
- [ ] Open the verification URL.
- [ ] Verification success page appears.
- [ ] Account can now sign in.
- [ ] Try signing in before verification and confirm it is blocked.
- [ ] Resend verification works.

## 4. Authentication
- [ ] Login with email works.
- [ ] Login with username works.
- [ ] Incorrect credentials show an inline error.
- [ ] Logout works.
- [ ] Password visibility buttons work.
- [ ] Password reset request works.
- [ ] Reset token can set a new password.

## 5. Marketplace
- [ ] Marketplace loads products.
- [ ] Search works.
- [ ] Category filter works.
- [ ] Condition filter works.
- [ ] Product detail page loads.
- [ ] Product image gallery works.
- [ ] Add to cart works.
- [ ] Cart quantity changes and removal work.
- [ ] Demo checkout clearly states that no real charge is made.

## 6. Selling
- [ ] Seller dashboard loads for an authenticated seller.
- [ ] Create product works.
- [ ] Product image previews work.
- [ ] Multiple product images can be uploaded.
- [ ] Edit product works.
- [ ] Product appears in the marketplace after creation.

## 7. Community / account
- [ ] Bulletin posts load.
- [ ] New bulletin post works.
- [ ] Profile loads.
- [ ] Profile changes save.
- [ ] Profile image upload works.
- [ ] Orders page loads purchases and sales.
- [ ] Wallet loads balances and transactions.
- [ ] Notifications load.

## 8. Before deployment
- [ ] Production `FLASK_SECRET_KEY` is set.
- [ ] Production `JWT_SECRET` is set.
- [ ] Production `SESSION_COOKIE_SECURE=true` is set behind HTTPS.
- [ ] Railway/MySQL environment variables are configured.
- [ ] SMTP is configured for production email delivery.
- [ ] `.env` and secrets are not committed.
- [ ] Gunicorn starts the application through the included `Procfile`.
