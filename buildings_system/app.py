#coding=utf-8
import re  # 引入正则表达式对用户输入进行限制
import flask
import pymysql  # 连接数据库
from flask import Flask, render_template, request, send_from_directory
import os
import json
from datafunction import *
from flask import jsonify
from datetime import date,datetime

# 初始化
app = Flask(__name__)
db = pymysql.connect(host='localhost', user='root',
                     password='123456', database='buildings_database')

cursor = db.cursor()
# 存储登陆用户的名字用户其它网页的显示
version = '数字江海'

def sqlCreate(dbname):
    dropsql = "drop table if exists %s;"%(dbname)
    cursor.execute(dropsql)
    db.commit()

    sql_createTb  =  """CREATE TABLE %s (
                 id bigint(20)  not null auto_increment,
                 name  CHAR(20),
                 fn CHAR(20),
                 status CHAR(20),
                 norms INT,
                 factn INT,
                 reserven INT,
                 totaln INT,
                 destination CHAR(20),
                 color CHAR(20),
                 density float, 
                 kg float, 
                 length float, 
                 area float, 
                 mode CHAR(20), 
                 remark CHAR(20), 
                 bn CHAR(20),
                 PRIMARY KEY(id))
                 """%(dbname)

    cursor.execute(sql_createTb)
    db.commit()

def selectAll():
    sql_getall = "select * from total"
    cursor.execute(sql_getall)
    db.commit()
    allarray = list(cursor.fetchall())
    for tup in allarray: #所有数据的元组转为数组
        tup = list(tup)
    return allarray

def selectAllPhyface():
    sql_getall = "select * from phyface"
    cursor.execute(sql_getall)
    db.commit()
    allarray = list(cursor.fetchall())
    return allarray

def insertLogs(op,dbname,sta):
    time = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    insert_sql = "Insert into logs " + "(operation, tbname,date,status) VALUES(%s,%s,%s,%s)"
    cursor.execute(insert_sql,[op,dbname,time,sta]) #执行sql语句
    db.commit()

phyAllay = selectAllPhyface()

def sqlInsertPhyface(phy_array):
    insert_sql = "INSERT INTO phyface"  + \
    "(fn, phy,jeck) VALUES(%s,%s,%s)"
    cursor.execute(insert_sql,phy_array) #执行sql语句
    db.commit()

def sqlInsertAll(dbname,tmp_row,ordern):
     #insert db #因为页面过来的值不存在id 和 料单号,数组短了两位
    if len(tmp_row)==16:
        tmp_row.insert(0,'1')
    print(tmp_row)
    for k in range(len(tmp_row)):
        data = tmp_row[k]
        if type(data) == str:
            tmp_row[k].replace(" ","")
        if k == 2:#检测厂家型材号是否合法
            if not(valueJudge(tmp_row[k])):
                print("Notice: 数据的厂家型材号有问题...")
                continue
        if k in [0,4,5,6,7]:
            tmp_row[k] = int(tmp_row[k])
        if k==9 and tmp_row[k]: #色号转大写
            tmp_row[k] = tmp_row[k].upper()
        if k==10: #线密度
            tmp_row[10] = float(tmp_row[10])
            if type(tmp_row[11]) == str:
                tmp_row[11] = float(tmp_row[11])
            tmp_row[12] = float(tmp_row[12])
            fns = [] #记录所有已有的型材号
            phyAllay = selectAllPhyface()
            for item in phyAllay:
                fns.append(item[1])
            if tmp_row[2] not in fns: #如果没有则insert
                phy_array = [tmp_row[2],tmp_row[10],tmp_row[12]]
                sqlInsertPhyface(phy_array)
            else:    #有则对比
                for item in phyAllay:
                    if item[1] == tmp_row[2]:
                        if item[2] == tmp_row[10] and item[3] == tmp_row[12]:
                            print("线密度和喷涂长度无误--")
                            break
                        else:
                            tmp_row[10] = item[2]
                            tmp_row[12] = item[3]
                            break
        if k == 11:
            tmp_row[k] = eval('%.2f'%tmp_row[k])
            caldata = calculateHeight(tmp_row[4],tmp_row[7],tmp_row[10])
            if caldata!=tmp_row[k]:
                print("输入的重量有问题，以纠正...")
                tmp_row[k] = caldata
            else:
                print("输入的重量无误问题...")
        if k == 14: #粉末喷涂
            tmp_row[k] = infaceDeal(tmp_row[k])
        if k == 16:
            tmp_row[k] = ordern
    print(tmp_row[7],tmp_row[5],tmp_row[6])
    tmp_row[7] = tmp_row[5] + tmp_row[6]

    sql = "INSERT INTO " + dbname + \
    "(name, fn, status, norms, factn, reserven, totaln, destination, color, density, kg, length, area, mode, remark, bn) \
VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    
    cursor.execute(sql,tmp_row[1:]) 
    db.commit()

