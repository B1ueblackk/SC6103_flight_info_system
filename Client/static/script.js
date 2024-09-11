const socket = io.connect('http://127.0.0.1:5000');
const contractABI = [
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": true,
				"internalType": "address",
				"name": "userId",
				"type": "address"
			},
			{
				"indexed": true,
				"internalType": "uint256",
				"name": "orderId",
				"type": "uint256"
			}
		],
		"name": "OrderAdded",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_orderId",
				"type": "uint256"
			}
		],
		"name": "addOrder",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "getMyOrders",
		"outputs": [
			{
				"components": [
					{
						"internalType": "uint256",
						"name": "orderId",
						"type": "uint256"
					},
					{
						"internalType": "address",
						"name": "userId",
						"type": "address"
					}
				],
				"internalType": "struct FlightOrder.Order[]",
				"name": "",
				"type": "tuple[]"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
];  // 请替换为你的合约 ABI
const contractAddress = "0x93658015b6c7d6c42b4e7631b0b08ec75a475033";  // 请替换为你的合约地址
let contract;

async function initContract() {
    if (typeof window.ethereum !== 'undefined') {
        // 创建 Web3 实例并初始化合约
        const web3 = new Web3(window.ethereum);
        contract = new web3.eth.Contract(contractABI, contractAddress);
    } else {
        alert('MetaMask not detected. Please install MetaMask to interact with the blockchain.');
        throw new Error('MetaMask not detected');
    }
}

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
async function reserveSeats() {
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
    .then(async data => {
        console.log(data); // 调试用，查看完整的返回数据
        console.log()
        let message = "An error occurred"; // 默认提示信息

        if (data.code === 0) {
            order_id = JSON.parse(data['response'])["id"]
            ret_json = JSON.parse(await reserveSeatsAndAddOrder(order_id, data['contract_address']))
            if (ret_json['code'] === 0) {
                message = "Seats reserved successfully!" + '\n' + ret_json['message']
            } else {
                message = ret_json['message']
            }
            // 提取成功的响应信息
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

async function reserveSeatsAndAddOrder(orderId, contractAddress) {
    try{
        initContract()

        const accounts = await ethereum.request({ method: 'eth_requestAccounts' });
        const userAddress = accounts[0];

        console.log('MetaMask address:', userAddress);

        // 构造交易，调用智能合约的 addOrder 方法
        const transactionParameters = {
            to: contractAddress,  // 合约地址
            from: userAddress,    // 用户地址
            data: contract.methods.addOrder(orderId).encodeABI(), // 调用合约函数
        };

        // 让 MetaMask 弹出签名和发送交易的窗口
        const txHash = await ethereum.request({
            method: 'eth_sendTransaction',
            params: [transactionParameters],
        });
        ret_message = 'Transaction hash:' + txHash;
        return JSON.stringify({'code':0, 'message': ret_message})
    } catch (error) {
        ret_message = "Error during MetaMask transaction"
        return JSON.stringify({'code':1, 'message': ret_message})
    }
}
document.addEventListener('DOMContentLoaded', function() {
    const updatesDiv = document.getElementById('monitorResult');
    const allButtons = document.querySelectorAll('button');

    socket.on('monitor_update', function(msg) {
        const newUpdate = document.createElement('p');
        newUpdate.innerText = msg.data;
        updatesDiv.appendChild(newUpdate);
        console.log(msg)
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

  function logout() {
            fetch('/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.code === 0) {
                    window.location.href = '/';  // 重定向到登录页面
                } else {
                    document.getElementById('logoutResult').innerText = data.message;
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }
function login() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log(data)
        if (data.code === 0) {
            window.location.href = "/index.html"; // Successful login, redirect
        } else if (data.code === 2) {
            document.getElementById('loginResult').innerText = data.response;
            metamask()
        }
        else{
            document.getElementById('loginResult').innerText = data.response;
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
async function metamask(){
    if (typeof window.ethereum !== 'undefined') {
                try {
                    // Request accounts from MetaMask
                    const accounts = await ethereum.request({ method: 'eth_requestAccounts' });
                    console.log(1111111)
                    const walletAddress = accounts[0];
                    // Send the address to the Flask server
                    fetch('/save_address', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ walletAddress: walletAddress })
                    }).then(response => response.json())
                    .then(data => {
                        console.log('Address saved:', data);
                    });
                } catch (error) {
                    console.error('Error connecting to MetaMask:', error);
                }
            } else {
                alert('MetaMask is not installed!');
    }
}
// Function to handle registration
function register() {
    const username = document.getElementById('registerUsername').value;
    const password = document.getElementById('registerPassword').value;

    fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('registerResult').innerText = data.response;
        if (data.code === 0) {
            closeRegisterModal();  // Close modal on successful registration
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Functions to handle modal visibility
function showRegisterModal() {
    document.getElementById('registerModal').style.display = 'block';
}

function closeRegisterModal() {
    document.getElementById('registerModal').style.display = 'none';
}

// 检查是否已登录
function checkLoginStatus() {
    fetch('/check_login', {
        method: 'GET',
    })
    .then(response => response.json())
    .then(data => {
        if (data.code !== 0) {
            window.location.href = '/';  // 如果未登录，重定向到登录页面
        }
    })
    .catch(error => {
        console.error('Error during login check:', error);
    });
}

// // 页面加载时检查登录状态
window.onload = function() {
    const currentPath = window.location.pathname;
    console.log(currentPath)
    // 如果当前页面不是登录页面，则检查登录状态
    if (currentPath !== '/login.html' && currentPath !== '/') {
        checkLoginStatus();
    }
};