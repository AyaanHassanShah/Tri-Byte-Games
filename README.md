# 🕹️ Game Store – E-commerce Web App (Database Systems Project)

<p align="center">
  <img src="https://img.shields.io/badge/Frontend-HTML%2FCSS-orange?style=for-the-badge&logo=html5" />
  <img src="https://img.shields.io/badge/Backend-Flask%20(Python)-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/Database-SQL%20Server-lightgrey?style=for-the-badge&logo=microsoftsqlserver" />
  <img src="https://img.shields.io/badge/Status-Completed-brightgreen?style=for-the-badge" />
</p>

---

## 📦 Project Overview

The **Game Store** is a database-driven e-commerce simulation built using **Flask (Python)** for backend logic and **HTML/CSS** for the front end. It models a full online store with:

- 🔐 User authentication & role-based access  
- 🎮 Game browsing & filtering  
- 🛒 Shopping cart & order processing  
- 💳 Payment simulation  
- 🧑‍💼 Admin panel for inventory control  

---

## 🎯 Project Objectives

- 🧠 Apply database normalization, relational schema, and SQL best practices  
- 🔗 Build a complete web app using Flask integrated with SQL Server  
- 🎨 Create an intuitive and responsive UI using HTML & CSS  
- 🔐 Implement secure login, role-based access, and session handling  

---





- 🏠 **Home Page:** Featured games, filters by genre/platform  
- 🎮 **Product Page:** Game details + Add to Cart  
- 🛒 **Cart Page:** Game list, quantity update, remove options  
- 📦 **Order Summary:** Final order view before placing  
- 🔐 **Login/Register Forms:** Validations, clean design  



---


- 🔐 **Sign Up / Login with hashed passwords**  
- 👥 **Role-Based Access:**  
  - Admin → Manage games & orders  
  - Customer → Shop, pay, track orders  
- ✅ **Session Handling:** Using Flask `session` & `login_required`  





- 🛒 Add/remove games from cart, live total  
- 📤 On checkout → create order in DB, trigger inventory update  
- 💳 Simulated payment gateway with confirmation  
- 🔄 Inventory auto-update using DB trigger logic  



---



- 🧰 All modules merged into one seamless Flask app  
- 🧑‍💼 Admin Panel → Add/edit/delete games  
- 🚚 Order Tracking: "Processing", "Shipped", "Delivered"  
- 🧪 Testing: full test suite run, performance load testing  



---

## 🧠 Database Design

- ✅ ERD in Visio with `Users`, `Games`, `Orders`, `Payments`, `Inventory`  
- ✅ Normalization: Up to 3NF  
- ✅ Relationships:  
  - One-to-many: Users → Orders  
  - Many-to-many: Orders ↔ Games  
- ✅ SQL:  
  - Stored Procedures  
  - Views & Joins  
  - Triggers for inventory control  

---

## 🛠️ Tech Stack

| Layer       | Technology          |
|-------------|---------------------|
| Frontend    | HTML5, CSS3         |
| Backend     | Python (Flask)      |
| Database    | Microsoft SQL Server|
| Tools       | VS Code, Postman    |
| Auth        | Flask Sessions |

---


## 📊 Languages Used
<hr>
<p align="center">
  ![Top Langs](https://github-readme-stats.vercel.app/api/top-langs/?username=AyaanHassanShah&repo=Tri-Byte-Games&layout=compact)
</p>

<p align="center">
  🔸 This project primarily uses <strong>Flask (Python)</strong> for backend development and application logic, and <strong>HTML</strong> and <strong>CSS</strong> for frontend design and styling.
</p>



## ✅ Project Status

- ✔️ All core modules complete and tested  
- 🚀 Integrated Flask App hosted locally  
- 🧩 Modular, maintainable, and scalable structure  

---

## 📬 Contact

<p align="center">
  <a href="https://www.linkedin.com/in/syed-ayaan-hassan-shah-4993a532a/" target="_blank">
    <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg" width="40" />
  </a>
  &nbsp;&nbsp;&nbsp;
  <a href="https://github.com/AyaanHassanShah" target="_blank">
    <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/github/github-original.svg" width="40" />
  </a>
</p>

---

> 📝 This project is part of a university course and is intended for educational purposes only.
