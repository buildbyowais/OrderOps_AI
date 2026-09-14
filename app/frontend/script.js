const API_BASE = "http://127.0.0.1:8000";

let allOrders = [];
let allCustomers = [];
let allProducts = [];

let selectedOrder = null;


/* =========================
   INITIALIZATION
========================= */

document.addEventListener("DOMContentLoaded", () => {

    setupNavigation();

    setupFilters();

    loadDashboard();

});


/* =========================
   NAVIGATION
========================= */

const pageInformation = {

    dashboard: {
        title: "Dashboard",
        subtitle: "Monitor your AI-powered order operations"
    },

    orders: {
        title: "Orders",
        subtitle: "Manage and monitor all customer orders"
    },

    customers: {
        title: "Customers",
        subtitle: "View customer information"
    },

    products: {
        title: "Products",
        subtitle: "Monitor products and available inventory"
    },

    reviews: {
        title: "Manual Reviews",
        subtitle: "Orders flagged by the AI risk system"
    },

    refunds: {
        title: "Refunds",
        subtitle: "Process and monitor customer refunds"
    }

};


function setupNavigation() {

    document.querySelectorAll(".nav-item").forEach(item => {

        item.addEventListener("click", event => {

            event.preventDefault();

            const page = item.dataset.page;

            navigateTo(page);

        });

    });

}


function navigateTo(page) {

    document.querySelectorAll(".page-section").forEach(section => {

        section.classList.add("d-none");

    });


    const target = document.getElementById(
        `${page}-page`
    );

    if (target) {
        target.classList.remove("d-none");
    }


    document.querySelectorAll(".nav-item").forEach(item => {

        item.classList.remove("active");

    });


    const activeItem = document.querySelector(
        `.nav-item[data-page="${page}"]`
    );

    if (activeItem) {
        activeItem.classList.add("active");
    }


    if (pageInformation[page]) {

        document.getElementById(
            "page-title"
        ).textContent = pageInformation[page].title;


        document.getElementById(
            "page-subtitle"
        ).textContent = pageInformation[page].subtitle;

    }


    if (page === "dashboard") {
        loadDashboard();
    }

    if (page === "orders") {
        loadOrders();
    }

    if (page === "customers") {
        loadCustomers();
    }

    if (page === "products") {
        loadProducts();
    }

    if (page === "reviews") {
        loadReviews();
    }

    if (page === "refunds") {
        loadRefunds();
    }

}


/* =========================
   API HELPER
========================= */

async function apiRequest(
    endpoint,
    options = {}
) {

    const response = await fetch(
        `${API_BASE}${endpoint}`,
        {
            ...options,

            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {})
            }
        }
    );


    const contentType =
        response.headers.get("content-type") || "";


    let data = null;


    if (contentType.includes("application/json")) {
        data = await response.json();
    } else {
        data = await response.text();
    }


    if (!response.ok) {

        let message = "Request failed.";

        if (typeof data === "object" && data?.detail) {
            message = data.detail;
        }

        else if (typeof data === "string" && data) {
            message = data;
        }

        throw new Error(message);
    }


    return data;
}


/* =========================
   DASHBOARD
========================= */

async function loadDashboard() {

    try {

        const orders = await apiRequest("/orders");

        allOrders = orders;

        updateDashboardStats(orders);

        displayRecentOrders(orders);

    }

    catch (error) {

        console.error(error);

        showToast(
            error.message,
            "danger"
        );

        document.getElementById(
            "recent-orders-table"
        ).innerHTML = emptyTable(
            6,
            "Unable to load orders."
        );

    }

}


function updateDashboardStats(orders) {

    const total = orders.length;


    const pending = orders.filter(order => {

        return [
            "pending",
            "processing",
            "workflow_started",
            "offer_created"
        ].includes(order.status);

    }).length;


    const completed = orders.filter(order => {

        return [
            "ready_for_fulfillment",
            "alternative_accepted"
        ].includes(order.status);

    }).length;


    const reviews = orders.filter(order => {

        return order.status === "manual_review";

    }).length;


    document.getElementById(
        "dashboard-total"
    ).textContent = total;


    document.getElementById(
        "dashboard-pending"
    ).textContent = pending;


    document.getElementById(
        "dashboard-completed"
    ).textContent = completed;


    document.getElementById(
        "dashboard-reviews"
    ).textContent = reviews;

}


