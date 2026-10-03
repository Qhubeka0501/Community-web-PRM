-- ResidenceHub / University Web MySQL schema
-- Generated from backend/migrate_database.py.
-- The Python migration remains the source of truth for non-destructive upgrades and legacy imports.

CREATE DATABASE IF NOT EXISTS residencehub CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE residencehub;

CREATE TABLE IF NOT EXISTS users (
 id INT AUTO_INCREMENT PRIMARY KEY, role VARCHAR(30) NOT NULL,
 name VARCHAR(255) NOT NULL, username VARCHAR(255) NULL UNIQUE, email VARCHAR(255) NULL UNIQUE,
 password_hash VARCHAR(255) NOT NULL, password_salt VARCHAR(255), password_scheme VARCHAR(30) NOT NULL DEFAULT 'werkzeug', cellphone VARCHAR(50), business_name VARCHAR(255),
 registration_number VARCHAR(100), residence VARCHAR(255), address VARCHAR(500),
 avatar_seed VARCHAR(255), profile_image_url TEXT, balance DECIMAL(12,2) NOT NULL DEFAULT 0,
 available_balance DECIMAL(12,2) NOT NULL DEFAULT 0, pending_balance DECIMAL(12,2) NOT NULL DEFAULT 0,
 is_verified TINYINT(1) NOT NULL DEFAULT 0, verification_token VARCHAR(255), token_expires_at DATETIME,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE KEY uk_users_verification_token (verification_token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS products (
 id INT AUTO_INCREMENT PRIMARY KEY, seller_id INT NOT NULL, name VARCHAR(255) NOT NULL, category VARCHAR(100) NOT NULL,
 residence VARCHAR(255), price DECIMAL(12,2) NOT NULL, stock INT NOT NULL DEFAULT 0, description TEXT,
 condition_tag VARCHAR(100), status VARCHAR(30) NOT NULL DEFAULT 'active', created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 KEY idx_products_seller(seller_id), CONSTRAINT fk_products_seller FOREIGN KEY(seller_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS product_images (
 id BIGINT AUTO_INCREMENT PRIMARY KEY, product_id INT NOT NULL, image_url TEXT NOT NULL,
 sort_order INT NOT NULL DEFAULT 0, is_primary TINYINT(1) NOT NULL DEFAULT 0, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 KEY idx_product_images_product(product_id), CONSTRAINT fk_product_images_product FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS product_sizes (
 id BIGINT AUTO_INCREMENT PRIMARY KEY, product_id INT NOT NULL, size VARCHAR(100) NOT NULL,
 KEY idx_product_sizes_product(product_id), CONSTRAINT fk_product_sizes_product FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS product_colors (
 id BIGINT AUTO_INCREMENT PRIMARY KEY, product_id INT NOT NULL, color VARCHAR(100) NOT NULL,
 KEY idx_product_colors_product(product_id), CONSTRAINT fk_product_colors_product FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cart_items (
 id INT AUTO_INCREMENT PRIMARY KEY,user_id INT NOT NULL,product_id INT NOT NULL,quantity INT NOT NULL DEFAULT 1,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,UNIQUE KEY uk_cart_user_product(user_id,product_id),
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE, FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS orders (
 id INT AUTO_INCREMENT PRIMARY KEY,buyer_id INT NOT NULL,seller_id INT NOT NULL,status VARCHAR(30) NOT NULL DEFAULT 'pending',
 subtotal DECIMAL(12,2) NOT NULL,delivery_fee DECIMAL(12,2) NOT NULL DEFAULT 25,total DECIMAL(12,2) NOT NULL,payment_method VARCHAR(100),
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,KEY idx_orders_buyer(buyer_id),KEY idx_orders_seller(seller_id),
 FOREIGN KEY(buyer_id) REFERENCES users(id),FOREIGN KEY(seller_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS order_items (
 id INT AUTO_INCREMENT PRIMARY KEY,order_id INT NOT NULL,product_id INT NULL,name VARCHAR(255) NOT NULL,price DECIMAL(12,2) NOT NULL,quantity INT NOT NULL DEFAULT 1,
 FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS reviews (
 id INT AUTO_INCREMENT PRIMARY KEY,seller_id INT NOT NULL,reviewer_id INT NULL,reviewer_name VARCHAR(255) NOT NULL,rating INT NOT NULL,comment TEXT,created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 KEY idx_reviews_seller(seller_id),FOREIGN KEY(seller_id) REFERENCES users(id) ON DELETE CASCADE,FOREIGN KEY(reviewer_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS transactions (
 id INT AUTO_INCREMENT PRIMARY KEY,user_id INT NOT NULL,type VARCHAR(30) NOT NULL,amount DECIMAL(12,2) NOT NULL,status VARCHAR(50) NOT NULL DEFAULT 'completed',description TEXT,created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 KEY idx_transactions_user(user_id),FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS password_resets (
 token VARCHAR(255) PRIMARY KEY,user_id INT NOT NULL,created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,expires_at DATETIME NOT NULL,used TINYINT(1) NOT NULL DEFAULT 0,
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS bulletin_posts (
 id INT AUTO_INCREMENT PRIMARY KEY,author_id INT NULL,author_name VARCHAR(255) NOT NULL,title VARCHAR(255) NOT NULL,body TEXT,tag VARCHAR(100),scope VARCHAR(30) NOT NULL DEFAULT 'all',created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(author_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS user_images (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,user_id INT NOT NULL,image_url TEXT NOT NULL,image_type VARCHAR(50) NOT NULL DEFAULT 'profile',sort_order INT NOT NULL DEFAULT 0,is_primary TINYINT(1) NOT NULL DEFAULT 0,created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 KEY idx_user_images_user(user_id),FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS notifications (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,user_id INT NOT NULL,title VARCHAR(255) NOT NULL,message TEXT NOT NULL,kind VARCHAR(50) NOT NULL DEFAULT 'info',link VARCHAR(500),is_read TINYINT(1) NOT NULL DEFAULT 0,created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 KEY idx_notifications_user(user_id,is_read,created_at),FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
