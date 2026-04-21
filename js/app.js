// -------------- Real Backend Bindings -------------- //
const API_URL = 'http://127.0.0.1:5001';

// Global Fetch Intercept to automatically send layout Session Cookies and intercept Unauthorized responses
const originalFetch = window.fetch;
window.fetch = async function() {
    let [resource, config] = arguments;
    if (!config) config = {};
    config.credentials = 'include';
    const res = await originalFetch(resource, config);
    if(res.status === 401 && !resource.includes('/login') && !resource.includes('/check-session')) {
        handleLogout();
    }
    return res;
};

let isLoggedIn = false;
let authMode = 'login'; // 'login' or 'signup'
let currentUser = null; 

let allItemsStore = [];
let allClaimsStore = [];

// DOM References
const navbar = document.getElementById('navbar');
const navLinks = document.querySelectorAll('.nav-links a[data-page]');
const pages = document.querySelectorAll('.page');

document.addEventListener('DOMContentLoaded', async () => {
    // Session State Authentication Restorer
    try {
        const res = await fetch(`${API_URL}/check-session`);
        if(res.ok) {
            const data = await res.json();
            currentUser = data.user;
            currentUser.role = data.role;
            isLoggedIn = true;
            
            initAuthToggle();
            initForms();
            initFilters();
            
            navbar.classList.remove('hidden');
            await fetchMetadata();
            
            if (currentUser.role === 'admin') {
                const adminNav = document.getElementById('nav-admin');
                if (adminNav) adminNav.classList.remove('hidden');
            }
            // Retain the visual dashboard entry
            navigateTo('dashboard');
            return;
        }
    } catch (err) {
        console.log("No persistent session found.");
    }
    
    initAuthToggle();
    initForms();
    initFilters();
});

// -------------- Bootloader Metadata -------------- //
async function fetchMetadata() {
    try {
        const catRes = await fetch(`${API_URL}/categories`);
        const catData = await catRes.json();
        
        const locRes = await fetch(`${API_URL}/locations`);
        const locData = await locRes.json();
        
        const catOptions = `<option value="">Select Category</option>` + catData.categories.map(c => `<option value="${c.category_id}">${c.category_name}</option>`).join('');
        const filterCatOptions = `<option value="">All Categories</option>` + catData.categories.map(c => `<option value="${c.category_id}">${c.category_name}</option>`).join('');

        const locOptions = `<option value="">Select Location</option>` + locData.locations.map(l => `<option value="${l.location_id}">${l.location_name}</option>`).join('');

        // Form Populations
        document.getElementById('lost-category').innerHTML = catOptions;
        document.getElementById('found-category').innerHTML = catOptions;
        document.getElementById('filter-category').innerHTML = filterCatOptions;
        
        document.getElementById('lost-location-select').innerHTML = locOptions;
        document.getElementById('found-location-select').innerHTML = locOptions;
    } catch(err) {
        console.error("Failed to connect to backend", err);
    }
}

// -------------- Navigation Logic -------------- //
function navigateTo(pageId) {
    pages.forEach(p => { p.classList.add('hidden'); p.classList.remove('active'); });
    navLinks.forEach(l => l.classList.remove('active'));
    
    const target = document.getElementById(`page-${pageId}`);
    if (target) {
        target.classList.remove('hidden');
        setTimeout(() => target.classList.add('active'), 10);
    }
    
    const activeLink = document.querySelector(`.nav-links a[data-page="${pageId}"]`);
    if (activeLink) activeLink.classList.add('active');

    // Toggle background modes (Login vs Internal/Dashboard)
    if (pageId === 'login') {
        document.body.classList.add('login-mode');
        document.body.classList.remove('dashboard-mode');
    } else {
        document.body.classList.remove('login-mode');
        document.body.classList.add('dashboard-mode');
    }

    // Action routers
    if (pageId === 'dashboard') {
        fetchAllItems(); // Deep fetch refresh pattern
    } else if (pageId === 'view-items') {
        fetchAllItems(); 
    } else if (pageId === 'admin') {
        fetchClaims(); 
    }
}

navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = link.getAttribute('data-page');
        if (page === 'login' && isLoggedIn) {
            handleLogout();
            return;
        }
        navigateTo(page);
    });
});

async function handleLogout() {
    isLoggedIn = false;
    currentUser = null;
    navbar.classList.add('hidden');
    try { await fetch(`${API_URL}/logout`); } catch(e) {}
    navigateTo('login');
}

