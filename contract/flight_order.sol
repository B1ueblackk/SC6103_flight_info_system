// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FlightOrder {

    // 定义订单结构体
    struct Order {
        uint orderId;        // 订单号
        address userId;      // 用户ID（以用户的地址表示）
    }

    // 订单映射，用户地址 => 订单列表
    mapping(address => Order[]) private userOrders;

    // 添加订单事件
    event OrderAdded(address indexed userId, uint indexed orderId);

    // 添加订单函数，只有用户自己可以添加订单
    function addOrder(uint _orderId) external {
        Order memory newOrder = Order({
            orderId: _orderId,
            userId: msg.sender  // 使用调用合约的用户的地址作为用户ID
        });

        // 将订单存储到该用户的订单列表中
        userOrders[msg.sender].push(newOrder);

        // 触发订单添加事件
        emit OrderAdded(msg.sender, _orderId);
    }

    // 获取用户自己的订单信息
    function getMyOrders() external view returns (Order[] memory) {
        return userOrders[msg.sender];
    }
}