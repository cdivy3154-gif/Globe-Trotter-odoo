// ── M3 Theme Toggle ──
function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') === 'dark';
    html.setAttribute('data-theme', isDark ? 'light' : 'dark');
    const icon  = document.getElementById('theme-icon');
    const label = document.getElementById('theme-label');
    if (icon)  icon.textContent  = isDark ? 'dark_mode'  : 'light_mode';
    if (label) label.textContent = isDark ? 'Dark Mode'  : 'Light Mode';
}

document.addEventListener('DOMContentLoaded', () => {
    const mainContent = document.getElementById('main-content');
    const sidebar = document.getElementById('sidebar');

    // Route handling
    const routes = {
        'login': 'tpl-login',
        'register': 'tpl-register',
        'dashboard': 'tpl-dashboard',
        'create-trip': 'tpl-create-trip',
        'add-itinerary': 'tpl-add-itinerary',
        'my-trips': 'tpl-my-trips',
        'profile': 'tpl-profile',
        'search': 'tpl-search',
        'itinerary': 'tpl-itinerary',
        'community': 'tpl-community',
        'calendar': 'tpl-calendar',
        'admin': 'tpl-admin'
        // Add more routes here as we build them
    };

    // Public routes that don't need sidebar
    const publicRoutes = ['login', 'register'];

    function navigateTo(route) {
        if (!routes[route]) route = 'login'; // Default route

        // Render template
        const template = document.getElementById(routes[route]);
        if (template) {
            mainContent.innerHTML = template.innerHTML;
        }

        // Toggle Sidebar
        if (publicRoutes.includes(route)) {
            sidebar.classList.add('hidden');
            mainContent.style.marginLeft = '0';
        } else {
            sidebar.classList.remove('hidden');
            mainContent.style.marginLeft = 'var(--sidebar-width)';
        }

        // Update active nav link
        document.querySelectorAll('.nav-links a').forEach(link => {
            if (link.dataset.route === route) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    } // <-- closing brace for navigateTo

    // Event Delegation for routing
    document.body.addEventListener('click', (e) => {
        const routeEl = e.target.closest('[data-route]');
        if (routeEl) {
            e.preventDefault();
            navigateTo(routeEl.dataset.route);
        }
    });

    // Event Delegation for form submissions
    document.body.addEventListener('submit', (e) => {
        if (e.target.id === 'login-form' || e.target.id === 'register-form') {
            e.preventDefault();
            navigateTo('dashboard');
        } else if (e.target.id === 'create-trip-form') {
            e.preventDefault();
            navigateTo('add-itinerary');
        }
    });

    // Initial navigation
    navigateTo('login');
});
