```python
import pyodbc
import os

# Output files
tables_file_path = "missing_tables.sql"
cols_file_path = "missing_columns.sql"
diff_file_path = "columns_diff.sql"

# Remove existing files if they exist
for f in [tables_file_path, cols_file_path, diff_file_path]:
    if os.path.exists(f):
        os.remove(f)
        print(f"[INFO] Old file removed: {f}")

def get_schema(connection_string):
    """Retrieve tables and columns from a database"""
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    query = """
    SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS
    ORDER BY TABLE_NAME, COLUMN_NAME
    """
    cursor.execute(query)

    schema = {}
    for row in cursor.fetchall():
        table = row.TABLE_NAME
        column = {
            "name": row.COLUMN_NAME,
            "type": row.DATA_TYPE,
            "nullable": row.IS_NULLABLE,
            "max_length": row.CHARACTER_MAXIMUM_LENGTH,
        }
        schema.setdefault(table, []).append(column)

    conn.close()
    return schema

def sql_type(col):
    """Return SQL type with length if applicable"""
    t = col['type'].upper()
    if t in ['CHAR', 'VARCHAR', 'NVARCHAR'] and col['max_length']:
        return f"{t}({col['max_length']})"
    return t

def compare_schemas(schema1, schema2, db1_name="DB1", db2_name="DB2"):
    """Compare two schemas and store differences in files with solutions"""
    
    with open(tables_file_path, "w", encoding="utf-8") as tables_file, \
         open(cols_file_path, "w", encoding="utf-8") as cols_file, \
         open(diff_file_path, "w", encoding="utf-8") as diff_file:

        all_tables = set(schema1.keys()).union(set(schema2.keys()))

        for table in sorted(all_tables):
            # Missing tables
            if table not in schema1:
                msg = f"-- ISSUE: Table {table} exists in {db2_name} but is missing in {db1_name}\n"
                solution = f"-- SOLUTION: Create table {table} in {db1_name}\n"
                print(msg.strip())
                tables_file.write(msg)
                tables_file.write(solution)

                cols = schema2[table]
                cols_sql = ",\n    ".join(f"{c['name']} {sql_type(c)} {'NULL' if c['nullable']=='YES' else 'NOT NULL'}" for c in cols)
                tables_file.write(f"CREATE TABLE {table} (\n    {cols_sql}\n);\n\n")
                continue

            if table not in schema2:
                msg = f"-- ISSUE: Table {table} exists in {db1_name} but is missing in {db2_name}\n"
                solution = f"-- SOLUTION: Create table {table} in {db2_name}\n"
                print(msg.strip())
                tables_file.write(msg)
                tables_file.write(solution)

                cols = schema1[table]
                cols_sql = ",\n    ".join(f"{c['name']} {sql_type(c)} {'NULL' if c['nullable']=='YES' else 'NOT NULL'}" for c in cols)
                tables_file.write(f"CREATE TABLE {table} (\n    {cols_sql}\n);\n\n")
                continue

            # Columns
            cols1 = {c['name']: c for c in schema1[table]}
            cols2 = {c['name']: c for c in schema2[table]}

            # Missing columns
            for col in sorted(cols1.keys() - cols2.keys()):
                c = cols1[col]
                msg = f"-- ISSUE: Column {col} in {db1_name}.{table} is missing in {db2_name}\n"
                solution = f"-- SOLUTION: Add the column in {db2_name}\n"
                print(msg.strip())
                cols_file.write(msg)
                cols_file.write(solution)
                cols_file.write(f"ALTER TABLE {table} ADD {c['name']} {sql_type(c)} {'NULL' if c['nullable']=='YES' else 'NOT NULL'};\n\n")

            for col in sorted(cols2.keys() - cols1.keys()):
                c = cols2[col]
                msg = f"-- ISSUE: Column {col} in {db2_name}.{table} is missing in {db1_name}\n"
                solution = f"-- SOLUTION: Add the column in {db1_name}\n"
                print(msg.strip())
                cols_file.write(msg)
                cols_file.write(solution)
                cols_file.write(f"ALTER TABLE {table} ADD {c['name']} {sql_type(c)} {'NULL' if c['nullable']=='YES' else 'NOT NULL'};\n\n")

            # Different columns
            for col in sorted(cols1.keys() & cols2.keys()):
                c1, c2 = cols1[col], cols2[col]
                if (c1['type'] != c2['type'] or c1['nullable'] != c2['nullable'] or c1['max_length'] != c2['max_length']):
                    msg = f"-- ISSUE: Difference in {table}.{col} : {db1_name}={c1} vs {db2_name}={c2}\n"
                    solution = f"-- SOLUTION: Harmonize {db2_name}.{table}.{col} to match {db1_name}\n"
                    print(msg.strip())
                    diff_file.write(msg)
                    diff_file.write(solution)
                    diff_file.write(f"ALTER TABLE {table} ALTER COLUMN {c1['name']} {sql_type(c1)} {'NULL' if c1['nullable']=='YES' else 'NOT NULL'};\n\n")

if __name__ == "__main__":
    # Masked connection strings
    connection_string1 = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=<SERVER>;DATABASE=<DB_NAME1>;UID=<USER1>;PWD=<PASSWORD1>"
    connection_string2 = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=<SERVER>;DATABASE=<DB_NAME2>;UID=<USER2>;PWD=<PASSWORD2>"

    schema1 = get_schema(connection_string1)
    schema2 = get_schema(connection_string2)

    compare_schemas(schema1, schema2, "DBName1", "DBName2")
