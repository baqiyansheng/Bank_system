from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# 用户管理
class User(db.Model):
    __tablename__ = 'login'

    username = db.Column(db.String(15, 'utf8mb4_0900_ai_ci'), primary_key=True)
    password = db.Column(db.String(50), nullable=False)


# 支行
class Bank(db.Model):
    __tablename__ = 'bank'

    Bank_ID = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    open_time = db.Column(db.Time, default='09:00:00')
    close_time = db.Column(db.Time, default='17:00:00')


# 部门
class Department(db.Model):
    __tablename__ = 'department'

    Department_ID = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    Bank_ID = db.Column(db.String(20),
                        db.ForeignKey('bank.Bank_ID'),
                        nullable=False)
    phone = db.Column(db.String(20))
    bank = db.relationship('Bank', backref=db.backref('departments'))


# 员工
class Stuff(db.Model):
    __tablename__ = 'stuff'

    Stuff_ID = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    Department_ID = db.Column(db.String(20),
                              db.ForeignKey('department.Department_ID'),
                              nullable=False)
    work = db.Column(db.String(20), nullable=False, default='员工')
    phone = db.Column(db.String(20))
    address = db.Column(db.String(50))
    figure = db.Column(db.String(50), nullable=False, default='default.jpg')
    department = db.relationship('Department', backref=db.backref('stuffs'))


# 客户
class Customer(db.Model):
    __tablename__ = 'customer'

    Customer_ID = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(50))


# 账户
class Account(db.Model):
    __tablename__ = 'account'

    Account_ID = db.Column(db.String(20), primary_key=True)
    Customer_ID = db.Column(db.String(20),
                            db.ForeignKey('customer.Customer_ID'),
                            nullable=False)
    Bank_ID = db.Column(db.String(20),
                        db.ForeignKey('bank.Bank_ID'),
                        nullable=False)
    create_time = db.Column(db.Date, nullable=False)
    Balance = db.Column(db.DECIMAL(18, 2), default=0)
    customer = db.relationship('Customer', backref=db.backref('accounts'))
    bank = db.relationship('Bank', backref=db.backref('accounts'))


# 交易记录
class Record(db.Model):
    __tablename__ = 'record'

    Record_ID = db.Column(db.String(20), primary_key=True)
    Account_ID = db.Column(db.String(20),
                           db.ForeignKey('account.Account_ID'),
                           nullable=False)
    time = db.Column(db.Date, nullable=False)
    increasement = db.Column(db.DECIMAL(18, 2), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    detail = db.Column(db.String(50))
    account = db.relationship('Account', backref=db.backref('records'))


# 贷款
class Loan(db.Model):
    __tablename__ = 'loan'

    Loan_ID = db.Column(db.String(20), primary_key=True)
    Customer_ID = db.Column(db.String(20),
                            db.ForeignKey('customer.Customer_ID'),
                            nullable=False)
    Bank_ID = db.Column(db.String(20),
                        db.ForeignKey('bank.Bank_ID'),
                        nullable=False)
    RemainingAmount = db.Column(db.DECIMAL(18, 2), nullable=False)
    term = db.Column(db.Date, nullable=False)
    status = db.Column(db.Integer, nullable=False, default=0)
    customer = db.relationship('Customer', backref=db.backref('loans'))
    bank = db.relationship('Bank', backref=db.backref('loans'))


class DepartmentManagerView:

    def __init__(self, department, stuff):
        self.department_id = department.Department_ID
        self.department_name = department.name
        self.bank_id = department.Bank_ID
        self.phone = department.phone
        if (stuff):
            self.manager_id = stuff.Stuff_ID
            self.manager_name = stuff.name
            self.manager_photo = stuff.figure
        else:
            self.manager_photo = 'default.jpg'
