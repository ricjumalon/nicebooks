import os
import csv
import psycopg2

#create connection to dabatase
conn = psycopg2.connect(os.getenv("DATABASE_URL"))

#open a cursor that will be used for database operations
db_cursor = conn.cursor()

#set the filename/path of the csv file
filename = "books.csv"

#trap errors in opening file
try:
    with open(filename) as f: #open files
        
        #use the copy_expert function of the psycopg2 with a posgresql query to copy the data from the CSV file to postgresql server
        db_cursor.copy_expert("COPY books (isbn, title, author, year) FROM STDIN WITH (FORMAT CSV, DELIMITER ',', HEADER TRUE)",f)
    
    conn.commit()   #make the changes
    print("Import data successful!")

    #close the communication with the database
    db_cursor.close()
    conn.close()

except psycopg2.Error as e:
    print(f"Error: {e}") #display error message if occurs