/**
 * Seller tooling script: dashboard section switching, product image upload/preview/
 * reorder, add & edit product validation, size/colour pickers and product deletion.
 */
document.addEventListener("DOMContentLoaded", () => {

    /* ===============================
       HELPER: HIDE ALL SECTIONS
       (FIXES CONTENT STACKING BUG)
    =============================== */
    /**
     * Hide every dashboard section so only the selected one is shown.
     */
    function hideAllSections() {
        const home = document.getElementById("home-section");
        const products = document.getElementById("products-section");
        const productsHeader= document.getElementById("products-section-header");
        const addProduct = document.getElementById("add-product-section");

        if (home) home.style.display = "none";
        if (products) products.style.display = "none";
        if(productsHeader)productsHeader.style.display="none";
        if (addProduct) addProduct.style.display = "none";
    }

    /* ===============================
       HAMBURGER MENU
    =============================== */
    const hamburger = document.getElementById('hamburger');
    const sidebar = document.getElementById('sidebar');

    if (hamburger && sidebar) {
        // Hamburger button: toggle the dashboard's mobile navigation.
        hamburger.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });
    }

    /* ===============================
       CLICKABLE ORDER ROWS
    =============================== */
    // Summary rows: expand or collapse the detail panel for each row.
    document.querySelectorAll('.summary-row').forEach(row => {
        row.addEventListener('click', () => {
            const detailsRow = row.nextElementSibling;
            if (!detailsRow || !detailsRow.classList.contains('details-row')) return;

            const detailsCell = detailsRow.querySelector('td');

            if (detailsRow.style.display === 'table-row') {
                detailsRow.style.display = 'none';
                return;
            }

            detailsCell.innerHTML = `
                <strong>Order Details</strong><br><br>
                <b>Order ID:</b> #${row.dataset.orderId}<br>
                <b>Customer:</b> ${row.dataset.customer}<br>
                <b>Product:</b> ${row.dataset.product}<br>
                <b>Quantity:</b> ${row.dataset.quantity}<br>
                <b>Address:</b> ${row.dataset.address}<br>
                <b>Payment:</b> ${row.dataset.payment}<br>
                <b>Status:</b> ${row.dataset.status}<br>
                <b>Amount:</b> R${row.dataset.amount}<br>
                <b>Notes:</b> ${row.dataset.notes}
            `;

            detailsRow.style.display = 'table-row';
        });
    });

    /* ===============================
       SIDEBAR NAV SWITCHING (FIXED)
    =============================== */
    const navHome = document.getElementById("nav-home");
    const navProducts = document.getElementById("nav-products");

    const homeSection = document.getElementById("home-section");
    const productsSection = document.getElementById("products-section");
    const productSectionHeader=document.getElementById("products-section-header");
    if (navHome && navProducts && homeSection && productsSection) {

        // Dashboard nav: show the overview/home section.
        navHome.addEventListener("click", () => {
            hideAllSections();
            homeSection.style.display = "block";

            navHome.classList.add("active");
            navProducts.classList.remove("active");
        });

        // Dashboard nav: show the products section.
        navProducts.addEventListener("click", () => {
            hideAllSections();
            productsSection.style.display = "block";
            productSectionHeader.style.display="block";
            navProducts.classList.add("active");
            navHome.classList.remove("active");
        });
    }

    /* ===============================
       ADD PRODUCT TOGGLE (FIXED)
    =============================== */
    const addProductSection = document.getElementById("add-product-section");
    const addProductBtn = document.querySelector("#products-section-header .add-btn");
    const backToProductsBtn = document.getElementById("back-to-products");
    const cancelAddBtn = document.getElementById("cancel-add");

    if (addProductBtn) {
        // Add product button: open the empty product form.
        addProductBtn.addEventListener("click", () => {
            hideAllSections();
            addProductSection.style.display = "block";
        });
    }

    if (backToProductsBtn) {
        // Back button: return from the form to the products list.
        backToProductsBtn.addEventListener("click", () => {
            hideAllSections();
            productsSection.style.display = "block";
             productSectionHeader.style.display="block";
        });
    }

    if (cancelAddBtn) {
        // Cancel button: discard the form and go back to the products list.
        cancelAddBtn.addEventListener("click", () => {
            /*hideAllSections();
            productsSection.style.display = "block";
             productSectionHeader.style.display="block";
             */
            clearAddProductForm();

        });
    }

    /* ===============================
       IMAGE CAROUSEL
    =============================== */
  /**
   * Initialise the product image carousel on a card.
   */
  function initCarousel() {
      // Initialise a carousel for every product card image gallery.
      document.querySelectorAll(".image-carousel").forEach(carousel => {

          const img = carousel.querySelector(".cardImg");
          if (!img || !img.dataset.images) return;

          let images;
          try {
              images = JSON.parse(img.dataset.images);
          } catch {
              console.error("Invalid image data:", img.dataset.images);
              return;
          }

          if (images.length <= 1) return;

          let index = 0;
          let startX = 0;
          let endX = 0;

          /**
           * Display the carousel image at the current index.
           */
          const showImage = () => {
              img.src = images[index];
          };

          // Carousel next / previous buttons and swipe gestures.
          carousel.querySelector(".next")?.addEventListener("click", () => {
              index = (index + 1) % images.length;
              showImage();
          });

          carousel.querySelector(".prev")?.addEventListener("click", () => {
              index = (index - 1 + images.length) % images.length;
              showImage();
          });

          // Swipe support
          img.addEventListener("touchstart", e => {
              startX = e.touches[0].clientX;
          });

          img.addEventListener("touchend", e => {
              endX = e.changedTouches[0].clientX;
              const diff = startX - endX;

              if (Math.abs(diff) > 40) {
                  index = diff > 0
                      ? (index + 1) % images.length
                      : (index - 1 + images.length) % images.length;
                  showImage();
              }
          });
      });
  }


    /* ===============================
       DRAG & DROP IMAGE UPLOAD
    =============================== */
    const uploadBox = document.getElementById("upload-box");
    const imageInput = document.getElementById("image-input");
    const imagePreview = document.getElementById("image-preview");

    let selectedImages = [];

    if (uploadBox && imageInput && imagePreview) {

        // Upload box click: open the native file picker.
        uploadBox.addEventListener("click", () => {
            imageInput.click();
        });

        // Drag over / drag leave / drop: highlight the upload box and accept dropped images.
        uploadBox.addEventListener("dragover", e => {
            e.preventDefault();
            uploadBox.style.borderColor = "#2563eb";
            uploadBox.style.background = "#eef2ff";
        });

        uploadBox.addEventListener("dragleave", () => {
            uploadBox.style.borderColor = "#cbd5e1";
            uploadBox.style.background = "#f8fafc";
        });

        uploadBox.addEventListener("drop", e => {
            e.preventDefault();
            uploadBox.style.borderColor = "#cbd5e1";
            uploadBox.style.background = "#f8fafc";
            handleFiles(e.dataTransfer.files);
        });

        // File input change: run the dropped or chosen files through validation.
        imageInput.addEventListener("change", () => {
            handleFiles(imageInput.files);
        });
    }





   /* function handleFiles(files) {
        for (let file of files) {
            if (!file.type.startsWith("image/")) continue;

            if (selectedImages.length >= 20) {
                alert("Maximum 20 images allowed");
                break;
            }

            selectedImages.push(file);

            const reader = new FileReader();
            reader.onload = e => {
                const img = document.createElement("img");
                img.src = e.target.result;
                imagePreview.appendChild(img);
            };
            reader.readAsDataURL(file);
        }
    }*/


