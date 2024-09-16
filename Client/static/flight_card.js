window.onload = function() {
    const currentPath = window.location.pathname;
    console.log(currentPath)
    // 如果当前页面不是登录页面，则检查登录状态
    if (currentPath === '/index.html') {
        fetch('/init', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(response => response.json())
    .then(data => {
        const cards = document.querySelectorAll('.card');
        flights = JSON.parse(data.response)
        const flightContainer = document.getElementById('flight-container');
        // Loop through each flight and create a card
        flights.forEach(flight => {
            const flightCard = document.createElement('div');
            flightCard.classList.add('card');

            flightCard.innerHTML = `
                <h3 class="flight-title">Flight: <span class="flight-number">#${flight.flight_identifier}</span></h3>
                <div class="flight-info">
                    <p><strong>From:</strong> ${flight.source_place}</p>
                    <p><strong>To:</strong> ${flight.destination_place}</p>
                    <p><strong>Departure:</strong> ${new Date(flight.departure_time).toLocaleString()}</p>
                    <p><strong>Price:</strong> $${flight.airfare}</p>
                    <p><strong>Seats Available:</strong> ${flight.seat_availability}</p>
                </div>
<!--                <button class="reserve-btn">Reserve Now</button>-->
            `;

            // Append the flight card to the container
            flightContainer.appendChild(flightCard);
        });
    })
    .catch(error => {
        console.error('Error:', error);
    });
    }
};
const carousel = document.querySelector('.carousel');
const dots = document.querySelectorAll('.dot');
let index = 0;
let interval;

// Auto-scroll function
function startAutoScroll() {
    interval = setInterval(() => {
        index = (index + 1) % dots.length;
        updateCarousel();
    }, 3000); // 3 seconds interval
}

// Stop auto-scroll when hovering
function stopAutoScroll() {
    clearInterval(interval);
}

// Update the carousel based on index
function updateCarousel() {
    carousel.style.transform = `translateX(-${index * 100}%)`;
    dots.forEach(dot => dot.classList.remove('active'));
    dots[index].classList.add('active');
}

// Attach hover event to each dot
dots.forEach(dot => {
    dot.addEventListener('mouseenter', () => {
        stopAutoScroll();
        index = dot.dataset.index;
        updateCarousel();
    });
    dot.addEventListener('mouseleave', startAutoScroll);
});

// Start auto-scroll on page load
startAutoScroll();