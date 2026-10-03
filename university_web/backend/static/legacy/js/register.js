// FOR REGISTERING AN ACCOUNT
document.addEventListener("DOMContentLoaded", () => {

    const regBtn = document.querySelector(".registerBtn");
    if (!regBtn) return;

    const spinner = document.createElement("span");
    spinner.style.display = "none";
    spinner.style.marginLeft = "8px";
    spinner.innerHTML = "⏳";
    regBtn.appendChild(spinner);

    const fields = {
        name: document.getElementById("nameInput"),
        email: document.getElementById("emailInput"),
        password: document.getElementById("passwordInput"),
        confirm: document.getElementById("confirmInput"),
        roleError: document.getElementById("roleError")
    };

    const errors = {
        name: document.getElementById("nameError"),
        email: document.getElementById("emailError"),
        password: document.getElementById("passwordError"),
        confirm: document.getElementById("confirmError")
    };

    /**
     * Clear all validation messages and error styling from the form.
     */
    function clearErrors() {
        Object.values(errors).forEach(e => e.textContent = "");
        fields.roleError.textContent = "";
        document.querySelectorAll(".register-input").forEach(i => i.classList.remove("error"));
    }

    /**
     * Mark an input as invalid and show its validation message.
     */
    function showError(input, errorEl, message) {
        input.classList.add("error");
        errorEl.textContent = message;
    }

    // Register click: validate every field, then POST the new account to /api/auth/register.
    regBtn.addEventListener("click", (e) => {
        e.preventDefault();
        clearErrors();

        const fullName = fields.name.value.trim();
        const email = fields.email.value.trim();
        const password = fields.password.value;
        const confirm = fields.confirm.value;
        const roleEl = document.querySelector('input[name="role"]:checked');

        let hasError = false;

        if (!fullName) {
            showError(fields.name, errors.name, "Full name is required");
            hasError = true;
        }

        if (!email) {
            showError(fields.email, errors.email, "Email is required");
            hasError = true;
        }

        if (!password) {
            showError(fields.password, errors.password, "Password is required");
            hasError = true;
        }

        if (password && password.length < 8) {
            showError(fields.password, errors.password, "Password must be at least 8 characters");
            hasError = true;
        }

        if (password !== confirm) {
            showError(fields.confirm, errors.confirm, "Passwords do not match");
            hasError = true;
        }

        if (!roleEl) {
            fields.roleError.textContent = "Please select Buyer or Seller";
            hasError = true;
        }

        if (hasError) return;

        // Disable button
        regBtn.disabled = true;
        regBtn.textContent = "Registering...";
        spinner.style.display = "inline-block";

        fetch("/register-user", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({
                fullName,
                email,
                password,
                role: roleEl.value
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                document.querySelector(".register-box").style.display = "none";
                document.getElementById("successBox").style.display = "block";
            } else {
                showError(fields.email, errors.email, data.message);
            }
        })
        .catch(() => {
            showError(fields.email, errors.email, "Server error. Please try again.");
        })
        .finally(() => {
            regBtn.disabled = false;
            regBtn.textContent = "Register";
            spinner.style.display = "none";
        });
    });
});
