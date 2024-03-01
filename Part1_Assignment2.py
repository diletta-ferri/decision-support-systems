# =======================================
# IMPORT LIBRARIES
# =======================================

import pyodbc
import csv

# =======================================
# CREATION OF THE CONNECTION
# =======================================

# Specify the database connection details
server = 'tcp:lds.di.unipi.it'
database = 'Group_ID_31_DB'
username = 'Group_ID_31'
password = '8PPZ9EZ4'
connectionString = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+password

# Establish a connection and create a cursor
cnxn = pyodbc.connect(connectionString)
cursor = cnxn.cursor()
cursor.fast_executemany = True

# =======================================
# DEFINITION OF THE FUNCTION
# =======================================

# Function to populate a table from a csv file
def populate_table(file_path, table_name, cursor, cnxn):
    with open(file_path, encoding='utf-8-sig') as csvfile:
        file = csv.DictReader(csvfile)
        fields = file.fieldnames
        
        # Generate the SQL INSERT query dynamically based on table name and fields (csv header)
        insert_query = '''
            INSERT INTO Group_ID_31.{} ({})
            VALUES ({})'''.format(table_name, ', '.join(fields), ', '.join(['?'] * len(fields)))

        # Create a list of tuples, each representing a row of values from the csv
        values_list = [tuple(row.values()) for row in file]

        # Execute the query for multiple rows using executemany to speed up the process
        cursor.executemany(insert_query, values_list)

        # Commit the changes to the database
        cnxn.commit()

# =======================================
# POPULATION OF THE TABLES
# =======================================

# Populate the dimension tables
populate_table('participant.csv', 'participant', cursor, cnxn)
populate_table('gun.csv', 'gun', cursor, cnxn)
populate_table('incident.csv', 'incident', cursor, cnxn)
populate_table('date.csv', 'date', cursor, cnxn)
populate_table('geography.csv', 'geography', cursor, cnxn)

# Populate the custody fact table
populate_table('custody.csv', 'custody', cursor, cnxn)

# Close the cursor and connection
cursor.close()
cnxn.close()
