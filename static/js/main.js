// BizManager - Main JavaScript
// Invoice logic is handled in invoice_create.html directly

// ========================
// Modal functions (used globally)
// ========================
function openModal(content) {
    document.getElementById('modal-content').innerHTML = content;
    document.getElementById('modal-overlay').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
    document.getElementById('modal-content').innerHTML = '';
}

// Close modal on overlay click
document.addEventListener('DOMContentLoaded', function () {
    const overlay = document.getElementById('modal-overlay');
    if (overlay) {
        overlay.addEventListener('click', function (e) {
            if (e.target === this) closeModal();
        });
    }
});

// ========================
// Quick Add Customer
// ========================
function quickAddCustomer() {
    const content = `
        <div class="p-6">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-bold text-gray-800">
                    <i class="fas fa-user-plus text-blue-500 mr-2"></i>Quick Add Customer
                </h3>
                <button onclick="closeModal()" class="text-gray-400 hover:text-gray-600">
                    <i class="fas fa-times text-xl"></i>
                </button>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="text-sm font-medium text-gray-700 mb-1 block">Customer Name *</label>
                    <input type="text" id="qc-name" class="form-input" placeholder="Enter name">
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-700 mb-1 block">Phone</label>
                    <input type="text" id="qc-phone" class="form-input" placeholder="03xx-xxxxxxx">
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-700 mb-1 block">Address</label>
                    <textarea id="qc-address" class="form-input" rows="2" placeholder="Optional"></textarea>
                </div>
                <div class="flex gap-3 pt-1">
                    <button type="button" onclick="submitQuickCustomer()"
                            class="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-lg font-medium transition-colors">
                        <i class="fas fa-save mr-2"></i>Save Customer
                    </button>
                    <button type="button" onclick="closeModal()"
                            class="px-4 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50">
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    `;
    openModal(content);
}

function submitQuickCustomer() {
    const name = document.getElementById('qc-name').value.trim();
    if (!name) { alert('Customer name is required!'); return; }

    fetch('/customers/quick-add/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({
            name: name,
            phone: document.getElementById('qc-phone').value.trim(),
            address: document.getElementById('qc-address').value.trim()
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const select = document.getElementById('customer-select');
            const opt = new Option(data.name, data.id, true, true);
            select.appendChild(opt);
            closeModal();
            showToast(`Customer "${data.name}" added!`, 'success');
        } else {
            alert('Error: ' + (data.error || 'Could not save'));
        }
    })
    .catch(() => alert('Network error. Try again.'));
}

// ========================
// Quick Add Broker
// ========================
function quickAddBroker() {
    const content = `
        <div class="p-6">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-bold text-gray-800">
                    <i class="fas fa-handshake text-orange-500 mr-2"></i>Quick Add Broker
                </h3>
                <button onclick="closeModal()" class="text-gray-400 hover:text-gray-600">
                    <i class="fas fa-times text-xl"></i>
                </button>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="text-sm font-medium text-gray-700 mb-1 block">Broker Name *</label>
                    <input type="text" id="qb-name" class="form-input" placeholder="Enter name">
                </div>
                <div>
                    <label class="text-sm font-medium text-gray-700 mb-1 block">Phone</label>
                    <input type="text" id="qb-phone" class="form-input" placeholder="03xx-xxxxxxx">
                </div>
                <div class="flex gap-3 pt-1">
                    <button type="button" onclick="submitQuickBroker()"
                            class="flex-1 bg-orange-500 hover:bg-orange-600 text-white py-2.5 rounded-lg font-medium transition-colors">
                        <i class="fas fa-save mr-2"></i>Save Broker
                    </button>
                    <button type="button" onclick="closeModal()"
                            class="px-4 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50">
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    `;
    openModal(content);
}

function submitQuickBroker() {
    const name = document.getElementById('qb-name').value.trim();
    if (!name) { alert('Broker name is required!'); return; }

    fetch('/brokers/quick-add/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({
            name: name,
            phone: document.getElementById('qb-phone').value.trim()
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const select = document.getElementById('broker-select');
            const opt = new Option(data.name, data.id, true, true);
            select.appendChild(opt);
            closeModal();
            showToast(`Broker "${data.name}" added!`, 'success');
        } else {
            alert('Error: ' + (data.error || 'Could not save'));
        }
    })
    .catch(() => alert('Network error. Try again.'));
}

// ========================
// Utilities
// ========================
function getCookie(name) {
    let val = null;
    document.cookie.split(';').forEach(c => {
        c = c.trim();
        if (c.startsWith(name + '=')) val = decodeURIComponent(c.slice(name.length + 1));
    });
    return val;
}

function showToast(message, type = 'info') {
    const colors = { success: 'bg-green-500', error: 'bg-red-500', info: 'bg-blue-500', warning: 'bg-yellow-500' };
    const icons = { success: 'fa-check-circle', error: 'fa-exclamation-circle', info: 'fa-info-circle', warning: 'fa-exclamation-triangle' };
    const toast = document.createElement('div');
    toast.className = `fixed top-5 right-5 z-[9999] ${colors[type]} text-white px-5 py-3 rounded-xl shadow-xl text-sm font-medium flex items-center gap-2`;
    toast.innerHTML = `<i class="fas ${icons[type]}"></i>${message}`;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function confirmDelete(msg) {
    return confirm(msg || 'Are you sure you want to delete this?');
}