// PAGINATED IMAGE PREVIEW
const previewContainer = document.getElementById("image-preview-container");
const previewInner = document.getElementById("image-preview");
const prevBtn = document.getElementById("preview-prev");
const nextBtn = document.getElementById("preview-next");

let currentPage = 0;
const pageSize = 4; // PC: 2x2

/**
 * Re-render the selected-image thumbnails and their order.
 */
function updatePreview() {
    const items = previewInner.querySelectorAll(".preview-item");

    if (items.length === 0) {
        if (prevBtn) prevBtn.style.display = "none";
        if (nextBtn) nextBtn.style.display = "none";
        return;
    }

    const isMobile = window.innerWidth <= 768;

    if (isMobile) {
        items.forEach((item, idx) => {
            item.style.display = idx === currentPage ? "block" : "none";
        });

        prevBtn.style.display = currentPage > 0 ? "flex" : "none";
        nextBtn.style.display = currentPage < items.length - 1 ? "flex" : "none";

    } else {
        const start = currentPage * pageSize;
        const end = start + pageSize;

        items.forEach((item, idx) => {
            item.style.display = idx >= start && idx < end ? "block" : "none";
        });

        prevBtn.style.display = currentPage === 0 ? "none" : "flex";
        nextBtn.style.display = end < items.length ? "flex" : "none";
    }
}