def sqlUpdate(elem,tmp_row,op,fnid):
    print("所匹配的id是 " + str(fnid))
    if op == 0:
        #数量 出库时备用数量为0，所以实际等于总数，出库时先出备用，备用不够再出总数
        if elem[6]>=tmp_row[7]: #如果备用数量够，直接用备用出，实际数量不变
            update_sql = "UPDATE total set factn = %d,reserven =%d,totaln = %d WHERE id = %s;"%(elem[6]-tmp_row[7],elem[7]-tmp_row[7],fnid)
            update_sql2 = "UPDATE total set kg = %d WHERE fn = '%s';"%(elem[11]-tmp_row[11],tmp_row[2]) #质量
        else: #备用小于需要出的总数
            #先出备用
            first_output = tmp_row[7] - elem[6] #第一次出了备用，剩下first_output从实际上出
            update_sql = "UPDATE total set factn = %d,reserven =%d,totaln = %d WHERE id = %s;"%(elem[5]-first_output,0,elem[7]-tmp_row[7],fnid)
            update_sql2 = "UPDATE total set kg = %d WHERE fn = '%s';"%(elem[11]-tmp_row[11],tmp_row[2]) #质量
        print("匹配成功，将进行数据出库...")
    else:
        update_sql = "UPDATE total set factn = %d,reserven =%d,totaln = %d WHERE id = %s;"%(elem[5]+tmp_row[5],elem[6]+tmp_row[6],elem[7]+tmp_row[7],fnid)
        update_sql2 = "UPDATE total set kg = %d WHERE id = %s;"%(elem[11]+tmp_row[11],fnid)
        print("匹配成功，将进行数据入库...")
    # print(update_sql)
    
    cursor.execute(update_sql)
    cursor.execute(update_sql2) 
    db.commit()

def sqlInsertItem(tmp_row):
    print("未匹配上，将进行数组更新...")
    insert_sql = "INSERT INTO total"  + \
    "(name, fn, status, norms, factn, reserven, totaln, destination, color, density, kg, length, area, mode, remark, bn) \
VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    # print(insert_sql)
    cursor.execute(insert_sql,tmp_row[1:]) #执行sql语句
    db.commit()

def showtables():
    sql_getall = "show tables"
    cursor.execute(sql_getall)
    db.commit()
    allarray = cursor.fetchall()
    arr = [i[0] for i in allarray]
    arr.remove("admins")
    arr.remove("phyface")
    arr.remove("contents")
    arr.remove("logs")
    return arr

@app.route("/", methods=["GET", "POST"])
def login():
    # 增加会话保护机制(未登陆前login的session值为空)
    flask.session['login'] = ''
    if flask.request.method == 'POST':
        user = flask.request.values.get("user", "")
        pwd = flask.request.values.get("pwd", "")
        result_user = re.search(r"^[a-zA-Z]+$", user)  # 限制用户名为全字母
        result_pwd = re.search(r"^[a-zA-Z\d]+$", pwd)  # 限制密码为 字母和数字的组合
        if result_user != None and result_pwd != None:  # 验证通过
            msg = '用户名或密码错误'
            # sql1 = "select * from admins where admin_name='" + \
            #        user + " ' and admin_password='" + pwd + "';"
            # cursor.execute(sql1)
            # result = cursor.fetchone()
            # # 匹配得到结果即管理员数据库中存在此管理员
            if user == 'admin' and pwd == 'admin':
                # 登陆成功
                flask.session['login'] = 'OK'
                return flask.redirect(flask.url_for('informations'))
        else:  # 输入验证不通过
            msg = '非法输入'
    else:
        msg = ''
        user = ''
    return flask.render_template('login.html', msg=msg, user=user)

