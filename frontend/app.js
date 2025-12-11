console.log("Frontend loaded");

const API_BASE = "/api";

const catalogBtn = document.getElementById("catalogBtn");
const cartBtn = document.getElementById("cartBtn");
const dashboardBtn = document.getElementById("dashboardBtn");

const catalogSection = document.getElementById("catalogSection");
const cartSection = document.getElementById("cartSection");
const dashboardSection = document.getElementById("dashboardSection");

const catalogGrid = document.getElementById("catalogGrid");
const cartItemsDiv = document.getElementById("cartItems");
const cartCount = document.getElementById("cartCount");

const checkoutBtn = document.getElementById("checkoutBtn");
const checkoutForm = document.getElementById("checkoutForm");

const redisStatus = document.getElementById("redisStatus");
const rabbitStatus = document.getElementById("rabbitStatus");
const ordersStatus = document.getElementById("ordersStatus");

const redisLed = document.getElementById("redisLed");
const rabbitLed = document.getElementById("rabbitLed");
const postgresLed = document.getElementById("postgresLed");

const successModal = document.getElementById("successModal");
const successMessage = document.getElementById("successMessage");

let carsCache = [];
let session_id = null;

/* Helper: LED */
function setLed(ledEl, isUp) {
    if (!ledEl) return;
    ledEl.classList.remove("ok", "down");
    if (isUp === true) ledEl.classList.add("ok");
    else if (isUp === false) ledEl.classList.add("down");
}

/* -------------------------
   SECTION SWITCHING
------------------------- */
catalogBtn.onclick = () => showSection("catalog");
cartBtn.onclick = async () => {
    showSection("cart");
    renderCart(await loadSessionCart());
};
dashboardBtn.onclick = () => {
    showSection("dashboard");
    loadDashboard();
};

function showSection(name) {
    /* NEW: Save last page */
    localStorage.setItem("activeSection", name);

    catalogSection.classList.remove("active");
    cartSection.classList.remove("active");
    dashboardSection.classList.remove("active");

    if (name === "catalog") catalogSection.classList.add("active");
    if (name === "cart") cartSection.classList.add("active");
    if (name === "dashboard") dashboardSection.classList.add("active");
}

/* -------------------------
   RESTORE LAST SECTION ON REFRESH
------------------------- */
const savedSection = localStorage.getItem("activeSection");
if (savedSection === "cart") {
    showSection("cart");
    loadSessionCart().then(items => renderCart(items));
}
else if (savedSection === "dashboard") {
    showSection("dashboard");
    loadDashboard();
}
else {
    showSection("catalog");
}

/* -------------------------
   LOAD CATALOG
------------------------- */
async function loadCatalog() {
    try {
        const response = await fetch(`${API_BASE}/cars`);
        if (!response.ok) throw new Error("Failed to load cars");
        const cars = await response.json();
        carsCache = cars;
        renderCatalog(cars);
    } catch (e) {
        console.error(e);
        catalogGrid.innerHTML = "<p>Error loading cars.</p>";
    }
}

function renderCatalog(cars) {
    catalogGrid.innerHTML = "";
    cars.forEach(car => {
        const card = document.createElement("div");
        card.className = "car-card";

        const imageUrl =
            `https://cdn.imagin.studio/getImage?customer=img&make=${encodeURIComponent(car.make)}&model=${encodeURIComponent(car.model)}&angle=front`;

        card.innerHTML = `
            <img src="${imageUrl}">
            <h3>${car.make} ${car.model}</h3>
            <p>${car.year}</p>
            <p>${car.description || ""}</p>
            <p><strong>$${Number(car.price).toLocaleString()}</strong></p>
            <button class="add-btn">Add</button>
        `;

        card.querySelector(".add-btn").onclick = () => addToCartBackend(car.id);
        catalogGrid.appendChild(card);
    });
}

/* -------------------------
   CART LOGIC
------------------------- */
async function loadSessionCart() {
    const res = await fetch(`${API_BASE}/cart`, { credentials: "include" });
    const data = await res.json();
    session_id = data.session_id;
    return data.items || [];
}

async function addToCartBackend(carId) {
    await fetch(`${API_BASE}/cart`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ car_id: carId, quantity: 1 })
    });
    updateCartCountUI();
}

async function updateCartCountUI() {
    const res = await fetch(`${API_BASE}/cart`, { credentials: "include" });
    const data = await res.json();
    let count = 0;
    (data.items || []).forEach(it => count += it.quantity);
    cartCount.textContent = count;
}

