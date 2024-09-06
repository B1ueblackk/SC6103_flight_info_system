const socket = io.connect('http://127.0.0.1:5000');

// 查询航班信息
function queryFlight() {
    const sourcePlace = document.getElementById('source').value;
    const destination = document.getElementById('destination').value;

    document.getElementById('queryFlightResult').innerText = ''
    const flightContainer = document.getElementById('flightContainer');
    flightContainer.innerHTML = ''; // 清空表格内容

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
        console.log(data)
        if (data.code === 0) {
            const flights = JSON.parse(data.response);
            updateFlightTable(flights); // 更新表格
        } else {
            document.getElementById('queryFlightResult').innerText = data.response;
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function updateFlightTable(flights) {
    const flightContainer = document.getElementById('flightContainer');

    // 构建表格的基础结构
    let tableHTML = `
    <table>
        <thead>
            <tr>
                <th>Flight Identifier</th>
                <th>Source Place</th>
                <th>Destination Place</th>
                <th>Departure Time</th>
                <th>Airfare</th>
                <th>Seat Availability</th>
            </tr>
        </thead>
        <tbody>
    `;

    // 为每个航班添加表格行
    flights.forEach(flight => {
        tableHTML += `
            <tr>
                <td>${flight.flight_identifier}</td>
                <td>${flight.source_place}</td>
                <td>${flight.destination_place}</td>
                <td>${flight.departure_time}</td>
                <td>${flight.airfare}</td>
                <td>${flight.seat_availability}</td>
            </tr>
        `;
    });

    // 结束表格
    tableHTML += `
        </tbody>
    </table>
    `;

    // 一次性将完整的表格结构插入容器
    flightContainer.innerHTML = tableHTML;
}


// 查询航班信息
function queryFlightInfo() {
    const flightId = document.getElementById('flightInfoId').value;

    document.getElementById('queryFlightInfoResult').innerText = ''
    const flightInfoContainer = document.getElementById('flightInfoContainer');
    flightInfoContainer.innerHTML = ''; // 清空表格内容


    fetch('/query_flight_info', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            source_place: flightId
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log(data)
        if (data.code === 0) {
            let flightInfo = JSON.parse(data.response);
            updateFlightInfoTable(flightInfo);
        }
        else {
            document.getElementById('queryFlightInfoResult').innerText = data.response;
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function updateFlightInfoTable(flightInfo) {
    // 将表格插入到容器中
    console.log(flightInfo);
    document.getElementById('flightInfoContainer').innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Flight Identifier</th>
                    <th>Source Place</th>
                    <th>Destination Place</th>
                    <th>Departure Time</th>
                    <th>Airfare</th>
                    <th>Seat Availability</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>${flightInfo.flight_identifier}</td>
                    <td>${flightInfo.source_place}</td>
                    <td>${flightInfo.destination_place}</td>
                    <td>${flightInfo.departure_time}</td>
                    <td>${flightInfo.airfare}</td>
                    <td>${flightInfo.seat_availability}</td>
                </tr>
            </tbody>
        </table>
    `;
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
        console.log(data); // 调试用，查看完整的返回数据
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


document.addEventListener('DOMContentLoaded', function() {
    const updatesDiv = document.getElementById('monitorResult');
    const allButtons = document.querySelectorAll('button');

    socket.on('monitor_update', function(msg) {
        const newUpdate = document.createElement('p');
        newUpdate.innerText = msg.data;
        updatesDiv.appendChild(newUpdate);

        if (msg.data === "Monitor finished!") {
            // 重新启用所有按钮
            allButtons.forEach(button => {
                button.disabled = false;
            });
        }
    });
});

function monitorFlight() {
    const flightId = document.getElementById('monitorFlightId').value;
    const periodTime = document.getElementById('periodTime').value;

    // 选择页面上所有按钮并禁用它们
    const allButtons = document.querySelectorAll('button');
    allButtons.forEach(button => {
        button.disabled = true;
    });

    // 获取用于显示监视更新的容器
    const updatesDiv = document.getElementById('monitorResult');
    if (!updatesDiv) {
        console.error('Element with id "monitorResult" not found.');
        // 如果找不到容器，重新启用按钮
        allButtons.forEach(button => {
            button.disabled = false;
        });
        return;
    }
    // 清空之前的监视更新
    updatesDiv.innerHTML = '';

    // 发送监视请求
    fetch(`/start_monitor?flightId=${flightId}&periodTime=${periodTime}`)
        .then(response => response.json())
        .then(data => {
            console.log(data);
            if (data.code !== 0) {
                // 如果返回的代码不为0，显示错误信息并重新启用按钮
                updatesDiv.innerHTML = '';
                const newUpdate = document.createElement('p');
                newUpdate.innerText = data.response;
                updatesDiv.appendChild(newUpdate);
                allButtons.forEach(button => {
                    button.disabled = false;
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // 如果请求出错，重新启用按钮
            allButtons.forEach(button => {
                button.disabled = false;
            });
        });
}
