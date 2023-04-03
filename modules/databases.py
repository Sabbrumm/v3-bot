import sqlite3 as sl
from paths import DB_PATH

def get_data(var:str, table:str, predicate=None, order=None, ASCDESC=None):
    output = []
    sql = f"select {var} from {table}"
    if predicate!= None:
        sql+=f" where {predicate}"
    if order!=None and ASCDESC!=None:
        sql+= f"order by {order} {ASCDESC}"
    con = sl.connect(DB_PATH)
    with con:
        data = con.execute(sql)
        for row in data:
            output.append(row)
        con.commit()
    return output
def update_data(table:str, change:str, predicate:str=None):
    sql = f"update {table} set {change}"
    if predicate != None:
        sql += f" where {predicate}"
    con = sl.connect(DB_PATH)
    adder = con.cursor()
    adder.execute(sql)
    con.commit()
    return 1
def remove_data(table:str, predicate:str):
    sql = 'DELETE FROM {} WHERE {}'.format(table, predicate)
    con = sl.connect(DB_PATH)
    adder = con.cursor()
    adder.execute(sql)
    con.commit()
    return 1
def add_data(table: str, values: list):
    val2 = []
    for val in values:
        if isinstance(val, int):
            val2.append(str(val))
        if isinstance(val, str):
            val2.append('"'+val+'"')
        if str(type(val)) == "<class 'NoneType'>":
            val2.append('Null')
    sql = 'INSERT INTO {} VALUES ({});'.format(table, ", ".join(val2))
    con = sl.connect(DB_PATH)
    adder = con.cursor()
    adder.execute(sql)
    con.commit()
    return 1
def get_table_names(table:str):
    con = sl.connect(DB_PATH)
    with con:
        data = con.execute(f'PRAGMA table_info("{table}")')
        columns = [i[1] for i in data]
        return columns


def sql_mode(command):
    output = []
    try:
        con = sl.connect(DB_PATH)
        data = con.execute(command)
        for row in data:
            output.append(row)
        con.commit()
        return output
    except Exception as error:
        return f'Error: {error}'