# Retail eCommerce Management System (ReMS)

## Overview

Retail eCommerce Management System (ReMS) is a desktop-based eCommerce application developed using Python Tkinter and MySQL. The system simulates the core functionalities of an online retail platform by providing separate interfaces for administrators and customers.

The project focuses on inventory management, order processing, authentication, database integration, and transactional consistency while demonstrating practical software engineering concepts such as relational database design, role-based access control, and secure data handling.

## Features

### Customer Features
* User Registration and Login
* Browse Product Catalog
* Search and Filter Products
* Add Products to Cart
* Checkout and Place Orders
* View Order History

### Admin Features
* Secure Admin Login
* Product Management
* Inventory Tracking
* Order Monitoring
* Customer Management
* Sales Analytics Dashboard
* Low Stock Alerts

### Database Features
* MySQL Relational Database
* Foreign Key Relationships
* Transaction Management
* Inventory Updates During Checkout
* Order Tracking System

## Technology Stack

### Frontend
* Python Tkinter

### Backend Logic
* Python

### Database
* MySQL
* MySQL Connector

### Additional Libraries
* hashlib
* tkinter
* mysql-connector-python
* 
## Database Schema
The system consists of four primary tables:

### Users
Stores customer and administrator information.

### Products
Stores product inventory and details.

### Orders
Stores customer orders.

### Order_Items
Links products with orders and tracks purchased quantities.

Relationship Flow:
Users → Orders → Order_Items → Products

## Project Structure
```text
ReMS/
│
├── rems.py
├── database/
├── assets/
├── screenshots/
└── README.md
```
## Installation

### Clone Repository
```bash
git clone https://github.com/yourusername/Retail-Ecommerce-Management-System.git
```

### Install Dependencies
```bash
pip install mysql-connector-python
```

### Configure MySQL
Create the database using the provided SQL schema.

```sql
CREATE DATABASE ReMS_DB;
```

Run the remaining table creation scripts.
### Launch Application

```bash
python rems.py
```


## Learning Outcomes
This project helped in understanding:
* Relational Database Design
* CRUD Operations
* Inventory Management Systems
* Transaction Handling
* Authentication Systems
* Role-Based Access Control
* Desktop Application Development
* Database Connectivity using Python

## Future Improvements

Planned enhancements include:

* Flask Web Application Version
* Multi-Vendor Marketplace Architecture
* Seller Dashboard
* Product Image Uploads
* Online Deployment
* Payment Gateway Integration
* Advanced Analytics Dashboard
* Responsive Web UI

## Author
Rabi Athul Baswariyya
B.Tech Computer Science and Engineering (AI & ML)

## License
This project is developed for educational and academic purposes.