// -------------- Handlers: Auth -------------- //
function initAuthToggle() {
    const toggleLink = document.getElementById('auth-toggle-link');
    const toggleText = document.getElementById('auth-toggle-text');
    const title = document.getElementById('auth-title');
    const subtitle = document.getElementById('auth-subtitle');
    const submitBtn = document.getElementById('auth-submit');
    const nameGroup = document.getElementById('name-group');
    const adminToggle = document.getElementById('admin-login-link');

    // Role Tab Handlers
    const roleTabs = document.querySelectorAll('.role-tab');
    if (roleTabs.length) {
        roleTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                roleTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');

                const role = tab.getAttribute('data-role');
                if (role === 'admin') {
                    authMode = 'admin';
                    nameGroup.classList.add('hidden');
                    document.getElementById('reg-name').required = false;
                    title.textContent = 'Admin Portal';
                    subtitle.textContent = 'Enter administrative credentials.';
                    submitBtn.textContent = '🚀 Sign In as Admin';
                    document.getElementById('email').value = 'harsha@srmap.edu.in';
                    document.getElementById('email').placeholder = 'admin@srmap.edu.in';
                } else if (role === 'user') {
                    authMode = 'login';
                    nameGroup.classList.add('hidden');
                    document.getElementById('reg-name').required = false;
                    title.textContent = 'Lost & Found';
                    subtitle.textContent = 'Campus Item Management';
                    submitBtn.textContent = '🚀 Sign In';
                    document.getElementById('email').value = '';
                    document.getElementById('email').placeholder = 'name@srmap.edu.in';
                }
            });
        });
    }

    adminToggle.addEventListener('click', (e) => {
        e.preventDefault();
        authMode = 'admin';
        nameGroup.classList.add('hidden');
        document.getElementById('reg-name').required = false;
        title.textContent = 'Admin Portal';
        subtitle.textContent = 'Enter administrative credentials.';
        toggleText.textContent = 'Standard user?';
        toggleLink.textContent = 'User Login';
        submitBtn.textContent = 'Log In as Admin';
        adminToggle.style.display = 'none';
        
        // Pre-fill admin email
        document.getElementById('email').value = 'harsha@srmap.edu.in';
    });

    toggleLink.addEventListener('click', (e) => {
        e.preventDefault();
        if (authMode === 'admin') {
            authMode = 'login';
            nameGroup.classList.add('hidden');
            document.getElementById('reg-name').required = false;
            title.textContent = 'Welcome Back';
            subtitle.textContent = 'Log in to manage lost and found items.';
            toggleText.textContent = "Don't have an account?";
            toggleLink.textContent = 'Sign Up';
            submitBtn.textContent = 'Log In';
            adminToggle.style.display = 'inline-block';
            document.getElementById('email').value = '';
        } else if (authMode === 'login') {
            authMode = 'signup';
            nameGroup.classList.remove('hidden');
            document.getElementById('reg-name').required = true;
            title.textContent = 'Create Account';
            subtitle.textContent = 'Sign up to manage lost and found items.';
            toggleText.textContent = 'Already have an account?';
            toggleLink.textContent = 'Log In';
            submitBtn.textContent = 'Sign Up';
            adminToggle.style.display = 'none';
        } else {
            authMode = 'login';
            nameGroup.classList.add('hidden');
            document.getElementById('reg-name').required = false;
            title.textContent = 'Welcome Back';
            subtitle.textContent = 'Log in to manage lost and found items.';
            toggleText.textContent = "Don't have an account?";
            toggleLink.textContent = 'Sign Up';
            submitBtn.textContent = 'Log In';
            adminToggle.style.display = 'inline-block';
        }
    });

    document.getElementById('auth-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value.trim();
            const submitBtn = document.getElementById('auth-submit');
            submitBtn.textContent = 'Processing...';

            console.log(`Attempting login with: ${email}`);

            try {
                if (authMode === 'login' || authMode === 'admin') {
                    const res = await fetch(`${API_URL}/login`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ email, password })
                    });
                    const data = await res.json();
                    if(!res.ok) throw new Error(data.error || 'Invalid credentials');
                    currentUser = data.user;
                    currentUser.role = data.role;
                } else {
                    const name = document.getElementById('reg-name').value.trim();
                    const regRes = await fetch(`${API_URL}/register`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ name, email, password })
                    });
                    const regData = await regRes.json();
                    if(!regRes.ok) throw new Error(regData.error || 'Registration failed');
                    
                    const loginRes = await fetch(`${API_URL}/login`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ email, password })
                    });
                    const loginData = await loginRes.json();
                    if(!loginRes.ok) throw new Error(loginData.error || 'Login failed after registration');
                    currentUser = loginData.user;
                    currentUser.role = loginData.role;
                }
            
            isLoggedIn = true;
            navbar.classList.remove('hidden');
            document.getElementById('auth-form').reset();
            
            // Kickstart Metadata fetch since connection is verified
            await fetchMetadata();
            
            if (currentUser.role === 'admin') {
                const adminNav = document.getElementById('nav-admin');
                if (adminNav) adminNav.classList.remove('hidden');
                navigateTo('admin');
            } else {
                const adminNav = document.getElementById('nav-admin');
                if (adminNav) adminNav.classList.add('hidden');
                navigateTo('dashboard');
            }
        } catch(err) {
            alert("Error: " + err.message);
        } finally {
            if (authMode === 'login' || authMode === 'admin') {
                submitBtn.textContent = authMode === 'admin' ? '🚀 Sign In as Admin' : '🚀 Sign In';
            } else {
                submitBtn.textContent = '🚀 Sign Up';
            }
        }
    });
}

