// Tab switching logic for the Loop examples
function showTab(event, tabId) {
    // Remove active class from all buttons in the same container
    const tabBtns = event.target.parentElement.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => btn.classList.remove('active'));

    // Remove active class from all content sections
    const tabContents = event.target.parentElement.nextElementSibling.parentElement.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));

    // Add active class to clicked button and target content
    event.target.classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

// Active link highlighting on scroll
const sections = document.querySelectorAll('section');
const navItems = document.querySelectorAll('.nav-item');

window.addEventListener('scroll', () => {
    let current = '';

    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        if (pageYOffset >= (sectionTop - 100)) {
            current = section.getAttribute('id');
        }
    });

    navItems.forEach(item => {
        item.classList.remove('active');
        const link = item.querySelector('a');
        if (link.getAttribute('href') === `#${current}`) {
            item.classList.add('active');
        }
    });
});

// Smooth scroll for anchor links
document.querySelectorAll('.sidebar-nav a').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();

        const targetId = this.getAttribute('href').substring(1);
        const targetElement = document.getElementById(targetId);

        if (targetElement) {
            window.scrollTo({
                top: targetElement.offsetTop - 20,
                behavior: 'smooth'
            });
        }
    });
});

// Search functionality (simple filtering)
const searchInput = document.getElementById('search-input');
const navLinks = document.querySelectorAll('.nav-item a');

if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();

        navLinks.forEach(link => {
            const text = link.textContent.toLowerCase();
            const parent = link.parentElement;

            if (text.includes(term)) {
                parent.style.display = 'block';
            } else {
                parent.style.display = 'none';
            }
        });
    });
}

// Add intersection observer for reveal animations
const observerOptions = {
    threshold: 0.1
};

const observer = window.observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('reveal');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

document.querySelectorAll('.section, .package-card').forEach(el => {
    observer.observe(el);
});

// Mobile Sidebar Toggle
const sidebar = document.querySelector('.sidebar');
const overlay = document.createElement('div');
overlay.className = 'sidebar-overlay';
document.body.appendChild(overlay);

const menuBtn = document.createElement('button');
menuBtn.className = 'mobile-menu-btn';
menuBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>';
document.body.appendChild(menuBtn);

function toggleSidebar() {
    if (sidebar && overlay) {
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
    }
}

if (menuBtn) menuBtn.addEventListener('click', toggleSidebar);
if (overlay) overlay.addEventListener('click', toggleSidebar);

// Close sidebar when clicking a link (on mobile)
document.querySelectorAll('.nav-item a').forEach(link => {
    link.addEventListener('click', () => {
        if (window.innerWidth <= 900) {
            toggleSidebar();
        }
    });
});
