const socket = io.connect('http://127.0.0.1:5000');

// 查询航班信息
function queryFlight() {
    const sourcePlace = document.getElementById('source').value;
    const destination = document.getElementById('destination').value;

    fetch('/query_flight', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            source_place: sourcePlace,
            destination: destination
        })
    })
    .then(response => response.json())
    .then(data => {
        let message = "An error occurred"; // 默认提示信息

        if (data.code === 0) {
            message = data.response; // 提取成功的响应信息
        } else if (data.code === 1) {
            message = "Error: " + data.response; // 错误提示信息
        }

        document.getElementById('queryFlightResult').innerText = message;
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('queryFlightResult').innerText = "An error occurred while querying flight.";
    });
}


// 预定座位
function reserveSeats() {
    const flightId = document.getElementById('flightId').value;
    const seatsCount = document.getElementById('seatsCount').value;

    fetch('/reserve_seats', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            flight_id: flightId,
            seats_count: seatsCount
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('reserveResult').innerText = JSON.stringify(data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// 预定座位
function reserveSeats() {
    const flightId = document.getElementById('flightId').value;
    const seatsCount = document.getElementById('seatsCount').value;

    fetch('/reserve_seats', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            flight_id: flightId,
            seats_count: seatsCount
        })
    })
    .then(response => response.json())
    .then(data => {
        let message = "An error occurred"; // 默认提示信息

        if (data.code === 0) {
            message = "Seats reserved successfully!"; // 提取成功的响应信息
        } else if (data.code === 1) {
            message = "Error: " + data.response; // 错误提示信息
        }

        document.getElementById('reserveResult').innerText = message;
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('reserveResult').innerText = "An error occurred while reserving seats.";
    });
}