// ARROWS
if (prevBtn && nextBtn) {
    // Preview navigation: scroll the selected-image strip left or right.
    prevBtn.addEventListener("click", () => {
        currentPage = Math.max(0, currentPage - 1);
        updatePreview();
    });

    nextBtn.addEventListener("click", () => {
        const items = previewInner.querySelectorAll(".preview-item");
        const isMobile = window.innerWidth <= 768;

        if (isMobile) {
            currentPage = Math.min(items.length - 1, currentPage + 1);
        } else {
            currentPage = Math.min(
                Math.floor((items.length - 1) / pageSize),
                currentPage + 1
            );
        }

        updatePreview();
    });
}

// ===============================
// IMAGE ADD + REMOVE + REORDER
// ===============================
function handleFiles(files) {
    for (let file of files) {
        if (!file.type.startsWith("image/")) continue;

        if (selectedImages.length >= 20) {
            alert("Maximum 20 images allowed");
            break;
        }

        selectedImages.push(file);

        const reader = new FileReader();
        reader.onload = e => {

            const wrapper = document.createElement("div");
            wrapper.className = "preview-item";
            wrapper.draggable = true;

            const img = document.createElement("img");
            img.src = e.target.result;

            const removeBtn = document.createElement("button");
            removeBtn.className = "remove-image";
            removeBtn.innerHTML = "×";

            // REMOVE IMAGE
            removeBtn.addEventListener("click", () => {
                const index = [...previewInner.children].indexOf(wrapper);
                selectedImages.splice(index, 1);
                wrapper.remove();
                currentPage = Math.max(0, currentPage - 1);
                updatePreview();
            });

            // DRAG EVENTS
            wrapper.addEventListener("dragstart", () => {
                wrapper.classList.add("dragging");
            });

            wrapper.addEventListener("dragend", () => {
                wrapper.classList.remove("dragging");
                syncSelectedImages();
            });

            wrapper.appendChild(img);
            wrapper.appendChild(removeBtn);
            previewInner.appendChild(wrapper);

            updatePreview();
        };

        reader.readAsDataURL(file);
    }
}

// ===============================
// DRAG & DROP REORDER LOGIC
// ===============================
previewInner.addEventListener("dragover", e => {
    e.preventDefault();
    const dragging = document.querySelector(".dragging");
    const afterElement = getDragAfterElement(previewInner, e.clientY);
    if (afterElement == null) {
        previewInner.appendChild(dragging);
    } else {
        previewInner.insertBefore(dragging, afterElement);
    }
});

/**
 * Work out which thumbnail the dragged image should be dropped after.
 */
function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll(".preview-item:not(.dragging)")];

    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;

        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

// ===============================
// KEEP FILE ORDER IN SYNC
// ===============================
function syncSelectedImages() {
    const newOrder = [];
    previewInner.querySelectorAll(".preview-item img").forEach((img, idx) => {
        newOrder.push(selectedImages[idx]);
    });
    selectedImages = newOrder;
}



// HELPER METHODS FOR THE VALIDATION OF ADDING PRODUCT

/**
 * Mark an input as invalid and show its validation message.
 */
function showError(element, message) {
    const wrapper = element.closest(".form-group") || element;
    const error = wrapper.querySelector(".error-msg");

    if (!error) return;

    wrapper.classList.add("error");
    error.textContent = message;
    error.style.display = "block";
}

/**
 * Remove the validation message from a field.
 */
function clearError(element) {
    const wrapper = element.closest(".form-group") || element;
    const error = wrapper.querySelector(".error-msg");

    if (!error) return;

    wrapper.classList.remove("error");
    error.textContent = "";
    error.style.display = "none";
}


//FUNCTION VALIDATE PRODUCT ADD
function validateAddProductForm() {
    let valid = true;

    const name = document.querySelector("input[placeholder='Enter product name']");
    const category = document.querySelector(".form-group select");
    const residence = document.querySelector("input[placeholder='Residence']");
    const price = document.querySelectorAll("input[type='number']")[0];
    const stock = document.querySelectorAll("input[type='number']")[1];
    const status = document.getElementById("product-status");
    const description = document.querySelector("textarea");
    const uploadBox = document.getElementById("upload-box");

    // Clear previous errors
    [name, category, residence, price, stock, status, description].forEach(clearError);
    uploadBox.classList.remove("error");
    uploadBox.querySelector(".error-msg").style.display = "none";

    if (!name.value.trim()) {
        showError(name, "This field is required");
        valid = false;
    }

    if (!category.value || category.value === "Select category") {
        showError(category, "Please select a category");
        valid = false;
    }

    if (!residence.value.trim()) {
        showError(residence, "Residence is required");
        valid = false;
    }

    if (!price.value || price.value <= 0) {
        showError(price, "Enter a valid price");
        valid = false;
    }

    if (!stock.value || stock.value < 0) {
        showError(stock, "Enter stock quantity");
        valid = false;
    }

    if (!status.value) {
        showError(status, "Select product status");
        valid = false;
    }

    if (!description.value.trim()) {
        showError(description, "Description is required");
        valid = false;
    }

    if (selectedImages.length === 0) {
        uploadBox.classList.add("error");
        const err = uploadBox.querySelector(".error-msg");
        err.textContent = "At least one image is required";
        err.style.display = "block";
        valid = false;
    }

    return valid;
}







