from flask import Flask, render_template, request, redirect, url_for
import config
import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, and_, update
import sqlalchemy
from flask import jsonify
from models import User, Bank, Department, Stuff, Customer, Account, Record, Loan, DepartmentManagerView
from decimal import Decimal
import os

app = Flask(__name__)
app.config.from_object(config)
db = SQLAlchemy(app)

filters = []
authorized = False
cur_ID = ''
accounts = None


def department_manager_view(departments):
    department_manager = []
    for department in departments:
        manager = db.session.query(Stuff).filter_by(
            Department_ID=department.Department_ID, work='经理').first()
        department_manager.append(DepartmentManagerView(department, manager))
    return department_manager


def generate_next_record_id():
    last_record = db.session.query(Record).order_by(
        Record.Record_ID.desc()).first()
    if last_record:
        return 'R' + str(int(last_record.Record_ID[1:]) + 1).zfill(
            3)  # R+自增的三位数
    else:
        return 'R001'


@app.route('/', methods=['GET', 'POST'])
def start():
    global cur_ID
    cur_ID = 'C001'
    return render_template('index.html', authorized=authorized, cur_ID=cur_ID)


@app.route('/login', methods=['GET', 'POST'])
def login():
    global authorized
    global cur_ID
    if request.method == 'GET':
        return render_template('login.html', authorized=authorized)
    else:
        if request.form.get('type') == 'signup':
            try:
                with db.session.begin():
                    ID = request.form.get('ID')
                    key = request.form.get('password')
                    confirm = request.form.get('password2')
                    name = request.form.get('name')
                    phone = request.form.get('phone')
                    city = request.form.get('city')
                    if not ID:
                        return jsonify({
                            'success': False,
                            'error_message': '用户名不能为空'
                        })
                    UserNotExist = db.session.query(User).filter_by(
                        username=ID).scalar() is None
                    if not UserNotExist:
                        return jsonify({
                            'success': False,
                            'error_message': '用户名已存在'
                        })
                    if key != confirm:
                        return jsonify({
                            'success': False,
                            'error_message': '两次密码不一致'
                        })
                    newUser = User(
                        username=ID,
                        password=key,
                    )
                    db.session.add(newUser)
                    newCustomer = Customer(Customer_ID=ID, name=name)
                    if phone:
                        newCustomer.phone = phone
                    if city:
                        newCustomer.address = city
                    db.session.add(newCustomer)
                    db.session.commit()
                    return jsonify({'success': True})
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'error_message': str(e)})
        elif request.form.get('type') == 'login':

            name = request.form.get('name')
            key = request.form.get('password')
            UserNotExist = db.session.query(User).filter_by(
                username=name).scalar() is None

            if UserNotExist == 1:
                error_title = '登录错误'
                error_message = '用户名不存在'
                return render_template('404.html',
                                       error_title=error_title,
                                       error_message=error_message)

            user_result = db.session.query(User).filter_by(
                username=name).first()
            if user_result.password == key:
                if name == 'admin':
                    authorized = True
                    cur_ID = name
                else:
                    authorized = False
                    cur_ID = name
                return render_template('index.html', authorized=authorized)
            else:
                error_title = '登录错误'
                error_message = '密码错误'
                return render_template('404.html',
                                       error_title=error_title,
                                       error_message=error_message)
    return render_template('login.html', authorized=authorized)


@app.route('/index')
def index():
    return render_template('index.html', authorized=authorized)