// -------------- Handlers: Insertions -------------- //
async function handleReport(type, formEvent) {
    formEvent.preventDefault();
    if (!currentUser) return alert("System Auth Token Failed. Log out and log back in.");

    const nameStr = type === 'lost' ? 'lost-name' : 'found-name';
    const catStr = type === 'lost' ? 'lost-category' : 'found-category';
    const locStr = type === 'lost' ? 'lost-location-select' : 'found-location-select';
    const descStr = type === 'lost' ? 'lost-desc' : 'found-desc';

    const payload = {
        user_id: currentUser.user_id,
        item_name: document.getElementById(nameStr).value,
        category_id: parseInt(document.getElementById(catStr).value),
        location_id: parseInt(document.getElementById(locStr).value),
        description: document.getElementById(descStr).value
    };

    try {
        const res = await fetch(`${API_URL}/report-${type}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if(!res.ok) throw new Error(data.error);

        formEvent.target.reset();
        
        // Smart Matching functionality (Alerts users heavily if related assets exist natively)
        if (type === 'lost' && data.potential_matches && data.potential_matches.length > 0) {
            showMatchPopup(data.potential_matches);
        } else {
            alert(`✅ Record submitted cleanly directly to securely partitioned tables.`);
            navigateTo('dashboard'); 
        }
    } catch(err) {
        alert("Action failed: " + err.message);
    }
}

function initForms() {
    document.getElementById('lost-form').addEventListener('submit', (e) => handleReport('lost', e));
    document.getElementById('found-form').addEventListener('submit', (e) => handleReport('found', e));
}

// -------------- Popup Components -------------- //
window.showMatchPopup = function(matches) {
    const container = document.getElementById('match-popup-items');
    container.innerHTML = matches.map(m => `
        <div class="match-item">
            <h4>${m.item_name}</h4>
            <p>Found at: ${m.location_name} • Logged on ${m.found_date}</p>
        </div>
    `).join('');
    document.getElementById('match-popup').classList.remove('hidden');
};

window.closeMatchPopup = function() {
    document.getElementById('match-popup').classList.add('hidden');
    navigateTo('dashboard');
};

// -------------- Data Polling -------------- //
async function fetchAllItems() {
    try {
        const res = await fetch(`${API_URL}/items`);
        const data = await res.json();
        allItemsStore = [...(data.lost || []), ...(data.found || [])];
        renderAllItems();
        
        if(document.getElementById('page-dashboard').classList.contains('active')) { 
            renderDashboard();
        }
    } catch(err) {
        console.error("Failed to load schema", err);
    }
}

function initFilters() {
    document.getElementById('filter-status').addEventListener('change', () => renderAllItems());
    document.getElementById('filter-category').addEventListener('change', () => renderAllItems());
}

// -------------- Render Functions -------------- //
function createItemCardHTML(item) {
    const badgeClass = item.status === 'Lost' ? 'badge-lost' : 'badge-found';
    const pinIcon = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:4px;"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>`;

    return `
        <div class="card item-card" onclick="viewItemDetail(${item.report_id}, '${item.status}')">
            <div class="item-card-header">
                <span class="badge ${badgeClass}">${item.status}</span>
                <span style="font-size: 13px; color: var(--color-text-light); font-weight: 500;">${item.report_date}</span>
            </div>
            <h3 class="item-title">${item.item_name}</h3>
            <span class="item-category">${item.category_name}</span>
            <div class="item-location"> ${pinIcon} ${item.location_name} </div>
            <div class="item-reporter" style="font-size: 11px; margin-top: 10px; color: var(--color-text-sub); border-top: 1px solid rgba(0,0,0,0.05); pt: 8px;">
                👤 ${item.reported_by} <br/>
                <span style="opacity: 0.8;">${item.reported_email}</span>
            </div>
        </div>
    `;
}

window.renderDashboard = function() {
    const lostItems = allItemsStore.filter(i => i.status === 'Lost').slice(0, 4);
    const foundItems = allItemsStore.filter(i => i.status === 'Found').slice(0, 4);

    document.getElementById('recent-lost-grid').innerHTML = lostItems.map(createItemCardHTML).join('') || '<p style="color:var(--color-text-sub);">No active missing reports.</p>';
    document.getElementById('recent-found-grid').innerHTML = foundItems.map(createItemCardHTML).join('') || '<p style="color:var(--color-text-sub);">No currently logged items.</p>';
}

window.renderAllItems = function() {
    const statusVal = document.getElementById('filter-status').value;
    const catSelect = document.getElementById('filter-category');
    const selectedCatName = catSelect.options[catSelect.selectedIndex]?.text || '';
    
    let dataset = allItemsStore;
    if (statusVal !== 'All') dataset = dataset.filter(i => i.status === statusVal);
    if (catSelect.value !== "") dataset = dataset.filter(i => i.category_name === selectedCatName);

    const grid = document.getElementById('all-items-grid');
    if (dataset.length === 0) {
        grid.innerHTML = '<p style="grid-column: 1/-1; text-align:center; color: var(--color-text-sub); padding: 40px 0;">No items found in active memory mappings.</p>';
    } else {
        grid.innerHTML = dataset.map(createItemCardHTML).join('');
    }
}

// -------------- Item Details & Async Claims -------------- //
window.viewItemDetail = function(reportId, status) {
    const item = allItemsStore.find(i => i.report_id === reportId && i.status === status);
    if (!item) return;

    const badgeClass = item.status === 'Lost' ? 'badge-lost' : 'badge-found';
    // Parameter parsing logic -> API takes either lost_id or found_id dynamically mapped
    const claimParams = status === 'Lost' ? `${reportId}, null` : `null, ${reportId}`;

    document.getElementById('item-detail-content').innerHTML = `
        <span class="badge ${badgeClass}">${item.status}</span>
        <h1>${item.item_name}</h1>
        <p class="subtitle">${item.category_name} • Handled on ${item.report_date}</p>
        
        <div class="detail-info">
            <p><strong>Location</strong> ${item.location_name}</p>
            <p><strong>Description</strong> ${item.description}</p>
            <p><strong>Logged By</strong> ${item.reported_by}</p>
        </div>
        <button class="btn btn-primary btn-block" onclick="requestClaim(${claimParams})">Request Claim Ticket</button>
    `;
    navigateTo('claim-item');
};

window.requestClaim = async function(lost_id, found_id) {
    if (!currentUser) return alert("System Auth Token Failed. Log back in.");
    try {
        const payload = {
            user_id: currentUser.user_id,
            lost_id: lost_id,
            found_id: found_id
        };
        const res = await fetch(`${API_URL}/claim`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if(!res.ok) throw new Error(data.error);

        alert('✅ Your claim has been requested! It is queued into the Admin panel for reviewing constraints.');
        navigateTo('dashboard');
    } catch(err) {
        alert("Operation Refused: " + err.message);
    }
};

// -------------- Admin Architecture -------------- //
async function fetchClaims() {
    try {
        const res = await fetch(`${API_URL}/claims`);
        const data = await res.json();
        allClaimsStore = data.claims;
        renderAdminTable();
    } catch(err) {
        console.error("Critical failure during claim synchronization.", err);
    }
}

function renderAdminTable() {
    const tbody = document.getElementById('admin-table-body');
    if(!allClaimsStore || allClaimsStore.length === 0) {
       tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No pending queue structures.</td></tr>';
       return;
    }
    
    tbody.innerHTML = allClaimsStore.map(c => {
        let statusBadge = 'badge-pending';
        if (c.claim_status === 'Approved') statusBadge = 'badge-found'; 
        if (c.claim_status === 'Rejected') statusBadge = 'badge-lost';  

        const actionsConfig = c.claim_status === 'Pending' 
            ? `
                <button class="action-btn" onclick="updateClaimStatus(${c.claim_id}, 'Approved')">Approve</button>
                <button class="action-btn reject" onclick="updateClaimStatus(${c.claim_id}, 'Rejected')">Reject</button>
              ` 
            : `<span style="color:var(--color-text-light); font-size: 13px;">Review Executed</span>`;

        return `
            <tr>
                <td><strong>${c.item_name}</strong> <br/><span style="font-size:12px;color:var(--color-text-sub)">${c.claim_type}</span></td>
                <td>${c.claimant_name} <br/><span style="font-size:12px;color:var(--color-text-sub)">${c.claimant_email}</span></td>
                <td>${c.claim_date}</td>
                <td><span class="badge ${statusBadge}">${c.claim_status}</span></td>
                <td>${actionsConfig}</td>
            </tr>
        `;
    }).join('');
}

window.updateClaimStatus = async function(id, newStatus) {
    if(!confirm(`Commit execution flag: ${newStatus}?`)) return;
    try {
        const res = await fetch(`${API_URL}/update-claim`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ claim_id: id, status: newStatus })
        });
        const data = await res.json();
        if(!res.ok) throw new Error(data.error);
        
        fetchClaims(); // Run deep synchronization array updates immediately
    } catch(err) {
        alert("Operation Refused: " + err.message);
    }
};