function displayRecentOrders(orders) {

    const table = document.getElementById(
        "recent-orders-table"
    );


    if (!orders.length) {

        table.innerHTML = emptyTable(
            6,
            "No orders found."
        );

        return;
    }


    const recent = [...orders]
        .reverse()
        .slice(0, 5);


    table.innerHTML = recent.map(order => {

        return `

            <tr>

                <td>
                    <span class="order-id">
                        #${order.id}
                    </span>
                </td>

                <td>
                    <span class="customer-name">
                        Customer #${order.customer_id}
                    </span>
                </td>

                <td>
                    <span class="product-name">
                        Product #${order.product_id}
                    </span>
                </td>

                <td>
                    ${order.quantity}
                </td>

                <td>
                    ${statusBadge(order.status)}
                </td>

                <td>

                    <button
                        class="btn-secondary-custom"
                        onclick="viewOrder(${order.id})"
                    >
                        View
                    </button>

                </td>

            </tr>

        `;

    }).join("");

}


/* =========================
   ORDERS
========================= */

async function loadOrders() {

    const table = document.getElementById(
        "orders-table"
    );


    table.innerHTML = loadingTable(
        6
    );


    try {

        const orders = await apiRequest(
            "/orders"
        );

        allOrders = orders;

        displayOrders(orders);

    }

    catch (error) {

        console.error(error);

        table.innerHTML = emptyTable(
            6,
            "Unable to load orders."
        );

        showToast(
            error.message,
            "danger"
        );

    }

}


function displayOrders(orders) {

    const table = document.getElementById(
        "orders-table"
    );


    if (!orders.length) {

        table.innerHTML = emptyTable(
            6,
            "No orders found."
        );

        return;
    }


    table.innerHTML = orders.map(order => {

        return `

            <tr>

                <td>
                    <span class="order-id">
                        #${order.id}
                    </span>
                </td>

                <td>
                    <span class="customer-name">
                        Customer #${order.customer_id}
                    </span>
                </td>

                <td>
                    <span class="product-name">
                        Product #${order.product_id}
                    </span>
                </td>

                <td>
                    ${order.quantity}
                </td>

                <td>
                    ${statusBadge(order.status)}
                </td>

                <td>

                    <button
                        class="btn-secondary-custom"
                        onclick="viewOrder(${order.id})"
                    >
                        <i class="bi bi-eye"></i>
                        View
                    </button>

                </td>

            </tr>

        `;

    }).join("");

}


/* =========================
   ORDER FILTER
========================= */

function setupFilters() {

    const searchInput =
        document.getElementById(
            "order-search"
        );


    const statusFilter =
        document.getElementById(
            "status-filter"
        );


    searchInput.addEventListener(
        "input",
        filterOrders
    );


    statusFilter.addEventListener(
        "change",
        filterOrders
    );

}


function filterOrders() {

    const search =
        document.getElementById(
            "order-search"
        ).value
        .trim()
        .toLowerCase();


    const status =
        document.getElementById(
            "status-filter"
        ).value;


    let filtered = [...allOrders];


    if (search) {

        filtered = filtered.filter(
            order =>
                String(order.id)
                    .toLowerCase()
                    .includes(search)
        );

    }


    if (status !== "all") {

        filtered = filtered.filter(
            order =>
                order.status === status
        );

    }


    displayOrders(filtered);

}


/* =========================
   CUSTOMERS
========================= */

async function loadCustomers() {

    const table =
        document.getElementById(
            "customers-table"
        );


    table.innerHTML =
        loadingTable(4);


    try {

        const customers =
            await apiRequest(
                "/customers"
            );


        allCustomers = customers;


        if (!customers.length) {

            table.innerHTML =
                emptyTable(
                    4,
                    "No customers found."
                );

            return;
        }


        table.innerHTML =
            customers.map(customer => {

                return `

                    <tr>

                        <td>
                            <span class="order-id">
                                #${customer.id}
                            </span>
                        </td>

                        <td>
                            <span class="customer-name">
                                ${escapeHtml(
                                    customer.name || "N/A"
                                )}
                            </span>
                        </td>

                        <td>
                            ${escapeHtml(
                                customer.email || "N/A"
                            )}
                        </td>

                        <td>
                            ${escapeHtml(
                                customer.phone || "N/A"
                            )}
                        </td>

                    </tr>

                `;

            }).join("");

    }

    catch (error) {

        console.error(error);

        table.innerHTML =
            emptyTable(
                4,
                "Unable to load customers."
            );

        showToast(
            error.message,
            "danger"
        );

    }

}