# 支行管理
@app.route('/bank', methods=['GET', 'POST'])
def bank():
    labels = ['支行号', '支行名', '城市', '电话', '开放时间', '关闭时间']

    if request.method == 'GET':
        result_query = db.session.query(Bank)
        result = result_query.all()
        return render_template('bank.html',
                               labels=labels,
                               content=result,
                               authorized=authorized)
    else:
        if request.form.get('type') == 'query':
            bank_id = request.form.get('id')
            bank_name = request.form.get('name')
            bank_city = request.form.get('city')

            # 构建查询条件
            global filters
            filters = []
            if bank_id:
                filters.append(Bank.Bank_ID == bank_id)
            if bank_name:
                filters.append(Bank.name == bank_name)
            if bank_city:
                filters.append(Bank.city.like(f'%{bank_city}%'))
            result_query = db.session.query(Bank)
            # 应用查询条件
            if filters:
                result_query = result_query.filter(and_(*filters))
            result = result_query.all()

            return render_template('bank.html',
                                   labels=labels,
                                   content=result,
                                   authorized=authorized)

        elif request.form.get('type') == 'update':
            try:
                with db.session.begin():
                    old_id = request.form.get('key')
                    bank_name = request.form.get('bank_name')
                    bank_city = request.form.get('bank_city')
                    bank_phone = request.form.get('bank_phone')
                    bank_open_time = request.form.get('bank_open_time')
                    bank_close_time = request.form.get('bank_close_time')
                    # 创建一个更新语句
                    update_stmt = (update(Bank).where(
                        Bank.Bank_ID == old_id).values(
                            name=bank_name,
                            city=bank_city,
                            phone=bank_phone,
                            open_time=bank_open_time,
                            close_time=bank_close_time))

                    # 执行更新操作
                    db.session.execute(update_stmt)
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                return render_template('404.html',
                                       error_title='支行信息更新错误',
                                       error_message=str(e._message()))
        elif request.form.get('type') == 'delete':
            try:
                with db.session.begin():
                    bank_id = request.form.get('key')
                    # 检查银行是否存在关联的账户
                    if db.session.query(Account).filter(
                            Account.Bank_ID == bank_id, Account.Balance
                            != 0).first() is not None:
                        error_title = '删除错误'
                        error_message = '支行存在关联账户'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)

                    # 检查银行是否存在未还清的贷款
                    if db.session.query(Loan).filter(
                            Loan.Bank_ID == bank_id,
                            Loan.status == 0).first() is not None:
                        error_title = '删除错误'
                        error_message = '支行存在未还清的贷款'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)

                    # 如果通过了所有检查，执行删除操作
                    # 先删除银行下的账户
                    account_result = db.session.query(Account).filter_by(
                        Bank_ID=bank_id).all()
                    for account in account_result:
                        db.session.delete(account)
                    # 再删除银行下的贷款
                    loan_result = db.session.query(Loan).filter_by(
                        Bank_ID=bank_id).all()
                    for loan in loan_result:
                        db.session.delete(loan)
                    # 查询银行下的部门
                    departments = db.session.query(Department).filter_by(
                        Bank_ID=bank_id).subquery()
                    # 删除部门下的员工
                    db.session.query(Stuff).filter(
                        Stuff.Department_ID.in_(departments)).delete()
                    # 删除部门
                    db.session.query(Department).filter_by(
                        Bank_ID=bank_id).delete()
                    # 最后删除银行
                    bank_result = db.session.query(Bank).filter_by(
                        Bank_ID=bank_id).first()
                    db.session.delete(bank_result)
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                return render_template('404.html',
                                       error_title='支行信息删除错误',
                                       error_message=str(e._message()))
        elif request.form.get('type') == 'insert':
            try:
                with db.session.begin():
                    bank_id = request.form.get('id')
                    bank_name = request.form.get('name')
                    bank_city = request.form.get('address')
                    bank_phone = request.form.get('phone')
                    bank_open_time = request.form.get('open_time')
                    bank_close_time = request.form.get('close_time')

                    # 检查每个属性是否存在，如果存在则设置相应的值，否则设置为 None
                    new_bank = Bank()
                    if bank_id:
                        new_bank.Bank_ID = bank_id
                    if bank_name:
                        new_bank.name = bank_name
                    if bank_city:
                        new_bank.city = bank_city
                    if bank_phone:
                        new_bank.phone = bank_phone
                    if bank_open_time:
                        new_bank.open_time = bank_open_time
                    if bank_close_time:
                        new_bank.close_time = bank_close_time
                    if db.session.query(Bank).filter_by(
                            Bank_ID=bank_id).first():
                        error_title = '插入错误'
                        error_message = '支行编号重复'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    db.session.add(new_bank)
                    db.session.commit()
                    filters = []
            except Exception as e:
                db.session.rollback()
                return render_template('404.html',
                                       error_title='支行信息插入错误',
                                       error_message=str(e._message()))
    result_query = db.session.query(Bank)
    if filters:
        result_query = result_query.filter(and_(*filters))
    result = result_query.all()
    return render_template('bank.html',
                           labels=labels,
                           content=result,
                           authorized=authorized)