@app.route('/files/<filename>')
def files(filename):
    return send_from_directory('./file/download/', filename, as_attachment=True)#上传到index.html页面中

@app.route('/indexop',methods=['GET', 'POST'])
def show_index():
    # urrent_path = os.getcwd()
    # print(urrent_path)
    entries = os.listdir('./file/download/')
    print(entries)
    return flask.render_template('makefile.html',entries = entries)#上传到index.html页面中

@app.route('/informations', methods=['GET', 'POST'])
def informations():
    insert_result = ''
    # 当用户登陆有存储信息时显示用户名,否则为空
    user_info = version
    # 获取显示管理员数据信息(GET方法的时候显示数据)
    if flask.request.method == 'GET':
        sql_list = "select * from total"
        cursor.execute(sql_list)
        results = cursor.fetchall()
    if flask.request.method == 'POST':
        # 获取输入的型材信息
        #fn_id = flask.request.values.get("id", "")
        fn_name = flask.request.values.get("name", "")
        fn_fn = flask.request.values.get("fn", "")
        fn_status = flask.request.values.get("status", "")
        fn_norms = flask.request.values.get("norms", "")
        fn_factn = flask.request.values.get("factn", "")
        fn_reserven = flask.request.values.get("reserven", "")
        fn_totaln = flask.request.values.get("totaln", "")
        fn_destination = flask.request.values.get("destination", "")
        fn_color = flask.request.values.get("color", "")
        fn_density = flask.request.values.get("density", "")
        fn_kg = flask.request.values.get("kg", "")
        fn_length = flask.request.values.get("length", "")
        fn_area = flask.request.values.get("area", "")
        fn_mode = flask.request.values.get("mode", "")
        fn_remark = flask.request.values.get("remark", "")
        fn_bn = flask.request.values.get("bn", "")

        insert_result = "暂时关闭该功能"
        if not all([fn_name,fn_fn ,fn_status ,fn_norms ,fn_factn ,fn_reserven ,fn_totaln ,fn_destination ,fn_color ,fn_density ,fn_kg ,fn_length,fn_area,fn_mode,fn_bn]):
            insert_result = "输入的型材信息不能为空"
        else:
            try:
                sql_1 = "INSERT INTO total"  + \
    "(name, fn, status, norms, factn, reserven, totaln, destination, color, density, kg, length, area, mode, remark, bn) \
VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                cursor.execute(sql_1, (fn_name,fn_fn ,fn_status ,fn_norms ,fn_factn ,fn_reserven ,fn_totaln ,fn_destination ,fn_color ,fn_density ,fn_kg ,fn_length,fn_area,fn_mode,fn_remark,fn_bn))
                insert_result = "成功存入一条型材信息"
                print(insert_result)
            except Exception as err:
                print(err)
                insert_result = "型材信息插入失败"
                print(insert_result)
                pass
            db.commit()

        # POST方法时显示数据
        sql_list = "select * from total"
        cursor.execute(sql_list)
        results = cursor.fetchall()

    return flask.render_template('informations.html', insert_result=insert_result, user_info=user_info, results=results)