/* =========================
   PRODUCTS
========================= */

async function loadProducts() {

    const table =
        document.getElementById(
            "products-table"
        );


    table.innerHTML =
        loadingTable(5);


    try {

        const products =
            await apiRequest(
                "/products"
            );


        allProducts = products;


        if (!products.length) {

            table.innerHTML =
                emptyTable(
                    5,
                    "No products found."
                );

            return;
        }


        table.innerHTML =
            products.map(product => {

                const stock =
                    Number(product.stock || 0);


                const available =
                    stock > 0;


                return `

                    <tr>

                        <td>
                            <span class="order-id">
                                #${product.id}
                            </span>
                        </td>

                        <td>
                            <span class="customer-name">
                                ${escapeHtml(
                                    product.name || "N/A"
                                )}
                            </span>
                        </td>

                        <td>
                            PKR ${formatNumber(
                                product.price
                            )}
                        </td>

                        <td>
                            ${stock}
                        </td>

                        <td>

                            ${
                                available
                                ?
                                `<span class="status-badge status-success">
                                    In Stock
                                </span>`
                                :
                                `<span class="status-badge status-refunded">
                                    Out of Stock
                                </span>`
                            }

                        </td>

                    </tr>

                `;

            }).join("");

    }

    catch (error) {

        console.error(error);

        table.innerHTML =
            emptyTable(
                5,
                "Unable to load products."
            );

        showToast(
            error.message,
            "danger"
        );

    }

}


/* =========================
   ORDER DETAILS
========================= */

async function viewOrder(orderId) {

    const modalElement =
        document.getElementById(
            "orderModal"
        );


    const modal =
        bootstrap.Modal.getOrCreateInstance(
            modalElement
        );


    document.getElementById(
        "modal-order-number"
    ).textContent =
        `Order #${orderId}`;


    document.getElementById(
        "order-details-content"
    ).innerHTML =
        `
            <div class="text-center py-5">

                <div class="spinner-border text-primary"></div>

                <p class="mt-3 text-muted">
                    Loading order information...
                </p>

            </div>
        `;


    modal.show();


    try {

        const orders =
            await apiRequest(
                "/orders"
            );


        const order =
            orders.find(
                item =>
                    item.id === orderId
            );


        if (!order) {
            throw new Error(
                "Order not found."
            );
        }


        selectedOrder = order;


        await renderOrderDetails(
            order
        );

    }

    catch (error) {

        console.error(error);

        document.getElementById(
            "order-details-content"
        ).innerHTML =
            `
                <div class="alert alert-danger">
                    ${escapeHtml(
                        error.message
                    )}
                </div>
            `;

    }

}


/* =========================
   ORDER DETAIL UI
========================= */