# 部门管理
@app.route('/department', methods=['GET', 'POST'])
def department():
    labels = ['部门号', '名称', '支行编号', '电话', '经理ID', '经理姓名', '照片']
    global filters
    if request.method == 'GET':
        filters = []
        # 查询部门信息并显示
        departments = db.session.query(Department).all()
        department_manager = department_manager_view(departments)
        return render_template('department.html',
                               labels=labels,
                               content=department_manager)

    elif request.method == 'POST':
        form_type = request.form.get('type')

        if form_type == 'query':
            # 获取查询条件
            department_id = request.form.get('id')
            department_name = request.form.get('name')
            bank_id = request.form.get('bank_id')

            # 构建查询条件
            filters = []
            if department_id:
                filters.append(Department.Department_ID == department_id)
            if department_name:
                filters.append(Department.name == department_name)
            if bank_id:
                filters.append(Department.Bank_ID == bank_id)

            # 应用查询条件
            if filters:
                departments = db.session.query(Department).filter(
                    and_(*filters)).all()
            else:
                departments = db.session.query(Department).all()

            department_manager = department_manager_view(departments)
            return render_template('department.html',
                                   labels=labels,
                                   content=department_manager)

        elif form_type == 'insert':
            try:
                with db.session.begin():
                    # 获取插入数据
                    department_id = request.form.get('depart_id')
                    department_name = request.form.get('depart_name')
                    bank_id = request.form.get('bank_id')
                    phone = request.form.get('phone')
                    # 检查每个属性是否存在，如果存在则设置相应的值，否则设置为 None
                    new_department = Department()
                    if department_id:
                        new_department.Department_ID = department_id
                    if department_name:
                        new_department.name = department_name
                    if bank_id:
                        new_department.Bank_ID = bank_id
                    if phone:
                        new_department.phone = phone
                    if db.session.query(Department).filter_by(
                            Department_ID=department_id).first():
                        error_title = '部门插入错误'
                        error_message = '部门编号重复'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    BankNotExist = db.session.query(Bank).filter_by(
                        Bank_ID=bank_id).scalar() is None
                    if (bank_id and BankNotExist):
                        error_title = '部门插入错误'
                        error_message = '银行不存在'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    db.session.query(Department)
                    db.session.add(new_department)
                    db.session.commit()
                    filters = []
                    return redirect(url_for('department'))
            except Exception as e:
                db.session.rollback()
                return render_template('404.html',
                                       error_title='部门信息插入错误',
                                       error_message=str(e._message()))
        elif form_type == 'delete':
            try:
                with db.session.begin():
                    department_id = request.form.get('key')
                    # 先删除部门下的员工
                    stuff_result = db.session.query(Stuff).filter_by(
                        Department_ID=department_id).all()
                    for stuff in stuff_result:
                        db.session.delete(stuff)
                    # 再删除部门
                    department_result = db.session.query(Department).filter_by(
                        Department_ID=department_id).first()
                    db.session.delete(department_result)
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                return render_template('404.html',
                                       error_title='部门信息删除错误',
                                       error_message=str(e._message()))
        elif request.form.get('type') == 'update':
            try:
                with db.session.begin():
                    old_id = request.form.get('Department_ID')
                    department_name = request.form.get('name')
                    bank_id = request.form.get('Bank_ID')
                    phone = request.form.get('phone')
                    stuff_id = request.form.get('stuff_id')
                    BankNotExist = db.session.query(Bank).filter_by(
                        Bank_ID=bank_id).scalar() is None
                    if (BankNotExist and bank_id):
                        error_title = '部门信息修改错误'
                        error_message = '银行不存在'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    StuffNotExist = db.session.query(Stuff).filter_by(
                        Stuff_ID=stuff_id).scalar() is None
                    if StuffNotExist and stuff_id:
                        error_title = '任命经理错误'
                        error_message = '没有该员工'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    # 创建一个更新部门信息
                    update_stmt = (update(Department).where(
                        Department.Department_ID == old_id).values(
                            name=department_name, Bank_ID=bank_id,
                            phone=phone))
                    db.session.execute(update_stmt)
                    # 把曾经的经理降级为员工
                    old_manager = db.session.query(Stuff).filter_by(
                        Department_ID=old_id, work='经理').first()
                    if old_manager:
                        old_manager_id = old_manager.Stuff_ID
                        update_stmt = (update(Stuff).where(
                            Stuff.Stuff_ID == old_manager_id).values(
                                work='员工'))
                        db.session.execute(update_stmt)
                    # 任命新的经理
                    update_stmt = (update(Stuff).where(
                        Stuff.Stuff_ID == stuff_id).values(
                            Department_ID=old_id, work='经理'))
                    db.session.execute(update_stmt)
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                return render_template('404.html',
                                       error_title='部门信息修改错误',
                                       error_message=str(e._message()))
        result_query = db.session.query(Department)
        if filters:
            result_query = result_query.filter(and_(*filters))
        departments = result_query.all()
        department_manager = department_manager_view(departments)
        return render_template('department.html',
                               labels=labels,
                               content=department_manager)


