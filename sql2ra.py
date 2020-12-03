from pprint import pprint

import re
import sqlparse
import radb
import radb.ast
import radb.parse


def extract_rel_name(attribute):
    if attribute.count('.') != 0:
        index_point = attribute.index('.')
        return {'rel': attribute[:index_point], 'name': attribute[index_point + 1:]}
    else:
        return {'rel': None, 'name': attribute}


def table_list_names(stmt_tokens):
    return clean_table_names(stmt_tokens[8].value).split(',')


def select(stmt_tokens, table_names):
    where_clause = stmt_tokens[-1] if str(stmt_tokens[-1][0]) == 'where' else None
    where_string = where_clause.value.replace('and', '')
    attributes_list = re.findall(r"[\w.']+", where_string)[1:]
    attref_list = [radb.ast.AttrRef(rel=extract_rel_name(attribute)['rel'], name=extract_rel_name(attribute)['name'])
                   for attribute in attributes_list]
    n = len(attref_list)
    res = attref_list[0]
    for i in range(1, n):
        res = radb.ast.ValExprBinaryOp(res, radb.ast.sym.EQ, attref_list[i])

    return radb.ast.Select(res, cross(table_names))


def clean_table_names(table_names):
    return re.sub(r"\s+", "", table_names)


def clean_query(sql_query):
    """remove all successive whitespace >2 and remove the white spaces at the start a
                            and at the end of the sql_query"""
    return re.sub("\s\s+", " ", sql_query).strip()


def cross(table_names):
    relref_list = [radb.ast.RelRef(rel=name) for name in table_names]
    n = len(relref_list)
    res = relref_list[0]
    for i in range(1, n):
        res = radb.ast.Cross(res, relref_list[i])
    return res


###########     select distinct * from Person where age=16;     #############
# cond = radb.ast.ValExprBinaryOp(radb.ast.AttrRef(None, 'age'), radb.ast.sym.EQ, radb.ast.RANumber('16'))
# input = radb.ast.RelRef('Person')
# select = radb.ast.Select(cond, input)
# print(select) => \select_{age=16}(Person);
# inputs =
# type(radb.ast.Cross())
###       "select distinct * from Person" ====>   "Person;"

# sql = "select distinct * from Person, Eats, Serves,foot,google"
# relational_query = "((Person \cross Eats) \cross Serves) \cross foot;"
# sql = clean_query(sql)
# relational_query = clean_query(relational_query)

# stmt_tokens = sqlparse.parse(sql)[0].tokens

# test_stmt = sqlparse.parse(sql)[0]
# sql1 = test_stmt.value
# print(sql1)
# print(type(sql))

sql2_test = "select distinct * from Person, Eats where Person.name = Eats.name and a = b "
relational_query2_test = "\select_{Person.name = Eats.name}(Person \cross Eats);"

sql2 = clean_query(sql2_test)
relational_query2 = clean_query(relational_query2_test)
stmt_tokens = sqlparse.parse(sql2)[0].tokens

patters = {'operation': stmt_tokens[0].value, "distinct": stmt_tokens[2], 'attributes': stmt_tokens[4],
           'from': table_list_names(stmt_tokens),
           'condition': stmt_tokens[-1] if str(stmt_tokens[-1][0]) == 'where' else None}

expected = radb.parse.one_statement_from_string(relational_query2)

# where_tokens = patters['condition'].value.replace('and', '')
# where_tokens = re.findall(r"[\w.']+", where_tokens)[1:][0]
# print(where_tokens[:where_tokens.index('.')])
# print(where_tokens[where_tokens.index('.') + 1:])
# print(expected.inputs)
# print('yup')

# cross_object = cross(patters['from'])
s = select(stmt_tokens,patters['from'])
print(type(s))
# print(cross_object)

def translate(stmt):
    # sql = """select distinct Person.name, pizzeria from Person, Eats, Serves
    # where Person.name = Eats.name and Eats.pizza = Serves.pizza"""
    stmt_tokens = stmt.tokens
    patters = {'operation': stmt_tokens[0], "distinct": stmt_tokens[2], 'attributes': stmt_tokens[4],
               'from': stmt_tokens[8], 'where': stmt_tokens[-1]}

    if (str(patters['operation']) == 'select'):
        cond = radb.ast.ValExprBinaryOp(radb.ast.AttrRef(None, 'age'), radb.ast.sym.EQ, radb.ast.RANumber('16'))
        input = radb.ast.RelRef('Person')
        select = radb.ast.Select(cond, input)

# for i, j in patters.items():
#     print(i, j)