@app.route('/destiny', methods=['GET', "POST"])
def destiny():
    insert_result = ''
    user_info = version

    # 获取显示管理员数据信息(GET方法的时候显示数据)
    if flask.request.method == 'GET':
        sql_list = "select * from phyface"
        cursor.execute(sql_list)
        results = cursor.fetchall()
    if flask.request.method == 'POST':
        print(request.values.to_dict())
        fn_fn = flask.request.values.get("fn", "")
        fn_phy = flask.request.values.get("phy", "")
        fn_jeck = flask.request.values.get("jeckoff", "")
        # print(fn_fn, fn_phy,fn_jeck)

        try:
            sql_1 = "insert into phyface(fn,phy,jeck)values(%s,%s,%s)"
            cursor.execute(sql_1, (fn_fn, fn_phy,fn_jeck))
            # result = cursor.fetchone()
            insert_result = "成功存入一条信息"
            print(insert_result)
        except Exception as err:
            print(err)
            insert_result = "信息插入失败"
            print(insert_result)
        db.commit()
        # POST方法时显示数据
        sql_list = "select * from phyface"
        cursor.execute(sql_list)
        results = cursor.fetchall()
    return flask.render_template('destiny.html', insert_result=insert_result, user_info=user_info,
                                 results=results)

@app.route('/search', methods=['GET', 'POST'])
def search():
    print(111)
    query_result = ''
    results = ''
    user_info = version
    # 获取下拉框的数据
    if flask.request.method == 'POST':
        query = flask.request.values.get('query')
        queryb = flask.request.values.get('query2')
        # 判断不同输入对数据表进行不同的处理
        print(query,queryb)
        if 1:
            try:
                sql = "select * from total where fn = %s and norms = %s; "
                cursor.execute(sql, [query, queryb])
                results = cursor.fetchall()
                if results:
                    query_result = '查询成功!'
                else:
                    query_result = '查询失败!'
            except Exception as err:
                print(err)
        #if 1:
        
        if 0:  #version1.2的版本注释掉
            select1 = ''
            if select1 == '型材号':
                try:
                    sql = "select * from total where fn = %s; "
                    cursor.execute(sql, query)
                    results = cursor.fetchall()
                    if results:
                        query_result = '查询成功!'
                    else:
                        query_result = '查询失败!'
                except Exception as err:
                    print(err)
            if select1 == 'id':
                try:
                    sql = "select * from total where id = %s; "
                    cursor.execute(sql, query)
                    results = cursor.fetchall()
                    if results:
                        query_result = '查询成功!'
                    else:
                        query_result = '查询失败!'
                except Exception as err:
                    print(err)
            if select1 == '规格':
                try:
                    sql = "select * from total where norms = %s;"
                    cursor.execute(sql, query)
                    results = cursor.fetchall()
                    if results:
                        query_result = '查询成功!'
                    else:
                        query_result = '查询失败!'
                except Exception as err:
                    print(err)
            if select1 == '材质状态':
                try:
                    sql = "select * from total where status = %s;"
                    cursor.execute(sql, query)
                    results = cursor.fetchall()
                    if results:
                        query_result = '查询成功!'
                    else:
                        query_result = '查询失败!'
                except Exception as err:
                    print(err)
    return flask.render_template('search.html', query_result=query_result, user_info=user_info, results=results)

@app.route('/history', methods=['GET', 'POST'])
def historysearch():
    tablesname = showtables() #只有存在数据的表名
    query_result = ''
    results = ''
    user_info = version
    results = []
    # 获取下拉框的数据
    if flask.request.method == 'POST':
        query = flask.request.values.get('query')
        queryb = flask.request.values.get('query2')
        # 判断不同输入对数据表进行不同的处理
        print(query,queryb)
        if 1:
            for tb in tablesname:
                try:
                    sql = "select * from " + tb + " where fn = %s and norms = %s; "
                    cursor.execute(sql, [query, queryb])
                    inner_result = cursor.fetchall()
                    if inner_result:
                        query_result = '查询成功!'
                        results.append([tb.upper(),inner_result])
                    else:
                        query_result = '查询失败!'
                except Exception as err:
                    print(err)
        print(results)
    return flask.render_template('history.html', query_result=query_result, user_info=user_info, results=results)

@app.route('/log4j', methods=['GET', 'POST'])
def blog4j():
    sql_getall = "select * from logs"
    cursor.execute(sql_getall)
    db.commit()
    allarray = cursor.fetchall()
    results = []
    for tup in allarray: #所有数据的元组转为数组
        tup = list(tup)
        if tup[1] == 1:
            tup[1] = "入库"  
        elif tup[1] == 0:
            tup[1] = "出库"
        else:
            tup[1] = "导出料单"
        tup[4] = "成功" if tup[4] == 1 else "失败"
        results.append(tup)
    # print(results)
    return flask.render_template('log4j.html',results = results,user_info=version)