# 员工管理
@app.route('/stuff', methods=['GET', 'POST'])
def stuff():
    labels = ['员工ID', '姓名', '部门编号', '职位', '联系电话', '居住城市', '照片']
    global filters
    filters = []
    if request.method == 'GET':
        filters = []
        # 查询员工信息并显示
        result = db.session.query(Stuff).all()
        return render_template('stuff.html', labels=labels, content=result)

    elif request.method == 'POST':
        form_type = request.form.get('type')
        if form_type == 'query':
            # 获取查询条件
            stuff_id = request.form.get('id')
            name = request.form.get('name')
            department_id = request.form.get('department_id')
            work = request.form.get('work')
            # 构建查询条件
            filters = []
            if stuff_id:
                filters.append(Stuff.Stuff_ID == stuff_id)
            if name:
                filters.append(Stuff.name == name)
            if department_id:
                filters.append(Stuff.Department_ID == department_id)
            if work:
                filters.append(Stuff.work == work)
            # 应用查询条件
            if filters:
                result = db.session.query(Stuff).filter(and_(*filters)).all()
            else:
                result = db.session.query(Stuff).all()

            return render_template('stuff.html', labels=labels, content=result)

        elif form_type == 'insert':
            try:
                with db.session.begin():
                    # 获取插入数据
                    stuff_id = request.form.get('stuff_id')
                    name = request.form.get('name')
                    department_id = request.form.get('department_id')
                    phone = request.form.get('phone')
                    address = request.form.get('address')
                    # 检查每个属性是否存在，如果存在则设置相应的值，否则设置为 None
                    new_stuff = Stuff()
                    if stuff_id:
                        new_stuff.Stuff_ID = stuff_id
                    if name:
                        new_stuff.name = name
                    if department_id:
                        new_stuff.Department_ID = department_id
                    if phone:
                        new_stuff.phone = phone
                    if address:
                        new_stuff.address = address
                    if os.path.exists('Database/lab2/src/static/photo/' +
                                      name + '.jpg'):
                        new_stuff.figure = name + '.jpg'
                    if db.session.query(Stuff).filter_by(
                            Stuff_ID=stuff_id).scalar():
                        error_title = '员工信息插入错误'
                        error_message = '员工编号重复'
                        return render_template('404.html',
                                               title=error_title,
                                               message=error_message)
                    DepartmentNotExist = db.session.query(
                        Department).filter_by(
                            Department_ID=department_id).scalar() is None
                    if DepartmentNotExist and department_id:
                        error_title = '员工信息插入错误'
                        error_message = '没有该部门'
                        return render_template('404.html',
                                               title=error_title,
                                               message=error_message)
                    # 添加到数据库并提交
                    db.session.query(Stuff)
                    db.session.add(new_stuff)
                    db.session.commit()
                    filters = []
                    return redirect(url_for('stuff'))
            except Exception as e:
                db.session.rollback()
                return render_template('404.html',
                                       error_title='员工信息插入错误',
                                       error_message=str(e._message()))
        elif form_type == 'delete':
            try:
                with db.session.begin():
                    stuff_id = request.form.get('key')
                    result = db.session.query(Stuff).filter_by(
                        Stuff_ID=stuff_id).first()
                    db.session.delete(result)
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                return render_template('404.html',
                                       error_title='员工信息删除错误',
                                       error_message=str(e._message()))
        elif request.form.get('type') == 'update':
            try:
                with db.session.begin():
                    old_id = request.form.get('stuff_id')
                    name = request.form.get('name')
                    department_id = request.form.get('department_id')
                    phone = request.form.get('phone')
                    DepartmentNotExist = db.session.query(
                        Department).filter_by(
                            Department_ID=department_id).scalar() is None
                    if DepartmentNotExist:
                        error_title = '员工信息更新错误'
                        error_message = '没有该部门'
                        return render_template('404.html',
                                               title=error_title,
                                               message=error_message)
                    update_stmt = (update(Stuff).where(
                        Stuff.Stuff_ID == old_id).values(
                            name=name,
                            Department_ID=department_id,
                            phone=phone))
                    db.session.execute(update_stmt)
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                return render_template('404.html',
                                       error_title='员工信息更新错误',
                                       error_message=str(e._message()))
        result_query = db.session.query(Stuff)
        if filters:
            result_query = result_query.filter(and_(*filters))
        result = result_query.all()
        return render_template('stuff.html', labels=labels, content=result)


