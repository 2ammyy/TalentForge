// In dashboard.html or analytics templates
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('growthChart').getContext('2d');
    
    // Get duration from data attribute
    const dateFormat = "{{ date_format|default:'%a' }}";  // Default to day names
    
    const growthChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [{% for day in daily_signups %}'{{ day.day }}'{% if not forloop.last %},{% endif %}{% endfor %}],
            datasets: [{
                label: 'New Users',
                data: [{% for day in daily_signups %}{{ day.count }}{% if not forloop.last %},{% endif %}{% endfor %}],
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'User Growth ({{ duration|title }})'
                }
            }
        }
    });
});