/* SAVING THE PRODUCT TO THE DATABASE */
document.querySelector(".save").addEventListener("click", () => {


       if (!validateAddProductForm()) {
           return; // ❌ stop here if invalid
       }

    const formData = new FormData();

    formData.append("name", document.querySelector("input[placeholder='Enter product name']").value);
    formData.append("category", document.querySelector("select").value);
    formData.append("price", document.querySelectorAll("input[type='number']")[0].value);
    formData.append("stock", document.querySelectorAll("input[type='number']")[1].value);
    formData.append("description", document.querySelector("textarea").value);
    formData.append("residence",document.querySelector("input[placeholder='Residence']").value);
    // ✅ MULTIPLE SIZES
    formData.append("sizes", sizesHidden.value);

    // ✅ MULTIPLE COLORS (prepare for later)
    formData.append("colors", colorsHidden?.value || "[]");

    const statusSelect = document.getElementById("product-status");
    formData.append("status", statusSelect ? statusSelect.value : "");

    // ✅ IMAGES (KEY MUST MATCH FLASK)
    selectedImages.forEach(file => {
        formData.append("images", file);
    });





    fetch("/seller/products", {
        method: "POST",
          headers: {
                "Authorization": "Bearer " + localStorage.getItem("token")
            },

        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("Product saved successfully");
            clearAddProductForm();
           getProductReusable();
        } else if(data.error) {
           // back to login page
           alert("Session expired");
            localStorage.removeItem("token");
             window.location.href = "/";

        }
    })
    .catch(err => {
        console.error(err);
        alert("Failed to save product");
    });
});






// ===== SIZE HANDLING =====
const sizeOptions = document.getElementById("size-options");
const customSizeInput = document.getElementById("custom-size-input");
const addSizeBtn = document.getElementById("add-size-btn");
const sizesHidden = document.getElementById("sizes-hidden");

let selectedSizes = [];

// Update hidden input
function updateSizesHidden() {
    sizesHidden.value = JSON.stringify(selectedSizes);
}

// Checkbox changes
sizeOptions.addEventListener("change", (e) => {
    if (e.target.type === "checkbox") {
        const value = e.target.value;

        if (e.target.checked) {
            if (!selectedSizes.includes(value)) {
                selectedSizes.push(value);
            }
        } else {
            selectedSizes = selectedSizes.filter(size => size !== value);
        }

        updateSizesHidden();
    }
});

// Add custom size
addSizeBtn.addEventListener("click", () => {
    const value = customSizeInput.value.trim();

    if (!value) return;

    if (selectedSizes.includes(value)) {
        alert("Size already added");
        return;
    }

    // Add checkbox dynamically
    const label = document.createElement("label");
    const checkbox = document.createElement("input");

    checkbox.type = "checkbox";
    checkbox.value = value;
    checkbox.checked = true;

    label.appendChild(checkbox);
    label.append(" " + value);

    sizeOptions.appendChild(label);

    selectedSizes.push(value);
    updateSizesHidden();

    customSizeInput.value = "";
});





// ===== COLOR HANDLING =====
const colorOptions = document.getElementById("color-options");
const customColorInput = document.getElementById("custom-color-input");
const addColorBtn = document.getElementById("add-color-btn");
const colorsHidden = document.getElementById("colors-hidden");

let selectedColors = [];

// Update hidden input
function updateColorsHidden() {
    colorsHidden.value = JSON.stringify(selectedColors);
}

// Checkbox changes
colorOptions.addEventListener("change", (e) => {
    if (e.target.type === "checkbox") {
        const value = e.target.value;

        if (e.target.checked) {
            if (!selectedColors.includes(value)) {
                selectedColors.push(value);
            }
        } else {
            selectedColors = selectedColors.filter(color => color !== value);
        }

        updateColorsHidden();
    }
});