@app.route('/client', methods=['GET', 'POST'])
def client():
    labels = ['客户ID', '姓名', '联系电话', '地址']
    global filters
    if request.method == 'GET':
        filters = []
        if authorized:
            result = db.session.query(Customer).all()
        else:
            result = db.session.query(Customer).filter_by(Customer_ID=cur_ID)
        return render_template('client.html',
                               labels=labels,
                               content=result,
                               authorized=authorized,
                               cur_ID=cur_ID)
    elif request.method == 'POST':
        form_type = request.form.get('type')
        if form_type == 'query':
            # 获取查询条件
            customer_id = request.form.get('id')
            name = request.form.get('name')
            phone = request.form.get('phone')
            address = request.form.get('address')
            # 构建查询条件
            filters = []
            if customer_id:
                filters.append(Customer.Customer_ID == customer_id)
            if name:
                filters.append(Customer.name == name)
            if phone:
                filters.append(Customer.phone == phone)
            if address:
                filters.append(Customer.address == address)
            # 应用查询条件
            if filters:
                result = db.session.query(Customer).filter(
                    and_(*filters)).all()
            else:
                result = db.session.query(Customer).all()
            return render_template('client.html',
                                   labels=labels,
                                   content=result,
                                   cur_ID=cur_ID,
                                   authorized=authorized)
        elif form_type == 'insert':
            try:
                with db.session.begin():
                    customer_id = request.form.get('customer_id')
                    name = request.form.get('name')
                    phone = request.form.get('phone')
                    address = request.form.get('address')
                    if not db.session.query(Customer).filter_by(
                            Customer_ID=customer_id).first():
                        new_customer = Customer()
                        if customer_id:
                            new_customer.Customer_ID = customer_id
                        if name:
                            new_customer.name = name
                        if phone:
                            new_customer.phone = phone
                        if address:
                            new_customer.address = address
                        db.session.add(new_customer)
                        # 同时创建登录账户
                        new_user = User(username=customer_id,
                                        password=customer_id)
                        db.add(new_user)
                        db.session.commit()
                        filters = []
                    else:
                        error_title = '客户信息插入错误'
                        error_message = '客户ID重复'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
            except Exception as e:
                db.session.rollback()
                return render_template('404.html',
                                       error_title='客户信息插入错误',
                                       error_message=str(e._message()))
        elif form_type == 'delete':
            try:
                with db.session.begin():
                    customer_id = request.form.get('key')
                    # 检查名下账户是否有余额
                    if db.session.query(Account).filter(
                            Account.Customer_ID == customer_id, Account.Balance
                            != 0).first():
                        error_title = '客户信息删除错误'
                        error_message = '客户名下账户有余额'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    # 检查名下贷款是否有未还贷款
                    if db.session.query(Loan).filter(
                            Loan.Customer_ID == customer_id,
                            Loan.status == 0).first():
                        error_title = '客户信息删除错误'
                        error_message = '客户名下贷款有未还完的贷款'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    # 删除客户
                    # 先删除名下的账户
                    account_result = db.session.query(Account).filter_by(
                        Customer_ID=customer_id).all()
                    for account in account_result:
                        db.session.delete(account)
                    # 再删除名下贷款
                    loan_result = db.session.query(Loan).filter_by(
                        Customer_ID=customer_id).all()
                    for loan in loan_result:
                        db.session.delete(loan)
                    # 最后删除客户
                    result = db.session.query(Customer).filter_by(
                        Customer_ID=customer_id).first()
                    db.session.delete(result)
                    # 还要删除登录账号
                    result = db.session.query(User).filter_by(
                        username=customer_id).first()
                    db.session.delete(result)
                    db.session.commit()
                    if not authorized:
                        return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                return render_template('404.html',
                                       error_title='客户信息删除错误',
                                       error_message=str(e._message()))
        elif form_type == 'update':
            try:
                with db.session.begin():
                    old_id = request.form.get('key')
                    name = request.form.get('name')
                    phone = request.form.get('phone')
                    address = request.form.get('address')
                    # 创建更新语句
                    update_stmt = update(Customer).where(
                        Customer.Customer_ID == old_id).values(name=name,
                                                               phone=phone,
                                                               address=address)
                    db.session.execute(update_stmt)
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                return render_template('404.html',
                                       error_title='客户信息更新错误',
                                       error_message=str(e._message()))
        if authorized:
            result_query = db.session.query(Customer)
            if filters:
                result_query = result_query.filter(and_(*filters))
            result = result_query.all()
        else:
            result = db.session.query(Customer).filter_by(Customer_ID=cur_ID)
        return render_template('client.html',
                               labels=labels,
                               content=result,
                               authorized=authorized,
                               cur_ID=cur_ID)