async function renderOrderDetails(
    order
) {

    const container =
        document.getElementById(
            "order-details-content"
        );


    container.innerHTML = `

        <div class="workflow-progress">

            ${workflowStep(
                "Order",
                "bi-box",
                true,
                true
            )}

            ${workflowStep(
                "Risk",
                "bi-shield-check",
                false,
                false
            )}

            ${workflowStep(
                "Stock",
                "bi-boxes",
                false,
                false
            )}

            ${workflowStep(
                "Alternative",
                "bi-search",
                false,
                false
            )}

            ${workflowStep(
                "AI Offer",
                "bi-stars",
                false,
                false
            )}

            ${workflowStep(
                "Response",
                "bi-envelope",
                false,
                false
            )}

            ${workflowStep(
                "Fulfillment",
                "bi-check2-circle",
                false,
                false
            )}

        </div>


        <div class="row g-3 mb-4">

            <div class="col-md-3">

                <div class="detail-box">

                    <label>
                        Order ID
                    </label>

                    <strong>
                        #${order.id}
                    </strong>

                </div>

            </div>


            <div class="col-md-3">

                <div class="detail-box">

                    <label>
                        Customer
                    </label>

                    <strong>
                        Customer #${order.customer_id}
                    </strong>

                </div>

            </div>


            <div class="col-md-3">

                <div class="detail-box">

                    <label>
                        Product
                    </label>

                    <strong>
                        Product #${order.product_id}
                    </strong>

                </div>

            </div>


            <div class="col-md-3">

                <div class="detail-box">

                    <label>
                        Quantity
                    </label>

                    <strong>
                        ${order.quantity}
                    </strong>

                </div>

            </div>

        </div>


        <div class="detail-box mb-4">

            <label>
                Current Status
            </label>

            <div>
                ${statusBadge(order.status)}
            </div>

        </div>


        <div id="analysis-results">

            <div class="row g-3">

                <div class="col-md-4">

                    <div class="action-panel">

                        <h6>
                            <i class="bi bi-shield-check me-1"></i>
                            Risk Analysis
                        </h6>

                        <p>
                            Run customer risk assessment.
                        </p>

                        <button
                            class="btn-secondary-custom"
                            onclick="runRiskCheck(${order.id})"
                        >
                            Check Risk
                        </button>

                        <div
                            id="risk-result"
                            class="mt-3"
                        ></div>

                    </div>

                </div>


                <div class="col-md-4">

                    <div class="action-panel">

                        <h6>
                            <i class="bi bi-boxes me-1"></i>
                            Stock Check
                        </h6>

                        <p>
                            Check current product availability.
                        </p>

                        <button
                            class="btn-secondary-custom"
                            onclick="runStockCheck(${order.id})"
                        >
                            Check Stock
                        </button>

                        <div
                            id="stock-result"
                            class="mt-3"
                        ></div>

                    </div>

                </div>


                <div class="col-md-4">

                    <div class="action-panel">

                        <h6>
                            <i class="bi bi-search me-1"></i>
                            Alternatives
                        </h6>

                        <p>
                            Find available alternatives.
                        </p>

                        <button
                            class="btn-secondary-custom"
                            onclick="loadAlternatives(${order.id})"
                        >
                            Find Alternatives
                        </button>

                        <div
                            id="alternative-result"
                            class="mt-3"
                        ></div>

                    </div>

                </div>

            </div>

        </div>


        <div class="action-panel mt-4">

            <h6>
                <i class="bi bi-stars me-1"></i>
                AI Order Workflow
            </h6>

            <p>
                Start the complete LangGraph order workflow.
            </p>

            <div class="action-buttons">

                <button
                    class="btn-primary-custom"
                    onclick="processOrder(${order.id})"
                >
                    <i class="bi bi-play-fill"></i>
                    Process Order
                </button>


                <button
                    class="btn-secondary-custom"
                    onclick="checkCustomerEmail(${order.id})"
                >
                    <i class="bi bi-envelope-check"></i>
                    Check Customer Email
                </button>


                <button
                    class="btn-secondary-custom"
                    onclick="fulfillDirect(${order.id})"
                >
                    <i class="bi bi-truck"></i>
                    Direct Fulfill
                </button>


                <button
                    class="btn-danger-custom"
                    onclick="processRefund(${order.id})"
                >
                    <i class="bi bi-arrow-counterclockwise"></i>
                    Refund
                </button>

            </div>

            <div
                id="workflow-result"
                class="mt-3"
            ></div>

        </div>

    `;

}


/* =========================
   RISK CHECK
========================= */

async function runRiskCheck(
    orderId
) {

    const container =
        document.getElementById(
            "risk-result"
        );


    container.innerHTML =
        loadingSmall();


    try {

        const result =
            await apiRequest(
                `/orders/${orderId}/risk-check`
            );


        container.innerHTML = `

            <div class="alert alert-light border mb-0">

                <strong>
                    Risk Score:
                </strong>

                ${result.risk_score ?? "N/A"}

                <br>

                <strong>
                    Decision:
                </strong>

                ${escapeHtml(
                    result.decision ||
                    result.risk_decision ||
                    "N/A"
                )}

            </div>

        `;

    }

    catch (error) {

        container.innerHTML =
            errorBox(
                error.message
            );

    }

}


/* =========================
   STOCK CHECK
========================= */

async function runStockCheck(
    orderId
) {

    const container =
        document.getElementById(
            "stock-result"
        );


    container.innerHTML =
        loadingSmall();


    try {

        const result =
            await apiRequest(
                `/orders/${orderId}/stock-check`
            );


        const available =
            result.available ??
            result.stock_available ??
            false;


        container.innerHTML = `

            <div class="alert ${
                available
                ? "alert-success"
                : "alert-danger"
            } mb-0">

                <strong>
                    ${available
                    ? "Available"
                    : "Out of Stock"}
                </strong>

                <br>

                ${escapeHtml(
                    JSON.stringify(
                        result
                    )
                )}

            </div>

        `;

    }

    catch (error) {

        container.innerHTML =
            errorBox(
                error.message
            );

    }

}


