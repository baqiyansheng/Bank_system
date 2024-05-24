-- Active: 1712124624809@@127.0.0.1@3306@bank_system
DROP TABLE IF EXISTS login,
bank,
department,
stuff,
customer,
account,
record,
loan;

CREATE Table login (
    username VARCHAR(20) PRIMARY KEY,
    password VARCHAR(20) NOT NULL
);
# 管理员账号
INSERT INTO login (username, password) VALUES ('admin', 'admin');
INSERT INTO login (username, password) VALUES ('C001', '123456');
INSERT INTO login (username, password) VALUES ('C002', '123456');


CREATE TABLE bank (
    Bank_ID VARCHAR(20) PRIMARY KEY,
    name VARCHAR(20) NOT NULL,
    city VARCHAR(20),
    phone VARCHAR(20),
    open_time TIME DEFAULT '09:00:00',
    close_time TIME DEFAULT '17:00:00'
);
INSERT INTO bank (Bank_ID, name, city, phone, open_time, close_time) 
VALUES ('B001', '黄山路支行', '安徽合肥', '1234567890', '08:00:00', '18:00:00');
INSERT INTO bank (Bank_ID, name, city, phone, open_time, close_time) 
VALUES ('B002', '肥西路支行', '安徽合肥', '9876543210', '09:00:00', '17:00:00');

CREATE TABLE department (
    Department_ID VARCHAR(20) PRIMARY KEY,
    name VARCHAR(20) NOT NULL,
    Bank_ID VARCHAR(20) NOT NULL,
    phone VARCHAR(20) ,
    FOREIGN KEY (Bank_ID) REFERENCES bank (Bank_ID)
);
INSERT INTO department (Department_ID, name, Bank_ID, phone) 
VALUES ('D001', '柜员部', 'B001', '1313131313');
INSERT INTO department ( Department_ID, name, Bank_ID, phone )
VALUES ('D002', '接待部', 'B001', '1414141414');
INSERT INTO department (Department_ID, name, Bank_ID, phone) 
VALUES ('D003', '柜员部', 'B002', '1515151515');
INSERT INTO department ( Department_ID, name, Bank_ID, phone )
VALUES ('D004', '接待部', 'B002', '1616161616');

CREATE TABLE stuff (
    Stuff_ID VARCHAR(20) PRIMARY KEY,
    name VARCHAR(20) NOT NULL,
    Department_ID VARCHAR(20) NOT NULL,
    work VARCHAR(20) NOT NULL DEFAULT '员工',
    phone VARCHAR(20),
    address VARCHAR(50),
    figure VARCHAR(50) NOT NULL DEFAULT 'default.jpg',
    FOREIGN KEY (Department_ID) REFERENCES department (Department_ID)
);
INSERT INTO stuff (Stuff_ID, name, Department_ID, work, phone, address, figure) 
VALUES ('S001', '钢铁侠', 'D001', '经理', '13000000000', '浙江杭州', '钢铁侠.jpg');
INSERT INTO stuff (Stuff_ID, name, Department_ID, work, phone, address, figure) 
VALUES ('S002', '美国队长', 'D002', '员工', '13100000000', '上海', '美国队长.jpg');
INSERT INTO stuff (Stuff_ID, name, Department_ID, work, phone, address, figure) 
VALUES ('S003', '浩克', 'D003', '员工', '13200000000', '北京', '浩克.jpg');
INSERT INTO stuff (Stuff_ID, name, Department_ID, work, phone, address, figure) 
VALUES ('S004', ' 死侍', 'D004', '经理', '13300000000', '江苏南京', '死侍.jpg');

CREATE TABLE customer (
    Customer_ID VARCHAR(20) PRIMARY KEY,
    name VARCHAR(20) NOT NULL,
    phone VARCHAR(20),
    address VARCHAR(50)
);
INSERT INTO customer (Customer_ID, name, phone, address) 
VALUES ('C001', '张三', '1300000789', '安徽合肥');
INSERT INTO customer (Customer_ID, name, phone, address) 
VALUES ('C002', '李四', '1310000789', '湖南长沙');

CREATE TABLE account (
    Account_ID VARCHAR(20) PRIMARY KEY,
    Customer_ID VARCHAR(20) NOT NULL,
    Bank_ID VARCHAR(20) NOT NULL,
    create_time DATE NOT NULL,
    Balance DECIMAL(18, 2) DEFAULT 0,
    FOREIGN KEY (Customer_ID) REFERENCES customer (Customer_ID),
    FOREIGN KEY (Bank_ID) REFERENCES bank (Bank_ID)
);

INSERT INTO account (Account_ID, Customer_ID, Bank_ID, create_time, Balance) 
VALUES ('A001', 'C001', 'B001', '2020-01-01', 10000);
INSERT INTO account (Account_ID, Customer_ID, Bank_ID, create_time, Balance) 
VALUES ('A002', 'C001', 'B002', '2021-01-01', 100000);
INSERT INTO account (Account_ID, Customer_ID, Bank_ID, create_time, Balance) 
VALUES ('A003', 'C002', 'B001', '2020-06-01', 5000);
INSERT INTO account (Account_ID, Customer_ID, Bank_ID, create_time, Balance) 
VALUES ('A004', 'C002', 'B002', '2021-11-11', 500);

CREATE TABLE record (
    Record_ID VARCHAR(20) PRIMARY KEY,
    Account_ID VARCHAR(20) NOT NULL,
    time DATE NOT NULL,
    increasement DECIMAL(18, 2) NOT NULL,
    type VARCHAR(20),
    detail VARCHAR(50),
    FOREIGN KEY (Account_ID) REFERENCES account (Account_ID)
);
INSERT INTO record (Record_ID, Account_ID, time, increasement, type, detail) 
VALUES ('R001', 'A001', '2020-01-01', 1000, '收入', '存钱');
INSERT INTO record (Record_ID, Account_ID, time, increasement, type, detail) 
VALUES ('R002', 'A001', '2020-01-02', -500,'支出', '取钱');
INSERT INTO record (Record_ID, Account_ID, time, increasement, type, detail) 
VALUES ('R003', 'A001', '2021-01-03', -500, '支出', '向A002转账');
INSERT INTO record (Record_ID, Account_ID, time, increasement, type, detail) 
VALUES ('R004', 'A001', '2021-01-04', 1000, '收入', 'A002的转账');


CREATE TABLE loan (
    Loan_ID VARCHAR(20) PRIMARY KEY,
    Customer_ID VARCHAR(20) NOT NULL,
    Bank_ID VARCHAR(20) NOT NULL,
    RemainingAmount DECIMAL(18, 2) NOT NULL,
    term DATE NOT NULL,
    status INT NOT NULL DEFAULT 0, # 0表示未还清,1表示已还清
    FOREIGN KEY (Customer_ID) REFERENCES customer (Customer_ID),
    FOREIGN KEY (Bank_ID) REFERENCES bank (Bank_ID)
);
INSERT INTO loan (Loan_ID, Customer_ID, Bank_ID, RemainingAmount, term, status) 
VALUES ('L001', 'C001', 'B001', 10000, '2022-01-01', 1);
INSERT INTO loan (Loan_ID, Customer_ID, Bank_ID, RemainingAmount, term, status)
VALUES ('L002', 'C001', 'B002', 100000, '2023-01-01', 0);