@app.route('/account', methods=['GET', 'POST'])
def account():
    labels = ['账户ID', '客户ID', '银行ID', '开户时间', '余额']
    global filters
    if request.method == 'GET':
        filters = []
        if authorized:
            result = db.session.query(Account).all()
        else:
            result = db.session.query(Account).filter_by(Customer_ID=cur_ID)
        return render_template('account.html',
                               labels=labels,
                               content=result,
                               cur_ID=cur_ID,
                               authorized=authorized)
    elif request.method == 'POST':
        form_type = request.form.get('type')
        if form_type == 'query':
            filters = []
            account_id = request.form.get('account_id')
            if authorized:
                customer_id = request.form.get('customer_id')
            else:
                customer_id = cur_ID
            bank_id = request.form.get('bank_id')
            if account_id:
                filters.append(Account.Account_ID == account_id)
            if customer_id:
                filters.append(Account.Customer_ID == customer_id)
            if bank_id:
                filters.append(Account.Bank_ID == bank_id)
            # 应用查询条件
            if filters:
                result = db.session.query(Account).filter(and_(*filters)).all()
            else:
                result = db.session.query(Account).all()
            return render_template('account.html',
                                   labels=labels,
                                   content=result,
                                   authorized=authorized,
                                   cur_ID=cur_ID)
        elif form_type == 'insert':
            try:
                with db.session.begin():
                    account_id = request.form.get('account_id')
                    if authorized:
                        customer_id = request.form.get('customer_id')
                    else:
                        customer_id = cur_ID
                    bank_id = request.form.get('bank_id')
                    if db.session.query(Account).filter_by(
                            Account_ID=account_id).first():
                        error_title = '账户信息插入错误'
                        error_message = '账户ID重复'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    if not db.session.query(Customer).filter_by(
                            Customer_ID=customer_id).first():
                        error_title = '账户信息插入错误'
                        error_message = '客户ID不存在'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    if not db.session.query(Bank).filter_by(
                            Bank_ID=bank_id).first():
                        error_title = '账户信息插入错误'
                        error_message = '银行ID不存在'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    new_account = Account(Account_ID=account_id,
                                          Customer_ID=customer_id,
                                          Bank_ID=bank_id,
                                          create_time=datetime.date.today(),
                                          Balance=0)
                    db.session.add(new_account)
                    db.session.commit()
                    filters = []
            except Exception as e:
                db.session.rollback()
                return render_template('404.html',
                                       error_title='账户信息插入错误',
                                       error_message=str(e._message()))
        elif form_type == 'delete':
            try:
                with db.session.begin():
                    account_id = request.form.get('key')
                    # 检查账户是否还有余额
                    account = db.session.query(Account).filter_by(
                        Account_ID=account_id).first()
                    if account.Balance != 0:
                        error_title = '账户信息删除错误'
                        error_message = '账户余额不为0'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    db.session.delete(account)
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                return render_template('404.html',
                                       error_title='账户信息删除错误',
                                       error_message=str(e._message()))
        if authorized:
            result_query = db.session.query(Account)
            if filters:
                result_query = result_query.filter(and_(*filters))
            result = result_query.all()
        else:
            result = db.session.query(Account).filter_by(Customer_ID=cur_ID)
        return render_template('account.html',
                               labels=labels,
                               content=result,
                               authorized=authorized,
                               cur_ID=cur_ID)


@app.route('/debt', methods=['GET', 'POST'])
def debt():
    labels = ['贷款ID', '客户ID', '银行ID', '未还贷款金额', '贷款期限', '贷款状态']
    global filters
    if request.method == 'GET':
        filters = []
        if authorized:
            result = db.session.query(Loan).all()
        else:
            result = db.session.query(Loan).filter_by(Customer_ID=cur_ID)
        return render_template('debt.html',
                               labels=labels,
                               content=result,
                               cur_ID=cur_ID,
                               authorized=authorized)
    elif request.method == 'POST':
        form_type = request.form.get('type')
        if form_type == 'query':
            filters = []
            loan_id = request.form.get('loan_id')
            if authorized:
                customer_id = request.form.get('customer_id')
            else:
                customer_id = cur_ID
            bank_id = request.form.get('bank_id')
            status = request.form.get('status')
            if status:
                if status == '是':
                    status = 1
                else:
                    status = 0
                filters.append(Loan.status == status)
            if loan_id:
                filters.append(Loan.Loan_ID == loan_id)
            if customer_id:
                filters.append(Loan.Customer_ID == customer_id)
            if bank_id:
                filters.append(Loan.Bank_ID == bank_id)
            # 应用查询条件
            if filters:
                result = db.session.query(Loan).filter(and_(*filters)).all()
            else:
                result = db.session.query(Loan).all()
            return render_template('debt.html',
                                   labels=labels,
                                   content=result,
                                   authorized=authorized,
                                   cur_ID=cur_ID)
        elif form_type == 'insert':
            try:
                with db.session.begin():
                    loan_id = request.form.get('loan_id')
                    if authorized:
                        customer_id = request.form.get('customer_id')
                    else:
                        customer_id = cur_ID
                    bank_id = request.form.get('bank_id')
                    loan_amount = request.form.get('loan_amount')
                    term = request.form.get('term')
                    if db.session.query(Loan).filter_by(
                            Loan_ID=loan_id).first():
                        error_title = '贷款信息插入错误'
                        error_message = '贷款ID重复'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    if not db.session.query(Customer).filter_by(
                            Customer_ID=customer_id).first():
                        error_title = '贷款信息插入错误'
                        error_message = '客户ID不存在'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    if not db.session.query(Bank).filter_by(
                            Bank_ID=bank_id).first():
                        error_title = '贷款信息插入错误'
                        error_message = '银行ID不存在'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    if Decimal(loan_amount) <= 0:
                        error_title = '贷款信息插入错误'
                        error_message = '贷款金额必须大于0'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    if datetime.datetime.strptime(term, "%Y-%m-%d").date(
                    ) <= datetime.datetime.now().date():
                        error_title = '贷款信息插入错误'
                        error_message = '贷款期限必须大于当前日期'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    new_loan = Loan(Loan_ID=loan_id,
                                    Customer_ID=customer_id,
                                    Bank_ID=bank_id,
                                    RemainingAmount=loan_amount,
                                    term=term,
                                    status=0)
                    db.session.add(new_loan)
                    db.session.commit()
                    filters = []
            except Exception as e:
                error_title = '贷款信息插入错误'
                error_message = str(e)
                return render_template('404.html',
                                       error_title=error_title,
                                       error_message=error_message)
        elif form_type == 'delete':
            try:
                with db.session.begin():
                    loan_id = request.form.get('key')
                    # 检查贷款是否还完
                    loan = db.session.query(Loan).filter_by(
                        Loan_ID=loan_id).first()
                    if loan.status == 0:
                        error_title = '贷款信息删除错误'
                        error_message = '贷款未还完'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    db.session.delete(loan)
                    db.session.commit()
            except Exception as e:
                error_title = '贷款信息删除错误'
                error_message = str(e)
                return render_template('404.html',
                                       error_title=error_title,
                                       error_message=error_message)
        elif form_type == 'update':
            try:
                with db.session.begin():
                    loan_id = request.form.get('loan_id')
                    amount = request.form.get('amount')
                    loan = db.session.query(Loan).filter_by(
                        Loan_ID=loan_id).first()
                    if Decimal(amount) <= 0:
                        error_title = '还贷错误'
                        error_message = '还款金额必须大于0'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    if Decimal(amount) > loan.RemainingAmount:
                        error_title = '还贷错误'
                        error_message = '还款金额不能大于剩余未还金额'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    db.session.query(Loan).filter_by(Loan_ID=loan_id).update({
                        'RemainingAmount':
                        loan.RemainingAmount - Decimal(amount)
                    })
                    loan = db.session.query(Loan).filter_by(
                        Loan_ID=loan_id).first()
                    if loan.RemainingAmount == 0:
                        db.session.query(Loan).filter_by(
                            Loan_ID=loan_id).update({'status': 1})
                    db.session.commit()
            except Exception as e:
                error_title = '还贷错误'
                error_message = str(e)
                return render_template('404.html',
                                       error_title=error_title,
                                       error_message=error_message)
        if authorized:
            result_query = db.session.query(Loan)
            if filters:
                result_query = result_query.filter(and_(*filters))
            result = result_query.all()
        else:
            result = db.session.query(Loan).filter_by(Customer_ID=cur_ID)
        return render_template('debt.html',
                               labels=labels,
                               content=result,
                               authorized=authorized,
                               cur_ID=cur_ID)


