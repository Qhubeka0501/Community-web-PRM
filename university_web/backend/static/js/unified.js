/**
 * Shared frontend script for every ResidenceHub page: a small fetch wrapper around
 * the Flask JSON API plus the per-page loaders (marketplace, product, cart, orders,
 * wallet, profile, bulletin, seller dashboard, auth forms and the home page).
 */
const API='/api';
/**
 * Fetch wrapper for the Flask JSON API: sends session cookies, parses JSON and throws the server's
 * error message when the response is not ok.
 */
async function api(path,opts={}){const method=(opts.method||'GET').toUpperCase();const headers=new Headers(opts.headers||{});if(!['GET','HEAD','OPTIONS'].includes(method)){const token=document.cookie.split('; ').find(x=>x.startsWith('csrf_token='))?.split('=')[1];if(token)headers.set('X-CSRF-Token',decodeURIComponent(token))}const r=await fetch(API+path,{credentials:'same-origin',...opts,headers});let d={};try{d=await r.json()}catch{}if(!r.ok)throw new Error(d.error||'Request failed');return d}
/**
 * HTML-escape a value before it is injected into a template string.
 */
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
/**
 * Turn a stored relative image path into a /static URL, falling back to the placeholder image.
 */
function img(p){return p?'/static/'+p:'/static/images/placeholder.jpg'}
/**
 * Render the marketplace product card markup for one product.
 */
function productCard(p){return `<article class="product-card"><a href="/product/${p.id}"><img src="${img(p.images?.[0]?.image_url)}" alt="${esc(p.name)}" loading="lazy"></a><div class="product-card-content"><a href="/product/${p.id}"><h3>${esc(p.name)}</h3></a><div class="meta">${esc(p.category)} · ${esc(p.condition_tag||'Available')}</div><div class="price">R ${Number(p.price).toFixed(2)}</div><div class="meta">${esc(p.seller?.name||'Seller')}</div></div></article>`}
/**
 * Marketplace page: fill the category filter, then search and render the product grid.
 */
async function loadMarketplace(){try{const cats=await api('/products/categories');const c=document.querySelector('#category');cats.categories.forEach(x=>c.insertAdjacentHTML('beforeend',`<option value="${esc(x.category)}">${esc(x.category)} (${x.count})</option>`));async function search(){const q=new URLSearchParams({q:document.querySelector('#search').value,category:c.value,condition:document.querySelector('#condition').value});const d=await api('/products?'+q);document.querySelector('#product-grid').innerHTML=d.products.length?d.products.map(productCard).join(''):'<p class="empty">No products found.</p>'}document.querySelector('#search-btn').onclick=search;document.querySelector('#search').addEventListener('keydown',e=>{if(e.key==='Enter')search()});await search()}catch(e){toast(e.message)}}
/**
 * Product page: render the gallery, details, seller link and the add-to-cart action.
 */
async function loadProduct(id){try{const {product:p}=await api('/products/'+id);const pics=p.images||[];document.querySelector('#product-detail').innerHTML=`<div><img id="main-image" class="gallery-main" src="${img(pics[0]?.image_url)}" alt="${esc(p.name)}"><div class="thumbs">${pics.map((x,i)=>`<img src="${img(x.image_url)}" alt="${esc(p.name)} image ${i+1}" onclick="document.querySelector('#main-image').src=this.src">`).join('')}</div></div><div class="product-detail-info"><p class="eyebrow">${esc(p.category)}</p><h1>${esc(p.name)}</h1><div class="price">R ${Number(p.price).toFixed(2)}</div><p>${esc(p.description||'No description provided.')}</p><p><b>Condition:</b> ${esc(p.condition_tag||'Not specified')}</p><p><b>Stock:</b> ${p.stock}</p><p><b>Seller:</b> ${esc(p.seller?.name||'')}</p><div class="product-detail-actions"><input id="qty" type="number" min="1" max="${p.stock}" value="1" aria-label="Quantity"><button class="button" id="add-cart" ${p.stock<1?'disabled':''}>Add to cart</button></div></div>`;document.querySelector('#add-cart').onclick=async()=>{try{await api('/cart/items',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({productId:p.id,quantity:+document.querySelector('#qty').value})});toast('Added to cart');refreshChrome()}catch(e){toast(e.message)}}}catch(e){toast(e.message)}}
/**
 * Cart page: render items grouped per seller with totals and wire up checkout.
 */
