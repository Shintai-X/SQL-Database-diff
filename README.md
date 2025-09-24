## Objective
It allows detecting and correcting discrepancies between 2 SQL Databases and generate SQL files to fix differences

The goal is to keep both databases synchronized and avoid any divergence.

---
## How to run the script

1. Have python installed on the machine.  
2. Create a folder and put the script on it.  
3. Download pyodbc package :  
   ```bash
   pip install pyodbc
   ```
5. Run the script:  
   ```bash
   python main.py
   ``` 
## Script Workflow

### 1. Initial Cleanup
- Deletes existing SQL files in the current folder.  
- Ensures a clean starting point before each execution.

### 2. Database Connection
- Connects using the provided connection strings.  
- Retrieves tables and their columns from `INFORMATION_SCHEMA`.  
- Stores the data in a dictionary named `schema` (one per database).

### 3. Type Normalization
- The `sql_type` function converts types retrieved from `INFORMATION_SCHEMA` into valid SQL types.  
- Ensures that the generated scripts are compatible for creating or modifying columns.

### 4. Building the Global Dictionary
- Merges the schemas of both databases into an `all_tables` dictionary.  
- This dictionary contains all tables present in either database.

### 5. Table Comparison
- If a table is missing from a database:  
  - generates a SQL query to create it;  
  - moves to the next table using the `continue` statement.  

### 6. Column Comparison
- If a table exists in both databases:  
  - compares the columns one by one;  
  - if discrepancies are found, generates the SQL query needed to fix them.  

The compared points are:  
- column existence  
If the column exists in both databases, the following are compared:  
- column type  
- nullability  
- size
