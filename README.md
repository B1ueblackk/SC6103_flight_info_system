# SC6103_flight_info_system

## Materials to be submitted
* demonstrate working programs
* submit a lab report
* well-commented source code

## Requirements
* use UDP protocol(assume all clients know the address and port of the server)
* client-server communication:clients provide interfaces for users to invoke services: 
	* users(input) -> clients(send request) -> server(perform and return) -> clients(present)
* design the request and reply message formats
* implement the marshalling/unmarshalling
* make sure the system is fault-tolerance
* server continuously handle the requests from clients
* returned or error messages should be printed at the console(server)

## Services to be implemented
* Query the flight
	1. Query by specifying the source and destination places
	2. All matched results should be returned
	3. The server would return an error message if no flight matched.
* Query the information about the flight
	1. the departure time, airfare and seat availability can be queried by the flight identifier
	2. The server would return an error message if no flight matched.
* Reserve seats
	1. make seat reservation on a flight by specifying the flight identifier and the number of seats to reserve
	2. if succeed - return an acknowledgement to the client and the seat availability updated
	3. if failed - return a proper error message
* Monitor updates
	1. Register: using **flight identifier** and **monitor interval**
	2. During the interval, the server informs all registered clients by **callback** every time the seats availability updates.
	3. After the interval, the monitor would be removed
	4. One client can only monitor one flight at the same time - other monitor requests will be blocked 
## Data Format
Flight

| Para_name                   | Format                  |
| --------------------------- | ----------------------- |
| flight identifier(main key) | integer                 |
| source place                | variable-length strings |
| destination place           | variable-length strings |
| the departure time          | TBD                     |
| the airfare                 | float                   |
| the seat availability       | integer                 |

