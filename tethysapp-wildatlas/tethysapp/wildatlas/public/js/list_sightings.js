$(document).ready(function() {
    document.querySelectorAll('.formatted-datetime').forEach(function(td) {
        const dateString = td.getAttribute('data-datetime');
        if (dateString) {
            const dateObj = new Date(dateString);
            const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
            const formatted = dateObj.toLocaleString(undefined, options);
            td.innerHTML = `${formatted} (~${td.innerHTML.split('~')[1]}`;
        }
    });
    // Format most recent sighting datetime in stats block
    const recentElem = document.getElementById('most-recent-datetime');
    if (recentElem && recentElem.dataset.datetime) {
        const dateObj = new Date(recentElem.dataset.datetime);
        const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
        recentElem.textContent = dateObj.toLocaleString(undefined, options);
    }

    document.querySelectorAll('.formatted-datetime').forEach(td => {
        const datetimeStr = td.getAttribute('data-datetime');
        if (datetimeStr) {
            const dt = new Date(datetimeStr); // JS parses ISO8601 string in UTC automatically
            // Format in user's local timezone (with options if you want)
            td.textContent = dt.toLocaleString(undefined, { 
                dateStyle: 'medium', 
                timeStyle: 'short' 
            });
        }
    });
});

function deleteSighting(deleteUrl) {
    if (!confirm('Are you sure you want to delete this sighting?')) return;
    fetch(deleteUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
    })
    .then(response => {
        if (response.ok) {
            location.reload();
        } else {
            alert('Failed to delete sighting.');
        }
    });
}
// Helper to get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}