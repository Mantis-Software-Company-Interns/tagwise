function showTab(tabName) {
    // Hide all forms
    document.querySelectorAll('.form').forEach(form => {
        form.classList.remove('active');
    });
    
    // Remove active class from all tabs
    document.querySelectorAll('.tab-btn').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected form
    document.getElementById(tabName + '-form').classList.add('active');
    
    // Add active class to selected tab
    event.target.classList.add('active');
}

// Form submission handling
document.getElementById('signin-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    console.log('Sign In:', { email, password });
    // Add your sign in logic here
});

document.getElementById('signup-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const email = document.getElementById('new-email').value;
    const password = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    if (password !== confirmPassword) {
        alert('Passwords do not match!');
        return;
    }
    
    console.log('Sign Up:', { email, password });
    // Add your sign up logic here
}); 