import re
import sqlparse
import radb
import radb.ast
import radb.parse


def columns(stmt_tokens):
    p = stmt_tokens[4].value
    if p.count('*'):
        return "*"
    else:
        return re.findall(r"[\w.']+", p)


def extract_rel_name(attribute):
    if attribute.count('.') != 0:
        index_point = attribute.index('.')
        return {'rel': attribute[:index_point], 'name': attribute[index_point + 1:]}
    else:
        return {'rel': None, 'name': attribute}


def select(stmt_tokens, table_names):
    where_clause = stmt_tokens[-1] if str(stmt_tokens[-1][0]) == 'where' else None
    where_string = where_clause.value.replace('and', '')
    attributes_list = re.findall(r"[\w.']+", where_string)[1:]
    attref_list = [radb.ast.AttrRef(rel=extract_rel_name(attribute)['rel'], name=extract_rel_name(attribute)['name'])
                   for attribute in attributes_list]
    n = len(attref_list)
    valexprebinaryop_list = [radb.ast.ValExprBinaryOp(attref_list[i], radb.ast.sym.EQ, attref_list[i + 1]) for i in
                             range(0, n, 2)]
    res = valexprebinaryop_list[0]
    n2 = len(valexprebinaryop_list)
    for i in range(1, n2):
        res = radb.ast.ValExprBinaryOp(res, radb.ast.sym.AND, valexprebinaryop_list[i])

    return radb.ast.Select(res, cross(table_names))


def is_renamed(table_name):
    return table_name.count(' ') > 0


def extract_table_alias(name):
    return name[name.index(' ') + 1:]


def extract_table_name(name):
    return name[:name.index(' ')]


def table_list_names(stmt_tokens):
    return list(map(lambda x: x.strip(), clean_table_names(stmt_tokens[8].value).split(',')))


def clean_table_names(table_names):
    """remove all successive whitespace >2  modified recently it was
                re.sub(r"\s+", "", table_names) in case code is broken """
    return re.sub(r"\s\s", "", table_names).strip()


def clean_query(sql_query):
    """remove all successive whitespace >2 and remove the white spaces at the start a
                            and at the end of the sql_query"""
    return re.sub("\s\s+", " ", sql_query).strip()


def cross(table_names):
    # if is_renamed(name) else radb.ast.Rename(relname=)
    relref_list = [radb.ast.Rename(relname=extract_table_alias(name), attrnames=None,
                                   input=radb.ast.RelRef(rel=extract_table_name(name))) if is_renamed(
        name) else radb.ast.RelRef(rel=name) for name in table_names]
    n = len(relref_list)
    res = relref_list[0]
    for i in range(1, n):
        res = radb.ast.Cross(res, relref_list[i])
    return res


def project(attributes, stmt_tokens, table_names):
    attrs = [radb.ast.AttrRef(rel=extract_rel_name(attribute)['rel'], name=extract_rel_name(attribute)['name']) for
             attribute in attributes]
    if str(stmt_tokens[-1][0]) != 'where':
        inputs = cross(table_names)
    else:
        inputs = select(stmt_tokens, table_names)

    return radb.ast.Project(attrs, inputs)


# sql2_test = "select distinct X.name from Person X"
# relational_query2_test = "Person;"
#
# sql2 = clean_query(sql2_test)
# relational_query2 = clean_query(relational_query2_test)
# stmt_tokens = sqlparse.parse(sql2)[0].tokens

# patters = {'operation': stmt_tokens[0].value, "distinct": stmt_tokens[2], 'columns': columns(stmt_tokens),
#            'from': table_list_names(stmt_tokens),
#            'condition': stmt_tokens[-1] if str(stmt_tokens[-1][0]) == 'where' else None}

# expected = radb.parse.one_statement_from_string(relational_query2)

# proj = project(patters['columns'], stmt_tokens, patters['from'])
# print(proj)
# cross_object = cross(patters['from'])
# print(cross_object)
# s = select(stmt_tokens,patters['from'])
# print(s)


def translate(stmt):
    sql = clean_query(stmt.value)
    stmt_tokens = sqlparse.parse(sql)[0].tokens
    patters = {'operation': stmt_tokens[0].value, "distinct": stmt_tokens[2], 'columns': columns(stmt_tokens),
               'from': table_list_names(stmt_tokens),
               'condition': stmt_tokens[-1] if str(stmt_tokens[-1][0]) == 'where' else None}
    if patters['columns'] == '*' and len(patters['from']) == 1 and patters['condition'] is None:
        return radb.ast.RelRef(rel=patters['from'][0])
    elif patters['columns'] == '*' and patters['condition'] is None:
        return cross(patters['from'])
    elif patters['columns'] == '*':
        return select(stmt_tokens, patters['from'])
    else:
        return project(patters['columns'], stmt_tokens, patters['from'])


sql_final = "select distinct * from Person"
stmt = sqlparse.parse(sql_final)[0]
ra = translate(stmt)
print(ra)