/* =========================
   ALTERNATIVES
========================= */

async function loadAlternatives(
    orderId
) {

    const container =
        document.getElementById(
            "alternative-result"
        );


    container.innerHTML =
        loadingSmall();


    try {

        const result =
            await apiRequest(
                `/orders/${orderId}/alternatives`
            );


        if (!Array.isArray(result) || !result.length) {

            container.innerHTML = `

                <div class="alert alert-warning mb-0">

                    No alternatives found.

                </div>

            `;

            return;
        }


        container.innerHTML = `

            <div class="alert alert-light border mb-0">

                <strong>
                    ${result.length}
                    alternative(s) found
                </strong>

                <div class="mt-2">

                    ${result.map(item => {

                        return `
                            <div class="mb-1">
                                • ${escapeHtml(
                                    item.name ||
                                    item.product_name ||
                                    "Alternative Product"
                                )}
                            </div>
                        `;

                    }).join("")}

                </div>

            </div>

        `;

    }

    catch (error) {

        container.innerHTML =
            errorBox(
                error.message
            );

    }

}


/* =========================
   AI OFFER
========================= */

async function loadOffer(
    orderId
) {

    try {

        const result =
            await apiRequest(
                `/orders/${orderId}/offer`
            );


        return result;

    }

    catch (error) {

        showToast(
            error.message,
            "danger"
        );

        return null;

    }

}


/* =========================
   PROCESS ORDER
========================= */

async function processOrder(
    orderId
) {

    const container =
        document.getElementById(
            "workflow-result"
        );


    container.innerHTML =
        loadingSmall();


    try {

        const result =
            await apiRequest(
                `/orders/${orderId}/process`,
                {
                    method: "POST"
                }
            );


        container.innerHTML =
            workflowResult(
                result,
                "Workflow started successfully."
            );


        showToast(
            "Order workflow started.",
            "success"
        );


        await refreshAfterAction(
            orderId
        );

    }

    catch (error) {

        container.innerHTML =
            errorBox(
                error.message
            );


        showToast(
            error.message,
            "danger"
        );

    }

}


/* =========================
   CUSTOMER EMAIL
========================= */

async function checkCustomerEmail(
    orderId
) {

    const container =
        document.getElementById(
            "workflow-result"
        );


    container.innerHTML =
        loadingSmall();


    try {

        const result =
            await apiRequest(
                `/orders/${orderId}/check-email`,
                {
                    method: "POST"
                }
            );


        let responseText =
            "Email checked successfully.";


        if (result.decision) {

            responseText =
                `Customer response: ${result.decision}`;

        }


        container.innerHTML =
            workflowResult(
                result,
                responseText
            );


        showToast(
            responseText,
            "success"
        );


        await refreshAfterAction(
            orderId
        );

    }

    catch (error) {

        container.innerHTML =
            errorBox(
                error.message
            );


        showToast(
            error.message,
            "danger"
        );

    }

}


/* =========================
   RESPONSE
========================= */

async function submitCustomerResponse(
    orderId,
    response
) {

    try {

        const result =
            await apiRequest(
                `/orders/${orderId}/response`,
                {
                    method: "POST",

                    body: JSON.stringify({
                        response: response
                    })
                }
            );


        showToast(
            `Customer response ${response}.`,
            "success"
        );


        document.getElementById(
            "workflow-result"
        ).innerHTML =
            workflowResult(
                result,
                `Response ${response}.`
            );


        await refreshAfterAction(
            orderId
        );

    }

    catch (error) {

        showToast(
            error.message,
            "danger"
        );

    }

}


/* =========================
   REFUND
========================= */

async function processRefund(
    orderId
) {

    const confirmed =
        confirm(
            `Process refund for Order #${orderId}?`
        );


    if (!confirmed) {
        return;
    }


    try {

        const result =
            await apiRequest(
                `/orders/${orderId}/refund`,
                {
                    method: "POST"
                }
            );


        showToast(
            "Refund processed successfully.",
            "success"
        );


        document.getElementById(
            "workflow-result"
        ).innerHTML =
            workflowResult(
                result,
                "Refund processed successfully."
            );


        await refreshAfterAction(
            orderId
        );

    }

    catch (error) {

        showToast(
            error.message,
            "danger"
        );

    }

}