function renderCart(items) {
    cartItemsDiv.innerHTML = "";
    if (!items.length) {
        cartItemsDiv.innerHTML = "<p>Your cart is empty.</p>";
        checkoutForm.style.display = "none";
        return;
    }

    items.forEach(it => {
        const car = carsCache.find(c => c.id === it.car_id);
        const row = document.createElement("div");
        row.className = "cart-item";
        row.innerHTML = `
            <p><strong>${car.make} ${car.model}</strong></p>
            <p>Quantity: ${it.quantity}</p>
            <p>Price: $${car.price}</p>
        `;
        cartItemsDiv.appendChild(row);
    });

    checkoutForm.style.display = "block";
}

/* -------------------------
   CHECKOUT
------------------------- */
checkoutBtn.onclick = checkout;

async function checkout() {
    const name = document.getElementById("custName").value.trim();
    const email = document.getElementById("custEmail").value.trim();

    const res = await fetch(`${API_BASE}/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ session_id, customer_name: name, customer_email: email })
    });

    const data = await res.json();

    if (!res.ok) return alert("Checkout failed: " + JSON.stringify(data));

    successMessage.textContent = `Order #${data.order_id} created!`;
    successModal.style.display = "block";

    await fetch(`${API_BASE}/cart`, { method: "DELETE", credentials: "include" });
    updateCartCountUI();
}

/* -------------------------
   SERVICE DASHBOARD
------------------------- */
async function loadDashboard() {
    redisStatus.textContent = "Loading...";
    rabbitStatus.textContent = "Loading...";
    ordersStatus.textContent = "Loading...";

    /* Redis LED */
    fetch(`${API_BASE}/status/redis`).then(r => r.json()).then(d => {
        redisStatus.textContent = JSON.stringify(d, null, 2);
        setLed(redisLed, d && d.redis === "OK");
    }).catch(() => {
        redisStatus.textContent = "Error contacting Redis";
        setLed(redisLed, false);
    });

    /* RabbitMQ LED */
    fetch(`${API_BASE}/status/rabbit`).then(r => r.json()).then(d => {
        rabbitStatus.textContent = JSON.stringify(d, null, 2);
        setLed(rabbitLed, d && d.rabbitmq === "OK");
    }).catch(() => {
        rabbitStatus.textContent = "Error contacting RabbitMQ";
        setLed(rabbitLed, false);
    });

    /* Postgres LED */
    fetch(`${API_BASE}/status/orders`).then(r => r.json()).then(d => {
        ordersStatus.textContent = JSON.stringify(d, null, 2);
        setLed(postgresLed, true);
    }).catch(() => {
        ordersStatus.textContent = "Error loading orders";
        setLed(postgresLed, false);
    });
}

/* ---- SERVICE CONTROL BUTTONS ---- */
document.querySelectorAll(".service-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const service = btn.dataset.service;
        const action = btn.dataset.action;
        const targetId = btn.dataset.target;
        handleServiceAction(service, action, targetId);
    });
});

async function handleServiceAction(service, action, targetId) {
    const target = document.getElementById(targetId);

    const ledMap = {
        redis: redisLed,
        rabbit: rabbitLed,
        postgres: postgresLed
    };
    const ledEl = ledMap[service];

    target.textContent = `[${new Date().toISOString()}] Running ${action.toUpperCase()} on ${service}...`;

    try {
        const res = await fetch(`${API_BASE}/service/${service}/${action}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: "{}"
        });

        const data = await res.json();

        if (!res.ok) {
            target.textContent = `[${new Date().toISOString()}] ERROR:\n` +
                (data.log || JSON.stringify(data, null, 2));
            if (ledEl) setLed(ledEl, false);
            return;
        }

        target.textContent = data.log || JSON.stringify(data, null, 2);

        if (action === "stop") setLed(ledEl, false);
        if (action === "start") setLed(ledEl, true);
        if (action === "status") setLed(ledEl, true);

    } catch (e) {
        target.textContent = `[${new Date().toISOString()}] Network error: ${e}`;
        if (ledEl) setLed(ledEl, false);
    }
}

/* -------------------------
   MODAL
------------------------- */
function closeModal() {
    successModal.style.display = "none";
}
window.closeModal = closeModal;

/* -------------------------
   INITIAL LOAD
------------------------- */
loadCatalog();
updateCartCountUI();
