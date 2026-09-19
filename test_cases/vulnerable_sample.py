# Secret Leak
AWS_SECRET_ACCESS_KEY = "1234567890abcdef12345"

# SQL Injection
def get_user(user_input):
    query = f"SELECT * FROM users WHERE username = '{user_input}'"
    return query

# Dangerous Eval & Exec
def run_dynamic_code(user_code):
    eval(user_code)
    exec("import os")

# Nested Loops
def process_matrix(matrix):
    for row in matrix:
        for val in row:
            print(val)