/* =========================
   FULFILL
========================= */

async function fulfillOrder(
    orderId
) {

    try {

        const result =
            await apiRequest(
                `/orders/${orderId}/fulfill`,
                {
                    method: "POST"
                }
            );


        showToast(
            "Order sent to fulfillment.",
            "success"
        );


        document.getElementById(
            "workflow-result"
        ).innerHTML =
            workflowResult(
                result,
                "Order ready for fulfillment."
            );


        await refreshAfterAction(
            orderId
        );

    }

    catch (error) {

        showToast(
            error.message,
            "danger"
        );

    }

}


/* =========================
   DIRECT FULFILL
========================= */

async function fulfillDirect(
    orderId
) {

    try {

        const result =
            await apiRequest(
                `/orders/${orderId}/fulfill-direct`,
                {
                    method: "POST"
                }
            );


        showToast(
            "Order directly fulfilled.",
            "success"
        );


        document.getElementById(
            "workflow-result"
        ).innerHTML =
            workflowResult(
                result,
                "Order ready for fulfillment."
            );


        await refreshAfterAction(
            orderId
        );

    }

    catch (error) {

        showToast(
            error.message,
            "danger"
        );

    }

}


/* =========================
   REFUNDS PAGE
========================= */

async function loadRefunds() {

    const table =
        document.getElementById(
            "refunds-table"
        );


    table.innerHTML =
        loadingTable(6);


    try {

        const orders =
            await apiRequest(
                "/orders"
            );


        const refunded =
            orders.filter(
                order =>
                    order.status === "refunded"
            );


        if (!refunded.length) {

            table.innerHTML =
                emptyTable(
                    6,
                    "No refunded orders found."
                );

            return;
        }


        const products =
            await apiRequest(
                "/products"
            );


        const customers =
            await apiRequest(
                "/customers"
            );


        table.innerHTML =
            refunded.map(order => {

                const product =
                    products.find(
                        item =>
                            item.id ===
                            order.product_id
                    );


                const customer =
                    customers.find(
                        item =>
                            item.id ===
                            order.customer_id
                    );


                const amount =
                    product
                    ? Number(product.price) *
                      Number(order.quantity)
                    : 0;


                return `

                    <tr>

                        <td>
                            <span class="order-id">
                                #${order.id}
                            </span>
                        </td>

                        <td>
                            ${escapeHtml(
                                customer?.name ||
                                `Customer #${order.customer_id}`
                            )}
                        </td>

                        <td>
                            ${escapeHtml(
                                product?.name ||
                                `Product #${order.product_id}`
                            )}
                        </td>

                        <td>
                            PKR ${formatNumber(
                                amount
                            )}
                        </td>

                        <td>
                            ${statusBadge(
                                "refunded"
                            )}
                        </td>

                        <td>
                            <button
                                class="btn-secondary-custom"
                                onclick="viewOrder(${order.id})"
                            >
                                View
                            </button>
                        </td>

                    </tr>

                `;

            }).join("");

    }

    catch (error) {

        console.error(error);

        table.innerHTML =
            emptyTable(
                6,
                "Unable to load refunds."
            );

    }

}


/* =========================
   MANUAL REVIEWS
========================= */

async function loadReviews() {

    const table =
        document.getElementById(
            "reviews-table"
        );


    table.innerHTML =
        loadingTable(4);


    try {

        const orders =
            await apiRequest(
                "/orders"
            );


        const reviews =
            orders.filter(
                order =>
                    order.status ===
                    "manual_review"
            );


        if (!reviews.length) {

            table.innerHTML =
                emptyTable(
                    4,
                    "No manual reviews required."
                );

            return;
        }


        table.innerHTML =
            reviews.map(order => {

                return `

                    <tr>

                        <td>
                            <span class="order-id">
                                #${order.id}
                            </span>
                        </td>

                        <td>
                            Customer #${order.customer_id}
                        </td>

                        <td>
                            ${statusBadge(
                                "manual_review"
                            )}
                        </td>

                        <td>

                            <button
                                class="btn-secondary-custom"
                                onclick="viewOrder(${order.id})"
                            >
                                Review
                            </button>

                        </td>

                    </tr>

                `;

            }).join("");

    }

    catch (error) {

        table.innerHTML =
            emptyTable(
                4,
                "Unable to load reviews."
            );

    }

}


/* =========================
   REFRESH AFTER ACTION
========================= */

async function refreshAfterAction(
    orderId
) {

    await loadDashboard();

    const orders =
        await apiRequest(
            "/orders"
        );


    allOrders = orders;


    const updated =
        orders.find(
            order =>
                order.id === orderId
        );


    if (updated) {

        selectedOrder =
            updated;

        await renderOrderDetails(
            updated
        );

    }

}


/* =========================
   STATUS BADGE
========================= */

function statusBadge(status) {

    if (!status) {

        return `
            <span class="status-badge status-processing">
                Unknown
            </span>
        `;

    }


    let className =
        "status-processing";


    if (
        [
            "ready_for_fulfillment",
            "alternative_accepted"
        ].includes(status)
    ) {

        className =
            "status-success";

    }


    else if (
        status === "refunded"
    ) {

        className =
            "status-refunded";

    }


    else if (
        status === "manual_review"
    ) {

        className =
            "status-review";

    }


    else if (
        [
            "pending",
            "no_alternative_found"
        ].includes(status)
    ) {

        className =
            "status-pending";

    }


    const formatted =
        status
            .replaceAll("_", " ")
            .replace(
                /\b\w/g,
                char =>
                    char.toUpperCase()
            );


    return `
        <span class="status-badge ${className}">
            ${formatted}
        </span>
    `;

}


/* =========================
   WORKFLOW STEP
========================= */

function workflowStep(
    title,
    icon,
    active = false,
    completed = false
) {

    let className = "";


    if (active) {
        className += " active";
    }


    if (completed) {
        className += " completed";
    }


    return `

        <div class="progress-item ${className}">

            <div class="progress-circle">

                <i class="bi ${icon}"></i>

            </div>

            <small>
                ${title}
            </small>

        </div>

    `;

}


/* =========================
   UI HELPERS
========================= */

function loadingTable(
    columns
) {

    return `

        <tr>

            <td colspan="${columns}">

                <div class="text-center py-5">

                    <div class="spinner-border text-primary"></div>

                    <p class="text-muted mt-2 mb-0">
                        Loading...
                    </p>

                </div>

            </td>

        </tr>

    `;

}


function emptyTable(
    columns,
    message
) {

    return `

        <tr>

            <td colspan="${columns}">

                <div class="text-center py-5 text-muted">

                    <i class="bi bi-inbox fs-3"></i>

                    <p class="mt-2 mb-0">
                        ${escapeHtml(message)}
                    </p>

                </div>

            </td>

        </tr>

    `;

}


function loadingSmall() {

    return `

        <div class="text-center py-2">

            <div
                class="spinner-border spinner-border-sm text-primary"
            ></div>

        </div>

    `;

}


function errorBox(
    message
) {

    return `

        <div class="alert alert-danger mb-0">

            ${escapeHtml(message)}

        </div>

    `;

}


function workflowResult(
    result,
    message
) {

    return `

        <div class="alert alert-light border">

            <strong>
                ${escapeHtml(message)}
            </strong>

            ${
                result?.final_status
                ?
                `
                    <br>
                    Status:
                    <strong>
                        ${escapeHtml(
                            result.final_status
                        )}
                    </strong>
                `
                :
                ""
            }

        </div>

    `;

}


function formatNumber(
    value
) {

    const number =
        Number(value || 0);


    return number.toLocaleString(
        "en-PK"
    );

}


function escapeHtml(
    value
) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


/* =========================
   TOAST
========================= */

function showToast(
    message,
    type = "success"
) {

    const container =
        document.getElementById(
            "toast-container"
        );


    const id =
        `toast-${Date.now()}`;


    const icon =
        type === "success"
        ? "bi-check-circle"
        : "bi-exclamation-circle";


    container.insertAdjacentHTML(
        "beforeend",
        `
            <div
                id="${id}"
                class="toast-custom mb-2"
            >

                <div
                    class="d-flex align-items-center gap-2"
                >

                    <i
                        class="bi ${icon} text-${
                            type === "success"
                            ? "success"
                            : "danger"
                        }"
                    ></i>

                    <span>
                        ${escapeHtml(message)}
                    </span>

                </div>

            </div>
        `
    );


    setTimeout(() => {

        const toast =
            document.getElementById(id);

        if (toast) {
            toast.remove();
        }

    }, 3500);

}