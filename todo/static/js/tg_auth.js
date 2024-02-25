document.addEventListener('DOMContentLoaded', function() {
    document.body.addEventListener('click', function(event) {
        if (event.target.id === 'redirectLink') {
            fetch('/auth/login/tg/generate-td-auth-url/')
                .then(response => response.json())
                .then(data => {
                    window.location.href = data.url;
                })
                .catch(error => console.error('Error fetching the ID:', error));
        }
    });
});