@app.route('/detail', methods=['GET', 'POST'])
def detail():
    global filters
    global accounts
    labels = ['记录ID', '账户ID', '交易时间', '净增值', '交易类型', '交易明细']

    if request.method == 'GET':
        filters = []
        accounts = db.session.query(Account.Account_ID).filter(
            Account.Customer_ID == cur_ID).subquery()
        result = db.session.query(Record).filter(
            Record.Account_ID.in_(accounts)).all()
        return render_template('detail.html', labels=labels, content=result)

    elif request.method == 'POST':
        form_type = request.form.get('type')
        if form_type == 'query':
            filters = []
            filters.append(Record.Account_ID.in_(accounts))
            record_id = request.form.get('record_id')
            account_id = request.form.get('account_id')
            record_type = request.form.get('record_type')

            if record_id:
                filters.append(Record.Record_ID == record_id)
            if account_id:
                AccountExist = db.session.query(Account).filter_by(
                    Account_ID=account_id, Customer_ID=cur_ID).first()
                if not AccountExist:
                    error_title = '账户明细查询错误'
                    error_message = '当前用户名下没有该账户'
                    return render_template('404.html',
                                           error_title=error_title,
                                           error_message=error_message)
                filters.append(Record.Account_ID == account_id)
            if record_type:
                filters.append(Record.type == record_type)

            if filters:
                result = db.session.query(Record).filter(and_(*filters)).all()
            else:
                result = db.session.query(Record).all()

            return render_template('detail.html',
                                   labels=labels,
                                   content=result)

        elif form_type == 'delete':
            try:
                with db.session.begin():
                    record_id = request.form.get('key')
                    record = db.session.query(Record).filter_by(
                        Record_ID=record_id).first()
                    if record:
                        db.session.delete(record)
                        db.session.commit()
            except Exception as e:
                error_title = '账户明细删除错误'
                error_message = str(e)
                return render_template('404.html',
                                       error_title=error_title,
                                       error_message=error_message)
        elif form_type == 'insert':
            account_id = request.form.get('account_id')
            amount = request.form.get('amount')
            target_id = request.form.get('target_id')
            action = request.form.get('action')
            try:
                with db.session.begin():  # 事务开始
                    if not db.session.query(Account).filter_by(
                            Account_ID=account_id, Customer_ID=cur_ID).first():
                        error_title = '业务办理错误'
                        error_message = '当前用户名下没有该账户'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    if Decimal(amount) <= 0:
                        error_title = '业务办理错误'
                        error_message = '金额必须大于0'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    if action == '取款':
                        # 余额不足
                        if db.session.query(Account).filter_by(
                                Account_ID=account_id).first(
                                ).Balance < Decimal(amount):
                            error_title = '取款业务办理错误'
                            error_message = '余额不足'
                            return render_template('404.html',
                                                   error_title=error_title,
                                                   error_message=error_message)
                        # 账户余额减少
                        db.session.query(Account).filter_by(
                            Account_ID=account_id).update(
                                {'Balance': Account.Balance - Decimal(amount)})
                        # 增加账户明细
                        new_record = Record(
                            Record_ID=generate_next_record_id(),
                            Account_ID=account_id,
                            time=datetime.datetime.now(),
                            increasement=-Decimal(amount),
                            type='支出',
                            detail='取款')
                        db.session.add(new_record)
                    elif action == '存款':
                        # 账户余额增加
                        db.session.query(Account).filter_by(
                            Account_ID=account_id).update(
                                {'Balance': Account.Balance + Decimal(amount)})
                        # 增加账户明细
                        new_record = Record(
                            Record_ID=generate_next_record_id(),
                            Account_ID=account_id,
                            time=datetime.datetime.now(),
                            increasement=Decimal(amount),
                            type='收入',
                            detail='存款')
                        db.session.add(new_record)
                    elif action == '转账':
                        # 余额不足
                        if db.session.query(Account).filter_by(
                                Account_ID=account_id).first(
                                ).Balance < Decimal(amount):
                            error_title = '转账业务办理错误'
                            error_message = '余额不足'
                            return render_template('404.html',
                                                   error_title=error_title,
                                                   error_message=error_message)
                        # 没有填写目标账户
                        if not target_id:
                            error_title = '转账业务办理错误'
                            error_message = '没有填写目标账户'
                            return render_template('404.html',
                                                   error_title=error_title,
                                                   error_message=error_message)
                        # 没有目标账户
                        TargetExist = db.session.query(Account).filter_by(
                            Account_ID=target_id).first()
                        if not TargetExist:
                            error_title = '转账业务办理错误'
                            error_message = '没有目标账户'
                            return render_template('404.html',
                                                   error_title=error_title,
                                                   error_message=error_message)
                        # 自己账户余额减少
                        db.session.query(Account).filter_by(
                            Account_ID=account_id).update(
                                {'Balance': Account.Balance - Decimal(amount)})
                        # 目标账户余额增加
                        db.session.query(Account).filter_by(
                            Account_ID=target_id).update(
                                {'Balance': Account.Balance + Decimal(amount)})
                        # 自己的账户增加账户明细
                        new_record = Record(
                            Record_ID=generate_next_record_id(),
                            Account_ID=account_id,
                            time=datetime.datetime.now(),
                            increasement=-Decimal(amount),
                            type='支出',
                            detail=f'向{target_id}转账')
                        db.session.add(new_record)
                        # 目标账户增加账户明细
                        new_target_record = Record(
                            Record_ID=generate_next_record_id(),
                            Account_ID=target_id,
                            time=datetime.datetime.now(),
                            increasement=Decimal(amount),
                            type='收入',
                            detail=f'{account_id}的转账')
                        db.session.add(new_target_record)
                        filters = []
                    else:
                        error_title = '业务办理错误'
                        error_message = '未知业务类型'
                        return render_template('404.html',
                                               error_title=error_title,
                                               error_message=error_message)
                    db.session.commit()
                    return redirect(url_for('detail'))
            except Exception as e:
                db.session.rollback()
                return render_template('404.html',
                                       error_title='业务办理错误',
                                       error_message=str(e._message()))
        result_query = db.session.query(Record)
        if filters:
            result_query = result_query.filter(and_(*filters))
        result = result_query.all()
        return render_template('detail.html', labels=labels, content=result)


@app.route('/404')
def not_found():
    return render_template('404.html',
                           error_title='错误标题',
                           error_message='错误信息')


@app.errorhandler(Exception)
def err_handle(e):
    error_message = ''
    error_title = ''
    print(e)
    if (type(e) == IndexError):
        error_title = '填写错误'
        error_message = '日期格式错误! (yyyy-mm-dd)'
    elif (type(e) == AssertionError):
        error_title = '删除错误'
        error_message = '删除条目仍有依赖！'
    elif (type(e) == sqlalchemy.exc.IntegrityError):
        error_title = '更新/插入错误'
        error_message = str(e._message())
    return render_template('404.html',
                           error_title=error_title,
                           error_message=error_message)


if __name__ == '__main__':
    app.run()
