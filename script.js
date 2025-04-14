// --- START OF FILE script.js ---

import { getMenuItems, createOrder } from './api.js';

// Initialize currentOrder from localStorage or empty array
let currentOrder = JSON.parse(localStorage.getItem('currentOrder') || '[]');

// --- Helper Function for Escaping HTML ---
function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') return unsafe;
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// --- DOM Element References ---
const menuContainer = document.getElementById('menu');
const orderList = document.getElementById('orderList');
const totalAmountSpan = document.getElementById('totalAmount');
const placeOrderButton = document.getElementById('placeOrderBtn');

// --- Core Application Logic ---
async function fetchMenu(category) {
    if (!menuContainer) {
        console.error("ERROR: Menu container element ('menu') not found in the DOM.");
        return;
    }

    menuContainer.innerHTML = '<p class="text-gray-500 col-span-full text-center py-10">🍳 Loading delicious items...</p>';

    try {
        const items = await getMenuItems(category);
        if (items && items.length > 0) {
            renderMenu(items);
        } else {
            menuContainer.innerHTML = `<p class="text-gray-500 col-span-full text-center py-10">🤔 No items found for the '${escapeHtml(category)}' category.</p>`;
        }
    } catch (error) {
        console.error(`ERROR fetching menu for category '${category}':`, error);
        menuContainer.innerHTML = `
          <p class="text-red-600 col-span-full text-center py-10">
            ❌ Failed to load menu. <br>
            Please check your connection or try again later. <br>
            <small>(${escapeHtml(error.message)})</small>
          </p>`;
    }
}

function renderMenu(items) {
    if (!menuContainer) return;

    menuContainer.innerHTML = items.map(item => {
        const itemJsonString = JSON.stringify(item);

        return `
        <div class="menu-item bg-white rounded-xl shadow-lg overflow-hidden p-4 flex flex-col transition duration-200 ease-in-out hover:shadow-xl">
          <div class="flex-grow mb-3">
            <h3 class="text-xl font-semibold text-gray-800 mb-1">${escapeHtml(item.name)}</h3>
            <p class="text-gray-600 text-sm">${escapeHtml(item.description || 'No description available.')}</p>
          </div>
          <div class="flex justify-between items-center mt-auto pt-2 border-t border-gray-100">
            <span class="text-orange-600 font-bold text-lg">₹${item.price}</span>
            <button
              onclick='window.app.addToOrder(\`${escapeHtml(itemJsonString)}\`)'
              class="bg-orange-500 hover:bg-orange-600 text-white px-4 py-1.5 rounded-lg transition duration-150 ease-in-out text-sm font-medium shadow-sm hover:shadow-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
            >
              Add
            </button>
          </div>
        </div>
      `;
    }).join('');
}

function addToOrder(escapedItemJsonString) {
    try {
        const item = JSON.parse(escapedItemJsonString);
        if (!item || typeof item.id === 'undefined' || typeof item.name !== 'string' || typeof item.price !== 'number') {
            throw new Error("Invalid item data received.");
        }

        console.log("Adding item:", item.name);
        currentOrder.push(item);
        // Save to localStorage
        localStorage.setItem('currentOrder', JSON.stringify(currentOrder));
        updateCart();
    } catch (e) {
        console.error("ERROR adding item to order:", e, "Received string:", escapedItemJsonString);
        alert("Sorry, there was an error adding that item to your order.");
    }
}

function removeFromOrder(index) {
    if (typeof index !== 'number' || index < 0 || index >= currentOrder.length) {
        console.error("ERROR: Invalid index provided to removeFromOrder:", index);
        return;
    }

    const removedItem = currentOrder.splice(index, 1)[0];
    console.log("Removed item:", removedItem?.name || 'Unknown');
    // Save to localStorage
    localStorage.setItem('currentOrder', JSON.stringify(currentOrder));
    updateCart();
}

function updateCart() {
    if (!orderList || !totalAmountSpan || !placeOrderButton) {
        console.error("ERROR: Cart elements (orderList, totalAmountSpan, or placeOrderButton) not found!");
        return;
    }

    if (currentOrder.length === 0) {
        orderList.innerHTML = '<p class="text-gray-500 italic px-2 py-4">Your order is empty.</p>';
        totalAmountSpan.textContent = '0';
        placeOrderButton.disabled = true;
        placeOrderButton.classList.add('opacity-50', 'cursor-not-allowed');
        placeOrderButton.classList.remove('hover:bg-orange-600');
    } else {
        orderList.innerHTML = currentOrder.map((item, index) => `
            <div class="flex justify-between items-center py-2 px-2 border-b border-gray-100 last:border-b-0">
                <div class="flex-grow mr-2">
                    <h4 class="font-semibold text-sm leading-tight">${escapeHtml(item.name)}</h4>
                    <p class="text-xs text-gray-600">₹${item.price}</p>
                </div>
                <button
                  onclick="window.app.removeFromOrder(${index})"
                  class="text-red-500 hover:text-red-700 text-xs font-semibold px-2 py-1 rounded hover:bg-red-50 transition duration-150"
                  aria-label="Remove ${escapeHtml(item.name)} from order"
                >
                  Remove
                </button>
            </div>
        `).join('');

        const total = currentOrder.reduce((sum, item) => sum + item.price, 0);
        totalAmountSpan.textContent = total;
        placeOrderButton.disabled = false;
        placeOrderButton.classList.remove('opacity-50', 'cursor-not-allowed');
        placeOrderButton.classList.add('hover:bg-orange-600');
    }
}

async function placeOrder() {
    if (currentOrder.length === 0) {
        alert("Your order is empty. Please add some items first!");
        return;
    }
    if (!placeOrderButton) {
        console.error("ERROR: Place Order button not found!");
        return;
    }

    placeOrderButton.disabled = true;
    placeOrderButton.textContent = 'Placing Order...';
    placeOrderButton.classList.add('opacity-75', 'cursor-wait');

    try {
        console.log("Placing order with items:", currentOrder);
        const createdOrder = await createOrder(currentOrder);

        alert(`✅ Order placed successfully!\nOrder ID: ${createdOrder.id}\nTotal Amount: ₹${createdOrder.total_amount}`);
        currentOrder = [];
        // Clear localStorage after successful order
        localStorage.removeItem('currentOrder');
        updateCart();
    } catch (error) {
        console.error("ERROR placing order:", error);
        alert(`❌ Failed to place order. Please try again.\n(${error.message})`);
        placeOrderButton.disabled = false;
    } finally {
        placeOrderButton.textContent = 'Place Order';
        placeOrderButton.classList.remove('opacity-75', 'cursor-wait');
        if (currentOrder.length === 0) {
            placeOrderButton.disabled = true;
            placeOrderButton.classList.add('opacity-50', 'cursor-not-allowed');
            placeOrderButton.classList.remove('hover:bg-orange-600');
        }
    }
}

// --- Global Namespace and Initialization ---
window.app = {
    fetchMenu,
    addToOrder,
    removeFromOrder,
    placeOrder,
    updateCart
};

console.log("App script loaded (no images). Functions attached to window.app");

// --- END OF FILE script.js ---
