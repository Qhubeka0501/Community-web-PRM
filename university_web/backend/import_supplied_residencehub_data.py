#!/usr/bin/env python3
"""Import supplied ResidenceHub records without destructive deletes or ID overwrites."""
from db import get_connection
records=[
('vendor','Qhubekani Smith','qhubekani','qhubekaphiwa@gmail.com','d08a3ac3fab7ee8168ce9ab5ef936ba66bcf57812fa00b1a32ff939dce2daeecf5dbe0a080e1a7980411cad6ab18be5707a86bf060bedf9c59c9f41eb0592ee8','632da8fd2964f4a43475fd7b0b4acd81','066 535 8679','QS Trading','Hanover Res','Hanover st, Cput d6',7500,500,120),
('student','Ningabiye A','ningabiye','ningabiye@myresidence.ac.za','d08a3ac3fab7ee8168ce9ab5ef936ba66bcf57812fa00b1a32ff939dce2daeecf5dbe0a080e1a7980411cad6ab18be5707a86bf060bedf9c59c9f41eb0592ee8','632da8fd2964f4a43475fd7b0b4acd81','071 000 1111',None,'Hanover Res','Hanover Res, Room 12',0,0,0),
('student','Avuyile T','avuyile','avuyile@myresidence.ac.za','d08a3ac3fab7ee8168ce9ab5ef936ba66bcf57812fa00b1a32ff939dce2daeecf5dbe0a080e1a7980411cad6ab18be5707a86bf060bedf9c59c9f41eb0592ee8','632da8fd2964f4a43475fd7b0b4acd81','072 000 2222',None,'Hanover Res','Hanover Res, Room 8',0,0,0),
('student','sphelele','qhawesheingmail.com','qhawesheingmail.com','8c1af77312588751f8b62b52e03827343e9a3661eb3780c751fdfc2f3ce884be131fd0ecbbcff4cf6571fd029a3315b6cf4398e6be32295b24d1e88aab6c34b2','82d81fe6fb80d56ee12df579124d7765','0780603273',None,'','',0,0,0)]
products=[('PM Book','Books','Hanover Res',300,24,'PMBOK Guide, 7th edition — the standard for project management.','3rd Edition'),
('iPhone 7','Electronics','Hanover Res',7000,100,'Reliable pre-owned iPhone 7, great battery life, unlocked.','Pre-owned'),
('Nike tekkie','Shoes','Hanover Res',450,50,'Nike sneakers, lightly worn, great condition.','Pre-owned'),
('Lenovo i5','Electronics','Hanover Res',5000,300,'Pre-owned PC, ideal for computer science students. Lenovo IdeaPad 3, Intel Core i5-10210U, 8GB RAM, 256GB SSD, 15.6" FHD.','Pre-owned')]
# Script entry point: run the migration / import steps inside one transaction.
def main():
 c=get_connection();cur=c.cursor(dictionary=True)
 try:
  for r in records:
   cur.execute("SELECT id FROM users WHERE email=%s",(r[3],))
   if cur.fetchone(): continue
   cur.execute("""INSERT INTO users(role,name,username,email,password_hash,password_salt,password_scheme,cellphone,business_name,residence,address,balance,available_balance,pending_balance,is_verified)
   VALUES(%s,%s,%s,%s,%s,%s,'legacy_scrypt',%s,%s,%s,%s,%s,%s,%s,1)""",r)
  cur.execute("SELECT id FROM users WHERE email='qhubekaphiwa@gmail.com'"); seller=cur.fetchone()
  if seller:
   for p in products:
    cur.execute("SELECT id FROM products WHERE seller_id=%s AND name=%s",(seller['id'],p[0]))
    if not cur.fetchone():cur.execute("""INSERT INTO products(seller_id,name,category,residence,price,stock,description,condition_tag,status)
    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'active')""",(seller['id'],*p))
  c.commit();print("Supplied ResidenceHub records imported where no conflict existed.")
 except: c.rollback();raise
 finally:cur.close();c.close()
if __name__=='__main__':main()
