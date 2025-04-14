// --- START OF FILE api.js ---

// Use localhost instead of 127.0.0.1 for consistency
const API_BASE_URL = 'http://localhost:5000/api';

// Menu API
export const getMenuItems = async (category = null) => {
    // Construct the URL, handling the category query parameter
    const url = category
        ? `${API_BASE_URL}/menu?category=${encodeURIComponent(category)}` // Encode category just in case
        : `${API_BASE_URL}/menu`;

    console.log(`Fetching menu items from: ${url}`); // Log the URL being fetched

    try {
        const response = await fetch(url);
        if (!response.ok) {
            // Provide more detailed error info if possible
            const errorBody = await response.text();
            console.error('Failed to fetch menu items. Status:', response.status, 'Body:', errorBody);
            throw new Error(`Failed to fetch menu items (Status: ${response.status})`);
        }
        const data = await response.json();
        console.log('Menu items received:', data); // Log the received data
        return data;
    } catch (error) {
        console.error('Error fetching menu items:', error);
        // Re-throw the error so the calling function can handle it
        throw error;
    }
};

// Orders API
export const createOrder = async (items) => {
    const url = `${API_BASE_URL}/orders`;
    console.log(`Creating order at: ${url} with items:`, items); // Log order creation attempt

    // Ensure items being sent have the necessary fields (id, name, price)
    const orderItems = items.map(item => ({
        id: item.id, // Make sure your backend expects 'id' or adjust as needed
        name: item.name,
        price: item.price
        // Add any other fields your backend 'Order' model expects within the 'items' JSON
    }));


    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            // Send only the relevant item details, not the full frontend object if it has extra stuff
            body: JSON.stringify({ items: orderItems }),
        });

        if (!response.ok) {
            const errorBody = await response.text();
            console.error('Failed to create order. Status:', response.status, 'Body:', errorBody);
            throw new Error(`Failed to create order (Status: ${response.status})`);
        }
        const data = await response.json();
        console.log('Order created:', data); // Log the successful order response
        return data;
    } catch (error) {
        console.error('Error creating order:', error);
        throw error;
    }
};

// --- Keep other API functions if needed, but they aren't used by script.js currently ---

export const getOrders = async () => {
    const url = `${API_BASE_URL}/orders`;
    console.log(`Fetching all orders from: ${url}`);
    try {
        const response = await fetch(url);
        if (!response.ok) {
            const errorBody = await response.text();
            console.error('Failed to fetch orders. Status:', response.status, 'Body:', errorBody);
            throw new Error(`Failed to fetch orders (Status: ${response.status})`);
        }
        const data = await response.json();
         console.log('Orders received:', data);
        return data;
    } catch (error) {
        console.error('Error fetching orders:', error);
        throw error;
    }
};

export const updateOrderStatus = async (orderId, status) => {
    const url = `${API_BASE_URL}/orders/${orderId}`;
     console.log(`Updating order ${orderId} status to: ${status} at: ${url}`);
    try {
        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ status }),
        });

        if (!response.ok) {
             const errorBody = await response.text();
            console.error('Failed to update order status. Status:', response.status, 'Body:', errorBody);
            throw new Error(`Failed to update order status (Status: ${response.status})`);
        }
        const data = await response.json();
        console.log('Order status updated:', data);
        return data;
    } catch (error) {
        console.error('Error updating order status:', error);
        throw error;
    }
};
// --- END OF FILE api.js ---