@app.route('/update', methods=['GET', "POST"])
def update():
    insert_result = ''

    if flask.request.method == 'GET':
        sql_list = "select * from total"
        cursor.execute(sql_list)
        results = cursor.fetchall()
    user_info = version

    if flask.request.method == 'POST':
        # 获取输入的型材信息
        fn_id = flask.request.values.get("id", "")
        fn_factn = flask.request.values.get("factn", "")
        fn_reserven = flask.request.values.get("reserven", "")
        
        select = flask.request.form.get('selected_one')
        if select == '修改型材':
            if fn_factn == '':
                fn_factn = 0
            if fn_reserven == '':
                fn_reserven = 0
            fn_reserven = int(fn_reserven)    
            fn_factn = int(fn_factn)
            try:
                sql_list = "select * from total where id=%s;"
                cursor.execute(sql_list,fn_id)
                res = cursor.fetchall()[0]
                old_factn = res[5]
                old_reserven = res[6]
                norms = res[4]
                density = res[10]
                if fn_factn!=0 and fn_reserven!=0:
                    fn_totaln = fn_factn + fn_reserven
                    print(fn_totaln)
                    sql = "update total set factn=%s,reserven = %s,totaln = %s where id=%s;"
                    cursor.execute(sql, (fn_factn,fn_reserven,fn_totaln,fn_id))

                if fn_factn==0 and fn_reserven!=0:
                    fn_totaln = fn_reserven + old_factn
                    print(fn_totaln)
                    sql = "update total set reserven=%s,totaln = %s where id=%s;"
                    cursor.execute(sql, (fn_reserven,fn_totaln,fn_id))

                if fn_factn!=0 and fn_reserven==0:    
                    fn_totaln = fn_factn + old_reserven
                    print(fn_totaln)
                    sql = "update total set factn=%s,totaln = %s where id=%s;"
                    cursor.execute(sql, (fn_factn,fn_totaln,fn_id))

                fn_kg = calculateHeight(norms,fn_totaln,density)
                sql2 = "update total set kg=%s where id=%s;"
                cursor.execute(sql2, (fn_kg,fn_id))
                insert_result = "型材" + fn_id + "的型材修改成功!"
            except Exception as err:
                print(err)
                insert_result = "修改型材失败!"
            db.commit()

        if select == '删除型材':
            try:
                sql_delete = "DELETE FROM total WHERE id= %s;"
                cursor.execute(sql_delete,fn_id)
                insert_result = "成功删除型材" + fn_id
            except Exception as err:
                print(err)
                insert_result = "删除失败"
            db.commit()

        # POST方法时显示数据
        sql_list = "select * from total"
        cursor.execute(sql_list)
        results = cursor.fetchall()
    return flask.render_template('update.html', user_info=user_info, insert_result=insert_result,
                                 results=results)

