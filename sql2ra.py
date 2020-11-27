import sqlparse

sql = 'select * from foo; select * from bar;'
# print(sqlparse.split(sql))
print(sqlparse.format(sql, reindent=True, keyword_case='upper'))
