#coding=utf-8
import xlrd
import xlwt
import xlutils.copy
import os
dict_linearDensity = { #报废
    "ZDN15698":0.555,
    "ZDN15699":0.674,
    "ZDN15696":0.555
} 

realname = ['序号', '型材名称', '厂家型材号', '材质状态', '规格(mm/支)', '实际数量(支)', '备用数量(支)', '总数量(支)', '收货地', '色号', 
'线密度(Kg/m)', '重量(Kg)', '喷涂长度(mm)', '喷涂面积(平方米)', '表面处理方式', '备注', '料单号']
virtual = ['sn', 'name', 'fn', 'status', 'norms', 'factn', 'reserven', 'totaln', 'destination', 'color', 'density', 'kg', 'length', 'area', 'mode', 'remark', 'bn']

row4 = ['序号', '型材名称', '厂家型材号', '材质状态', '规格(mm/支)', '实际数量(支)', '备用数量(支)', '总数量(支)', '收货地', '色号', 
            '线密度(Kg/m)', '重量(Kg)', '喷涂长度(mm)', '喷涂面积(平方米)', '表面处理方式', '备注', '料单号']

def valueJudge(filenum): #判断值的合法行 主要是指厂家型材号
    if check_digit(filenum) and not(contain_chinese(filenum)):
        return True
    return False

def calculateHeight(norms,tn,destiny): #重量 = 规 格*总数量*线密度/1000
    destiny = float(destiny)
    return eval('%.2f'%(norms * tn * destiny/1000))

def kernelNumberCal(): #合并总数量
    #数据库update
    return

def kernelCheck(lista,listb): #判断是否一致
    if len(lista) != len(listb):
        print("Notice：某组数据的长度有误，请注意...")
        return False
    print(lista)
    print(listb)
    for i in range(1,len(lista)):
        if i in [5,6,7,11,10,15,16]: #7-2 实际数量(支), 8 备用数量(支), 9 总数量(支), 13 重量 (Kg),17备注
            continue
        else:
            if lista[i] != listb[i]:
                print("Notice：不同之处在于 %s 和 %s"%(lista[i],listb[i]))
                return False
    print("Notice：是同一组数据！")
    return lista[0]

def infaceDeal(elem):
    if elem == "粉末喷涂":
        elem = "粉沫喷涂"
    if elem == "氟碳喷涂" or elem == "氟碳喷涂(PVDF)": 
        elem = "PVDF"
    return elem

def check_digit(s):
    for char in s:
        if char.isdigit():
            return True
    return False

def contain_chinese(check_str):
    for ch in check_str:
        if '\u4e00' <= ch <= '\u9fa5':
            return True
    return False

def ismerge(number):
    if number == 1:
        return True
    return False

def readxls(filename,op):
    datas = []
    if op == 0:
        workbook = xlrd.open_workbook("./file/output/" + filename, formatting_info=False)
    else:
        workbook = xlrd.open_workbook("./file/input/" + filename, formatting_info=False)
    print("所有的工作表：",workbook.sheet_names())
    sheetb = workbook.sheet_by_index(0)
    ordernumber = sheetb.row_values(2)[14] #文件编号SZ-LT37 
    ordern = ordernumber[3:] #料单号LT37 

    for i in range(len(workbook.sheet_names())):
        sheet1 = workbook.sheet_by_index(i)
        for i in range(5, sheet1.nrows): 
                tmp_row = sheet1.row_values(i)[2:] 
                if tmp_row[1] == "小计" and tmp_row[2] == "" :
                    break
                if tmp_row.count('') > 4: #空元素太多排除
                    continue
                datas.append(tmp_row)
    return datas,ordern

def writexls(datas):
    if os.path.exists('./file/download/出货单.xls'):
        os.remove('./file/download/出货单.xls')
    wb = xlwt.Workbook()
    ws = wb.add_sheet("CNY")
    row4 = ['型材名称', '厂家型材号', '材质状态', '规格(mm/支)', '实际数量(支)', '备用数量(支)', '总数量(支)', '收货地', '色号', 
            '线密度(Kg/m)', '重量(Kg)', '喷涂长度(mm)', '喷涂面积(平方米)', '表面处理方式', '备注', '料单号']
    for j in range(len(row4)):
        ws.write(0, j, row4[j]) 

    for i in range(len(datas)):
        tmp = datas[i][1:]
        for j in range(len(tmp)):
            ws.write(i+1, j, tmp[j]) 
    wb.save("./file/download/出货单.xls")

# datas = [[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16],[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]]
# writexls(datas)

#历史搜搜过页面的数据结构
#[['tablename',[['datas'],['datas2']]]
#results = [["tt",[[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16],[10,20,30,4,5,6,7,8,9,10,11,12,13,14,15,16]]],["tt2",[[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16],[10,20,30,4,5,6,7,8,9,10,11,12,13,14,15,16]]]]