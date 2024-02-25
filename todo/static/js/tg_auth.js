document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('redirectLink').addEventListener('click', function() {
        fetch('auth/login/tg/generate-td-auth-url/')
            .then(response => response.json())
            .then(data => {
                const telegramUrl = data.url
                window.location.href = telegramUrl;
            })
            .catch(error => console.error('Error fetching the ID:', error));
    });
});