async function loadCart(){try{const d=await api('/cart');const root=document.querySelector('#cart');root.innerHTML=d.groups.length?d.groups.map(g=>`<div class="cart-group"><h3>${esc(g.seller.name)}</h3>${g.items.map(i=>`<div class="cart-item"><img src="${img(i.product.images?.[0]?.image_url)}"><div><b>${esc(i.product.name)}</b><div>R ${Number(i.lineTotal).toFixed(2)}</div></div><input style="width:80px" type="number" min="0" value="${i.quantity}" onchange="updateCart(${i.cartItemId},this.value)"><button class="danger" onclick="updateCart(${i.cartItemId},0)">Remove</button></div>`).join('')}<b>Seller subtotal: R ${Number(g.subtotal).toFixed(2)}</b></div>`).join('')+`<h2>Total: R ${Number(d.total).toFixed(2)}</h2>`:'<p class="empty">Your cart is empty.</p>';document.querySelector('#checkout').onclick=checkout}catch(e){toast(e.message)}}
/**
 * Change or remove a cart line, then re-render the cart and header counters.
 */
async function updateCart(id,q){try{await api('/cart/items/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({quantity:+q})});loadCart();refreshChrome()}catch(e){toast(e.message)}}
/**
 * Create orders from the cart and confirm the demo payment.
 */
async function checkout(){try{const d=await api('/orders/checkout',{method:'POST'});const card=await demoPaymentDialog();if(!card)return;await api('/payments/confirm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({orderIds:d.orderIds,method:'card',cardNumber:card})});toast('Demo payment completed. No real charge was made.','success');setTimeout(()=>location.href='/orders',700)}catch(e){toast(e.message,'error')}}
function demoPaymentDialog(){return new Promise(resolve=>{const wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal" role="dialog" aria-modal="true" aria-labelledby="demo-payment-title"><button class="modal-close" type="button" aria-label="Close">×</button><p class="eyebrow">DEMO CHECKOUT</p><h2 id="demo-payment-title">Confirm demo payment</h2><p>This is a testing payment flow. No real card charge is made and the number is not stored.</p><label for="demo-card">Test card number</label><input id="demo-card" inputmode="numeric" autocomplete="off" placeholder="Enter any test number"><div class="modal-actions"><button class="button secondary" type="button" data-cancel>Cancel</button><button class="button" type="button" data-confirm>Confirm demo payment</button></div></div>`;document.body.appendChild(wrap);const close=()=>{wrap.remove();resolve(null)};wrap.querySelector('.modal-close').onclick=close;wrap.querySelector('[data-cancel]').onclick=close;wrap.querySelector('[data-confirm]').onclick=()=>{const value=wrap.querySelector('#demo-card').value.trim();if(!value){toast('Enter a test card number to continue.','error');return}wrap.remove();resolve(value)};wrap.querySelector('#demo-card').focus()})}
function setOrderTab(button,seller){document.querySelectorAll('.tabs .tab').forEach(x=>x.classList.remove('active'));button?.classList.add('active')}
/**
 * Orders page: list orders for the buyer, or for the seller when called with seller=true.
 */
async function loadOrders(seller){try{const d=await api('/orders?as='+(seller?'seller':'buyer'));document.querySelector('#orders').innerHTML=d.orders.length?d.orders.map(o=>`<article class="order-card"><h3>Order #${o.id} · ${esc(o.status)}</h3>${o.items.map(i=>`<div>${esc(i.name)} × ${i.quantity} — R ${Number(i.price).toFixed(2)}</div>`).join('')}<p><b>Total: R ${Number(o.total).toFixed(2)}</b></p></article>`).join(''):'<p class="empty">No orders yet.</p>'}catch(e){toast(e.message)}}
/**
 * Wallet page: render balances, transactions and the deposit/withdraw forms.
 */
async function loadWallet(){try{const d=await api('/wallet');document.querySelector('#wallet-balances').innerHTML=stat('Balance',d.balance)+stat('Available',d.availableBalance)+stat('Pending',d.pendingBalance);document.querySelector('#transactions').innerHTML=d.transactions.map(t=>`<article class="order-card"><b>${esc(t.type)}</b> · R ${Number(t.amount).toFixed(2)}<div class="meta">${esc(t.description||'')} · ${esc(t.createdAt)}</div></article>`).join('')||'<p class="empty">No transactions.</p>';document.querySelector('#deposit-form').onsubmit=e=>walletAction(e,'/wallet/deposit');document.querySelector('#withdraw-form').onsubmit=e=>walletAction(e,'/wallet/withdraw')}catch(e){toast(e.message)}}
/**
 * Render one labelled money statistic tile.
 */
function stat(a,b){return `<div class="stat"><span>${a}</span><b>R ${Number(b).toFixed(2)}</b></div>`}
/**
 * Submit a wallet deposit or withdrawal form, then refresh the wallet.
 */
async function walletAction(e,path){e.preventDefault();try{await api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({amount:e.target.amount.value})});loadWallet()}catch(x){toast(x.message)}}
/**
 * Profile page: show the user's details and handle profile updates and image upload.
 */
async function loadProfile(){try{const {profile:p}=await api('/users/me');document.querySelector('#profile').innerHTML=`${p.profile_image_url?`<img style="width:100px;height:100px;border-radius:50%;object-fit:cover" src="${img(p.profile_image_url)}">`:''}<h2>${esc(p.name)}</h2><p>${esc(p.role)} · ${esc(p.email)}</p>`;for(const k of ['name','cellphone','residence','address'])document.querySelector(`[name="${k}"]`).value=p[k]||'';document.querySelector('#profile-form').onsubmit=async e=>{e.preventDefault();try{await api('/users/me',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(e.target))) });toast('Profile saved');loadProfile()}catch(x){toast(x.message)}};document.querySelector('#profile-image-form').onsubmit=async e=>{e.preventDefault();try{await api('/users/me/profile-image',{method:'POST',body:new FormData(e.target)});loadProfile()}catch(x){toast(x.message)}}}catch(e){location.href='/login'}}
/**
 * Bulletin page: list community posts and handle new posts.
 */
async function loadBulletin(){try{const d=await api('/bulletin');document.querySelector('#bulletin').innerHTML=d.posts.map(p=>`<article class="post"><h3>${esc(p.title)}</h3><p>${esc(p.body||'')}</p><span class="meta">${esc(p.author_name)} ${esc(p.tag||'')} · ${esc(p.scope)}</span></article>`).join('');document.querySelector('#bulletin-form').onsubmit=async e=>{e.preventDefault();try{await api('/bulletin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(e.target)))});e.target.reset();loadBulletin()}catch(x){toast(x.message)}}}catch(e){toast(e.message)}}
/**
 * Seller dashboard: render sales statistics and the seller's own listings.
 */
async function loadSellerDashboard(){try{const d=await api('/orders/seller-stats');document.querySelector('#seller-stats').innerHTML=stat('Orders',d.totalOrders)+stat('Deliveries',d.deliveries)+stat('Products',d.myProducts)+stat('Balance',d.balance);const p=await api('/seller/products');document.querySelector('#seller-products').innerHTML=p.products.map(x=>`<div class="seller-listing">${productCard(x)}<a class="button secondary listing-edit" href="/seller/products/${x.id}/edit">Edit product</a></div>`).join('')||'<p class="empty">You have no products yet. Create your first listing to get started.</p>'}catch(e){toast(e.message);if(String(e.message).includes('Authentication'))location.href='/login'}}
/**
 * Wire up the add/edit product form: image selection, sizes, colours and submit.
 */
function initProductForm(){const f=document.querySelector('#product-form');const pid=f.dataset.productId;f.images.onchange=()=>document.querySelector('#image-preview').innerHTML=[...f.images.files].map(x=>`<span class="small">${esc(x.name)}</span>`).join(' ');f.onsubmit=async e=>{e.preventDefault();const fd=new FormData(f);try{['sizes','colors'].forEach(k=>{try{JSON.parse(fd.get(k)||'[]')}catch{throw new Error(k+' must be valid JSON')}});const d=await api(pid?'/products/'+pid:'/products',{method:pid?'PUT':'POST',body:fd});if(pid)location.href='/seller/dashboard';else location.href='/product/'+d.product_id}catch(x){toast(x.message)}}}
/**
 * Wire up the login form and redirect after a successful sign in.
 */
function initLogin(){document.querySelector('#login-form').onsubmit=async e=>{e.preventDefault();clearFormError(e.target);try{await api('/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(e.target)))});location.href='/marketplace'}catch(x){showFormError(e.target,x.message)}}}

/**
 * Wire up registration and move the user to the verification step.
 */
function initRegister(){document.querySelector('#register-form').onsubmit=async e=>{e.preventDefault();clearFormError(e.target);try{const d=await api('/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(e.target)))});sessionStorage.setItem('verificationEmail',e.target.email.value.trim().toLowerCase());location.href='/verification-pending?email='+encodeURIComponent(e.target.email.value.trim().toLowerCase())}catch(x){showFormError(e.target,x.message)}}}

function initVerificationPending(email){const button=document.querySelector('#resend-verification');button?.addEventListener('click',async()=>{button.disabled=true;button.textContent='Sending…';try{const d=await api('/auth/resend-verification',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email})});toast(d.message,'success')}catch(e){toast(e.message,'error')}finally{button.disabled=false;button.textContent='Resend verification email'}})}

/**
 * Wire up the 'send me a reset link' form.
 */
function initRequestReset(){document.querySelector('#request-reset-form').onsubmit=async e=>{e.preventDefault();try{const d=await api('/auth/request-reset',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(e.target)))});toast(d.message)}catch(x){toast(x.message)}}}
/**
 * Wire up the 'set a new password' form.
 */
function initPerformReset(){document.querySelector('#perform-reset-form').onsubmit=async e=>{e.preventDefault();try{await api('/auth/perform-reset',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(e.target)))});location.href='/login'}catch(x){toast(x.message)}}}
function clearFormError(form){form.querySelector('.form-error')?.remove()}
function showFormError(form,message){clearFormError(form);const box=document.createElement('div');box.className='form-error';box.setAttribute('role','alert');box.textContent=message;form.prepend(box)}
function toast(message,type='info'){const region=document.querySelector('#toast-region');if(!region){return}const item=document.createElement('div');item.className='toast '+type;item.textContent=message;region.appendChild(item);requestAnimationFrame(()=>item.classList.add('show'));setTimeout(()=>{item.classList.remove('show');setTimeout(()=>item.remove(),220)},3800)}
function initPasswordToggles(){document.querySelectorAll('.password-toggle').forEach(button=>button.addEventListener('click',()=>{const input=document.getElementById(button.dataset.target);if(!input)return;const show=input.type==='password';input.type=show?'text':'password';button.textContent=show?'Hide':'Show';button.setAttribute('aria-label',show?'Hide password':'Show password')}))}

/**
 * Refresh shared header state such as the cart counter and notification badge.
 */
async function refreshChrome(){
  try{const me=await api('/auth/me');const auth=document.querySelector('#auth-link');if(auth){auth.textContent='Sign out';auth.href='#';auth.classList.add('account-link');auth.onclick=async e=>{e.preventDefault();try{await api('/auth/logout',{method:'POST'});location.href='/'}catch(x){toast(x.message,'error')}}}const seller=document.querySelector('#seller-nav');if(seller)seller.hidden=!me.user.can_sell;}catch{const seller=document.querySelector('#seller-nav');if(seller)seller.hidden=true}
  try{const c=await api('/cart');const count=document.querySelector('#cart-count');if(count)count.textContent=c.itemCount||''}catch{}
  try{const n=await api('/notifications');const unread=n.notifications.filter(x=>!x.is_read);const count=document.querySelector('#notification-count');if(count)count.textContent=unread.length||'';const button=document.querySelector('#notification-button');const panel=document.querySelector('#notification-panel');button?.addEventListener('click',()=>{panel.classList.toggle('hidden');button.setAttribute('aria-expanded',String(!panel.classList.contains('hidden')));panel.innerHTML=n.notifications.map(x=>`<article class="notification-item ${x.is_read?'':'unread'}"><b>${esc(x.title)}</b><p>${esc(x.message)}</p></article>`).join('')||'<p class="empty">No notifications yet.</p>'})}catch{}
}

document.addEventListener('DOMContentLoaded',()=>{const toggle=document.querySelector('.nav-toggle');toggle?.addEventListener('click',()=>{const nav=document.querySelector('#main-nav');const open=nav.classList.toggle('open');toggle.setAttribute('aria-expanded',String(open))});initPasswordToggles();refreshChrome()});
/**
 * Home page: render the first eight live products and handle the hero search form.
 */
async function loadHome(){
  const grid=document.querySelector('#home-product-grid');
  const form=document.querySelector('#home-search-form');
  if(!grid)return;
  /**
   * Fetch products for the current query and paint them into the home grid.
   */
  async function render(query=''){
    try{
      grid.innerHTML='<p class="home-products-loading">Loading products...</p>';
      const params=new URLSearchParams({q:query});
      const d=await api('/products?'+params.toString());
      const products=(d.products||[]).slice(0,8);
      grid.innerHTML=products.length?products.map(homeProductCard).join(''):'<div class="home-empty">No products found.</div>';
    }catch(e){
      grid.innerHTML='<div class="home-empty">Unable to load products right now.</div>';
      toast(e.message);
    }
  }
  form?.addEventListener('submit',e=>{e.preventDefault();render(document.querySelector('#home-search').value.trim())});
  await render();
}

/**
 * Render the home page product card markup for one product.
 */
function homeProductCard(p){
  const image=img(p.images?.[0]?.image_url);
  const price=Number(p.price||0).toFixed(2);
  const condition=esc(p.condition_tag||'Available');
  const seller=esc(p.seller?.name||'ResidenceHub seller');
  return `<article class="home-product-card">
    <a class="home-product-image-wrap" href="/product/${p.id}">
      <img class="home-product-image" src="${image}" alt="${esc(p.name)}" loading="lazy">
      <span class="home-product-badge">${condition}</span>
    </a>
    <div class="home-product-body">
      <p class="home-product-category">${esc(p.category||'Product')}</p>
      <a class="home-product-title" href="/product/${p.id}">${esc(p.name)}</a>
      <div class="home-product-footer">
        <div>
          <strong class="home-product-price">R ${price}</strong>
          <span class="home-product-seller">${seller}</span>
        </div>
        <a class="home-product-action" href="/product/${p.id}" aria-label="View ${esc(p.name)}">View</a>
      </div>
    </div>
  </article>`;
}
