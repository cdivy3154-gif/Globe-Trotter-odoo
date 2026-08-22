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

        // Re-attach event listeners to new content
        attachRouteListeners();
    }

    function attachRouteListeners() {
        document.querySelectorAll('[data-route]').forEach(el => {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                const route = el.dataset.route;
                navigateTo(route);
            });
        });

        // Form submissions (mock)
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                navigateTo('dashboard');
            });
        }

        const registerForm = document.getElementById('register-form');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => {
                e.preventDefault();
                navigateTo('dashboard');
            });
        }

        const createTripForm = document.getElementById('create-trip-form');
        if (createTripForm) {
            createTripForm.addEventListener('submit', (e) => {
                e.preventDefault();
                navigateTo('add-itinerary');
            });
        }
    }

    // Initial navigation
    navigateTo('login');
});