// Add custom color
addColorBtn.addEventListener("click", () => {
    const value = customColorInput.value.trim();

    if (!value) return;

    if (selectedColors.includes(value)) {
        alert("Color already added");
        return;
    }

    const label = document.createElement("label");
    const checkbox = document.createElement("input");

    checkbox.type = "checkbox";
    checkbox.value = value;
    checkbox.checked = true;

    label.appendChild(checkbox);
    label.append(" " + value);

    colorOptions.appendChild(label);

    selectedColors.push(value);
    updateColorsHidden();

    customColorInput.value = "";
});



getProductReusable();




/**
 * Build the reusable product card markup used across seller views.
 */
function getProductReusable(){
const token = localStorage.getItem("token");
const productGrid = document.getElementById("productGrid");
const pgreenCard= document.querySelector(".stat-card.green p");
fetch("/seller/products", {
    headers: {
        "Authorization": "Bearer " + token
    }
})
.then(res => res.json())
.then(data=> {
    productGrid.innerHTML = "";

   pgreenCard.textContent = data.total_products;
    const products = data.products;
    products.forEach(product => {
        const images = product.images.length
            ? product.images
            : ["/static/images/place.jpg"];

        const card = document.createElement("div");
        card.className = "product-card";

        card.innerHTML = `
            <div class="image-carousel">
                <button class="nav prev">&#10094;</button>

                <img
                    src="${images[0]}"
                    class="cardImg"
                    data-images='${JSON.stringify(images)}'
                >

                <button class="nav next">&#10095;</button>
            </div>

            <div class="card-body">
                <h3>${product.name}</h3>
                <p class="price">R ${product.price}</p>

                <span class="badge ${product.status === "active" ? "active" : ""}">
                    ${product.status}
                </span>
                <span class="badge category">${product.category}</span>

                <p><strong>Stock:</strong> ${product.stock}</p>
                <p class="Residence"> <strong>Residence:</strong> ${product.residence}</p>

                <p class="description">
                    ${product.description}
                </p>
            </div>

            <div class="card-actions">
                <button class="edit" data-id="${product.id}">Edit</button>
                <button class="delete" data-id="${product.id}">Delete</button>
            </div>

        `;

        productGrid.appendChild(card);
    });

    initCarousel(); // reuse your existing carousel logic
});


}
//DELETE PRODUCT LOGIC
let productToDelete = null;
let cardToDelete = null;

// Delegated click handler: react to edit, delete and modal buttons on product cards.
document.addEventListener("click", function (e) {

    // DELETE BUTTON CLICK
    if (e.target.classList.contains("delete")) {
        productToDelete = e.target.dataset.id;
        cardToDelete = e.target.closest(".product-card");

        document.getElementById("deleteModal").classList.remove("hidden");
    }

    // CANCEL DELETE
    if (e.target.id === "cancelDelete") {
        closeDeleteModal();
    }

    // CONFIRM DELETE
    if (e.target.id === "confirmDelete") {
        deleteProduct(productToDelete, cardToDelete);
        closeDeleteModal();
    }
});

/**
 * Close the delete-confirmation modal.
 */
function closeDeleteModal() {
    document.getElementById("deleteModal").classList.add("hidden");
    productToDelete = null;
    cardToDelete = null;
}

/**
 * Delete/archive a listing and remove its card from the page after confirmation.
 */
function deleteProduct(productId, cardElement) {
    fetch("/seller/delete-product", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + localStorage.getItem("token")
        },
        body: JSON.stringify({ product_id: productId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            cardElement.remove();
        } else if(data.error) {
            alert("Session expired");
            localStorage.removeItem("token");
             window.location.href = "/";
        }
    })
    .catch(err => {
        console.error(err);
        alert("Server error");
    });
}

/**
 * Reset the add product form back to its empty state.
 */
function clearAddProductForm(){
 // selecting the documennt (add-product_section) with everything that is an input type
 document.querySelectorAll("#add-product-section input[type='text'], #add-product-section input[type='number']").
 forEach(input=> {input.value=""});// every input must set to an empty

 document.querySelector("#add-product-section textarea").value="";
 document.querySelectorAll("#add-product-section select").
 forEach(select=> {select.selectedIndex=0});
 document.querySelectorAll("#add-product-section input[type='checkbox']").
 forEach(cb=>{cb.checked=false});

 document.getElementById("colors-hidden").value="";
 document.getElementById("sizes-hidden").value="";

document.getElementById("image-input").value="";

 document.getElementById("image-preview").innerHTML="";

}


});