@app.route('/makefile',methods=['GET', 'POST'])
def show_page():
    data = request.form
    query_result = ''
    f = request.files['file']
    entries = os.listdir('./file/download/')
    print(entries)
    op = int(data["selection"]) #操作码
    print(f)
    if f:# 表示有发送文件
        filename =  f.filename
        path = ''
        if op == 0:
            path = os.path.join('./file/output', filename)
        elif op == 1:
            path = os.path.join('./file/input', filename)
        f.save(path)
        filename = filename.strip()
        dbname = filename[:5]
        sheet_datas,ordern = readxls(filename,op) #一板子读取excel所有sheet的数据
        if op == 0: #chuku
            try:
                dbname = 'out' + dbname
                sqlCreate(dbname)
                allarray = selectAll()

                for i in range(len(sheet_datas)): 
                    tmp_row = sheet_datas[i] 
                    sqlInsertAll(dbname,tmp_row,ordern)
                    flag = 0
                    for elem in allarray:
                        if kernelCheck(elem,tmp_row):
                            fnid = kernelCheck(elem,tmp_row)
                            flag = 1
                            sqlUpdate(elem,tmp_row,op,fnid)
                            break
                    if flag == 0:
                        tmp_row[7] = - tmp_row[7]
                        sqlInsertItem(tmp_row)
                insertLogs(op,dbname,1)
                query_result = '出库成功'
            except Exception as err:
                print("存在错误！")
                print(err)
                insertLogs(op,dbname,0)
                query_result = '出库失败'

        if op == 1: #ruku
            try:
                dbname = 'in' + dbname
                sqlCreate(dbname)
                allarray = selectAll()
                for i in range(len(sheet_datas)): 
                    tmp_row = sheet_datas[i] 
                    sqlInsertAll(dbname,tmp_row,ordern)
                
                    flag = 0
                    for elem in allarray:
                        if kernelCheck(elem,tmp_row):
                            fnid = kernelCheck(elem,tmp_row)
                            flag = 1
                            sqlUpdate(elem,tmp_row,op,fnid)
                            break
                    if flag == 0:
                        sqlInsertItem(tmp_row)
                insertLogs(op,dbname,1)
                query_result = '入库成功'
            except:
                print("存在错误！")
                insertLogs(op,dbname,0)
                query_result = '入库失败'
        return flask.render_template('makefile.html',entries = entries,query_result=query_result)
    if op == 2:
        alldata = selectAll()
        output = []
        ids = []
        for dk in alldata:
            if dk[7]<0:
                ids.append(dk[0])
                output.append(dk)
        print(output,ids)
        if not output:
            print('无需出货')
            query_result = '无需出货'
            return flask.render_template('makefile.html',entries = entries,query_result=query_result)
        try:
            writexls(output)
            insertLogs(op,"料单导出",1)
            query_result = '料单导出成功'
        except:
            print('导出出错!')
            insertLogs(op,"料单导出",0)
            query_result = '料单导出失败'
            return flask.render_template('makefile.html',entries = entries,query_result=query_result)
        
        for id in ids:
            delete_sql = "DELETE FROM total WHERE id = %s"
            cursor.execute(delete_sql, ids)
        db.commit()
        #先写入excel 再数据库删除

    return flask.render_template('makefile.html',entries = entries,query_result=query_result)

@app.route('/assist',methods=['GET', 'POST'])
def helpput():
    query_result = ''
    insert_result = ''
    results = ''
    # 获取下拉框的数据
    if flask.request.method == 'POST':
        # select1 = flask.request.form.get('selected_one')
        # select2 = flask.request.form.get('selected_two')
        query = flask.request.values.get('query')
        queryb = flask.request.values.get('query2')
        # 判断不同输入对数据表进行不同的处理
        # if select1 == '型材号' and select2 == '规格':
        if 1 :
            print(query,queryb)
            try:
                sql = "select * from total where fn = %s and norms = %s; "
                cursor.execute(sql, [query, queryb])
                results = cursor.fetchall()
                if results:
                    query_result = '查询成功!'
                else:
                    query_result = '查询失败!'
            except Exception as err:
                print(err)
        
    return flask.render_template('assist.html',results = results, query_result=query_result,insert_result=insert_result,user_info = version)

@app.route('/heart',methods=['GET', 'POST'])
def heart():
    results = ''
    # 获取下拉框的数据
    if flask.request.method == 'POST':
        jsondata = request.json
        print('recv:', jsondata)
        dbname = "Total"
        try:
            for i in range(len(jsondata)): 
                tmp_row = jsondata[i] 
                tmp_row[-1] = "页面录入"
                tmp_row.append("")
                sqlInsertAll(dbname,tmp_row,"page")
                db.commit()
            insertLogs(1,"页面录入",1)
            return "操作成功"
        except:
            print("存在错误！")
            insertLogs(1,"页面录入",0)
    return "操作失败，输入有误"


app.secret_key = 'biguncle'
try:
    app.run()
except Exception as err:
    print(err)
    db.close()  # 关闭数据库连接
