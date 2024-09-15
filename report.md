**SC6103 Flight Info System Report**

**1. Introduction**
The **SC6103 Flight Info System** is a decentralized flight information management system built using Python for back-end services, JavaScript for the front-end, and Solidity for smart contract integration. The project’s primary goal is to provide flight information, seat reservations, and blockchain-based transaction management using a user-friendly web interface.

**2. System Architecture**

**2.1 Components Overview**
The project consists of three main components:
1. **Client-side**: A Flask-based web application serving as the front-end for users to interact with flight data, monitor reservations, and connect with the blockchain.
2. **Server-side**: Another Flask service that manages requests from the client, processes flight information, and communicates with the MongoDB database.
3. **Blockchain**: A Solidity-based contract deployed on the Ethereum blockchain to handle flight order transactions, ensuring transparency and immutability for users’ reservation records.

**2.2 Data Flow**
1. **User Interaction**: Users interact with the front-end interface, sending requests for flight queries, reservations, and order monitoring.
2. **Back-End Processing**: The server handles the processing of these requests, querying the database for relevant information.
3. **Smart Contract Interaction**: When a reservation is made, it is also recorded on the Ethereum blockchain through a smart contract.

**2.3 Database**
The project uses MongoDB to store flight information, such as:
• Flight identifier
• Source and destination locations
• Departure time
• Seat availability
Additionally, user reservations are stored, and the system can return the current state of reservations.

**3. Client-Side Implementation**
The **Client** folder contains the web interface, which uses Flask to serve the front-end. This interface is where users can query flights, monitor seat availability, and view their orders.

**3.1 Flight Query and Reservation**
The user can:
• Enter source and destination locations to fetch available flights.
• Reserve seats for specific flights, which reduces available seat count in real-time.
The client-side communicates with the server using RESTful API requests and WebSocket communication for real-time updates.

**3.2 Monitoring and Notifications**
The system implements flight monitoring using a multi-threaded approach. Users can subscribe to flight updates, which are sent to the front-end through WebSockets. This allows the client to handle real-time seat reservation updates and notify the user of changes.

**3.3 Blockchain Integration**
MetaMask is used to authorize and sign transactions.

**4. Server-Side Implementation**
The **Server** is responsible for processing the client’s requests, managing MongoDB queries, and interacting with the blockchain. It provides endpoints to query flights, make reservations, and return the current state of the flights.

**4.1 MongoDB Queries**
MongoDB stores all flight-related data. For example:
• query_flight() returns available flights based on user input (source and destination).
• reserve_seats() updates the seat availability and stores the reservation both in MongoDB and the blockchain contract.

**4.2 Smart Contract Interaction**
The server-side also manages the interaction with the blockchain. When a reservation is made, the order ID and user ID are logged onto the Ethereum blockchain using the smart contract methods such as addOrder().

**5. Smart Contract (Solidity)**
The smart contract ensures that flight orders are transparent and immutable. It uses Solidity to handle:
• **Order Storage**: Keeps a record of flight orders on-chain.
• **Order Queries**: Users can view their order history through the getMyOrders() function.
• **Event Handling**: An event OrderAdded is emitted when a new order is added, allowing users to track when their reservations are recorded.

**5.1 Contract Overview**
The contract contains two primary functions:
• **addOrder**: Adds a flight reservation to the blockchain.
• **getMyOrders**: Retrieves a list of all orders for the current user.
This ensures users have full access to their historical reservations, even if the main database is altered or compromised.

**6. Key Challenges and Solutions**
**6.1 Blockchain Integration**
Integrating the blockchain into the existing web architecture was a key challenge. By using Web3.js on the front-end, MetaMask was seamlessly integrated to manage transactions without exposing the user’s private keys.

**6.2 Real-Time Monitoring**
To achieve real-time monitoring of seat reservations, WebSockets were implemented. This allowed instant updates on flight reservations and cancellations, providing a better user experience.

**7. Future Improvements**
• **Security Enhancements**: Additional measures such as multi-factor authentication for sensitive operations like reservations.
• **Optimized Blockchain Interaction**: Gas optimizations for the smart contract and improved transaction handling for high-volume traffic.
• **Scalability**: Using cloud platforms like AWS or Render to scale the server infrastructure for handling more users and requests efficiently.

**8. Conclusion**
The SC6103 Flight Info System demonstrates a comprehensive implementation of a decentralized flight reservation system. By combining Python Flask for the web interface, MongoDB for data management, and Solidity smart contracts for transparent reservations, the project achieves its goal of offering a reliable, secure, and transparent flight management system. Future enhancements will focus on scalability, security, and user experience.