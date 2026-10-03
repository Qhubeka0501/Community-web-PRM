// ==============================
// FORM SUBMIT HANDLER
// ==============================

/*const form = document.getElementById("user-form");
const output = document.getElementById("output");

// Contact form submit: POST the message to the backend and show the response.
form.addEventListener("submit", function(event) {
    event.preventDefault(); // Prevent page reload

    const name = document.getElementById("name").value;
    const surname = document.getElementById("surname").value;

    const base_url = "http://127.0.0.1:5000";

    fetch(`${base_url}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `name=${encodeURIComponent(name)}&surname=${encodeURIComponent(surname)}`
    })
    .then(response => response.json())
    .then(data => {
        // Show success message
        output.innerHTML = `
            <p style="font-size:18px; color:green;">
                Hello <strong>${data.name} ${data.surname}</strong><br>
                Your name is captured.
            </p>
        `;

        output.style.display = "block";
        form.reset(); // Clear inputs
    })
    .catch(error => console.error("Error:", error));
});

*/

// ==============================
// CAROUSEL SLIDER
// ==============================

// ==============================
// EMAIL VERIFICATION MESSAGE
// ==============================
document.addEventListener("DOMContentLoaded", () => {
    const urlParams = new URLSearchParams(window.location.search);
    const verified = urlParams.get("verified");

    if (verified === "1") {
        alert("✅ Your email has been verified! Click the Sign In button to log in.");
        window.history.replaceState({}, document.title, window.location.pathname);
    } else if (verified === "0") {
        alert("❌ Invalid or expired verification link.");
        window.history.replaceState({}, document.title, window.location.pathname);
    }
});

// ==============================
// TESTIMONIAL CAROUSEL
// ==============================
let index = 0;
const slides = document.querySelectorAll(".testimonial");
const carousel = document.querySelector(".carousel");

/**
 * Show the testimonial slide at the given index, wrapping around at both ends.
 */
function showSlide(i) {
    index = (i + slides.length) % slides.length;
    carousel.style.transform = `translateX(${-index * 320}px)`;
}

// Carousel controls: show the next / previous testimonial, and auto-advance every 4 seconds.
document.querySelector(".next").onclick = () => showSlide(index + 1);
document.querySelector(".prev").onclick = () => showSlide(index - 1);
setInterval(() => showSlide(index + 1), 4000);

// ==============================
// MODAL POPUP (SIGN IN POPUP)
// ==============================
const signBtn = document.querySelector(".signBtn");
const modalOverlay = document.querySelector(".modal-overlay");
const modalClose = document.querySelector(".modal-close");

// Open the sign-in modal.
signBtn.addEventListener("click", () => {
    modalOverlay.style.display = "flex";
});

// Close button: hide the sign-in modal and reset the role radios.
modalClose.addEventListener("click", () => {
    modalOverlay.style.display = "none";
    loginEmail.value="";
    loginPassword.value="";
    document.querySelectorAll('input[name="role"]').forEach(radio => {
        radio.checked = false;
    });

});

// Click on the overlay background: close the modal and reset the role radios.
modalOverlay.addEventListener("click", event => {
    if (event.target === modalOverlay) {
        modalOverlay.style.display = "none";
        loginEmail.value="";
        loginPassword.value="";
        document.querySelectorAll('input[name="role"]').forEach(radio => {
            radio.checked = false;
        });

    }
});

// REGISTER BUTTON
document.getElementById("RegBtn").addEventListener("click", () => {
   window.location.href = "/register";
});



// PASSWORD RESET
document.getElementById("forgotPassword").addEventListener("click", (e) => {
    e.preventDefault(); // stops page jump
    window.location.href = "/password_reset";
});





// ==============================
// LOGIN MODAL
// ==============================
document.addEventListener("DOMContentLoaded", () => {
    const loginBtn = document.querySelector(".modalLoginBtn");
    const errorEl = document.getElementById("loginError");
    const passwordInput = document.getElementById("loginPassword");

    // Login click: validate the fields, call /api/auth/login and route the user onwards.
    loginBtn.addEventListener("click", (e) => {
        e.preventDefault();

        errorEl.textContent = "";
        passwordInput.classList.remove("error");

        const email = document.getElementById("loginEmail").value.trim();
        const password = passwordInput.value;
        const roleEl = document.querySelector('input[name="role"]:checked');

        if (!email || !password) {
            errorEl.textContent = "Email and password are required";
            passwordInput.classList.add("error");
            return;
        }

        if (!roleEl) {
            errorEl.textContent = "Please select Buyer or Seller";
            passwordInput.classList.add("error");
            return;
        }

        const role = roleEl.value;

        fetch("/login-user", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({ email, password, role })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                // Save JWT token
                localStorage.setItem("token", data.token);

                // Clear login fields
                document.getElementById("loginEmail").value = "";
                passwordInput.value = "";
                document.querySelectorAll('input[name="role"]').forEach(radio => {
                    radio.checked = false;
                });

                // Redirect based on role
                if (role === "seller") {
                    // Fetch seller dashboard with JWT
                    fetch("/seller/dashboard", {
                        headers: {
                            "Authorization": "Bearer " + data.token
                        }
                    })
                    .then(res => res.text())
                    .then(html => {
                        // Replace body content with seller dashboard
                        document.open();
                        document.write(html);
                        document.close();
                    })
                    .catch(() => {
                        alert("Failed to load seller dashboard. Try again.");
                    });
                } else {
                    // Example: buyer goes to home page
                    window.location.href = "/";
                }

            } else {
                errorEl.textContent = data.message;
                passwordInput.classList.add("error");
            }
        })
        .catch(() => {
            errorEl.textContent = "Something went wrong. Try again.";
            passwordInput.classList.add("error");
        });
    });
});


// ==============================
// BTN PRIMARY TO OPEN SIGN IN MODAL
// ==============================
const btnPrimaryElement = document.querySelectorAll(".btnPrimary");
// Primary buttons: give each one its click behaviour.
btnPrimaryElement.forEach(btn => {
    btn.addEventListener("click", () => {
        modalOverlay.style.display = "flex";
    });
});

// ==============================
// HAMBURGER MENU
// ==============================
const hamburger = document.querySelector(".hamburger");
const mobileMenu = document.querySelector(".mobileMenu");

// Hamburger button: toggle the mobile navigation menu.
hamburger.addEventListener("click", () => {
    hamburger.classList.toggle("active");
    mobileMenu.classList.toggle("show");

    const expanded = hamburger.classList.contains("active");
    hamburger.setAttribute("aria-expanded", expanded);
});















