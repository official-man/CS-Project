# ================================================================
#  db_config.py | Database Configuration & Auto-Initialisation
#  School Lab Inventory Manager — CBSE Class 12 CS Project
#
#  Architecture : Purely Procedural (no classes)
#  Database     : MySQL / MariaDB via mysql-connector-python
#  Platforms    : Archcraft Linux & Windows (Cross-Platform)
# ================================================================

import os                                      # module for interacting with the operating system (cross-platform checks)
import getpass                                 # module to get the logged-in system username for Linux socket fallback
import mysql.connector                         # official MySQL connector library for Python to communicate with the DB

# ----------------------------------------------------------------
# SECTION 1 : DATABASE CONNECTION CONFIGURATION
# ----------------------------------------------------------------
# Instructions for changing password:
#   - School Lab (Windows): usually user="root" and password="" (empty string).
#   - Home PC (Windows or Linux): if your MySQL root has a password, type it inside password="".
#   - Archcraft Linux: if using local MariaDB, get_connection() will also automatically
#     use local unix_socket authentication if TCP access is restricted.
DB_CONFIG = {                                  # dictionary storing default MySQL connection parameters
    "host": "localhost",                       # server host (localhost represents this local machine)
    "user": "root",                            # MySQL username (root is the standard administrative user)
    "password": ""                             # MySQL password (change here if your school lab has a password)
}


# ----------------------------------------------------------------
# SECTION 2 : CONNECTION FACTORY FUNCTION
# ----------------------------------------------------------------

def get_connection(database="LabInventory"):
    # Establishes and returns an active database connection.
    # Accepts an optional database name parameter (defaults to "LabInventory").
    # If database=None, it connects to the MySQL server without selecting a database.
    # Handles both Windows (TCP port 3306) and Linux (TCP or local unix_socket) automatically.

    params = dict(DB_CONFIG)                   # creates a copy of the configuration dictionary
    if database is not None:                   # checks if a specific database was requested
        params["database"] = database          # sets the database name in connection parameters

    try:                                       # attempts standard TCP connection first (works on Windows & Linux TCP)
        conn = mysql.connector.connect(**params)  # connects to MySQL using the dictionary arguments
        return conn                            # returns the live connection object to the caller
    except mysql.connector.Error as primary_err:  # catches connection failure (e.g. Linux socket auth or bad credentials)
        if os.name != "nt":                    # checks if the operating system is Linux/Unix (not Windows "nt")
            socket_paths = [                   # list of standard Linux MariaDB/MySQL unix socket file paths
                "/run/mysqld/mysqld.sock",     # standard MariaDB socket location on Archcraft/Arch Linux
                "/var/run/mysqld/mysqld.sock"  # standard MySQL/MariaDB socket location on Debian/Ubuntu Linux
            ]
            for sock in socket_paths:          # loops through each potential socket file path
                if os.path.exists(sock):       # checks if this socket file actually exists on the disk
                    users_to_try = [           # list of usernames to try for unix socket authentication
                        getpass.getuser(),     # current logged-in Linux username (e.g. "adhithyan")
                        params.get("user", "root")  # the username specified in DB_CONFIG
                    ]
                    for u in users_to_try:     # tries each username in sequence
                        try:                   # attempts connection via the unix socket file
                            sock_args = {      # creates argument dictionary for socket connection
                                "unix_socket": sock,  # path to the unix domain socket file
                                "user": u      # username to authenticate with via OS socket
                            }
                            if database is not None:  # checks if database parameter was specified
                                sock_args["database"] = database  # attaches database name if requested
                            conn = mysql.connector.connect(**sock_args)  # opens connection using unix socket
                            return conn        # returns the successful socket connection object
                        except mysql.connector.Error:  # catches error if this specific user/socket fails
                            continue           # proceeds to try the next candidate username
        raise primary_err                      # if all fallback attempts fail, re-raises the original error


# ----------------------------------------------------------------
# SECTION 3 : DATABASE & TABLE INITIALISATION
# ----------------------------------------------------------------

def initialize_database():
    # Automatically creates the LabInventory database and all required tables
    # if they do not already exist. Runs on application startup so the app
    # works immediately on a brand-new machine without manual SQL execution.

    conn = get_connection(database=None)       # connects to MySQL server without selecting any database
    cursor = conn.cursor()                     # creates a cursor to execute administrative SQL queries

    cursor.execute("CREATE DATABASE IF NOT EXISTS LabInventory")  # creates the LabInventory database if missing
    cursor.execute("USE LabInventory")         # switches current session context to LabInventory database

    # Create Items table to track laboratory items and stock quantities
    items_table_sql = """
    CREATE TABLE IF NOT EXISTS Items (
        item_id   INT          AUTO_INCREMENT PRIMARY KEY,
        name      VARCHAR(100) NOT NULL,
        total_qty INT          NOT NULL DEFAULT 0
    )
    """                                        # SQL command definition for creating Items table
    cursor.execute(items_table_sql)            # sends CREATE TABLE IF NOT EXISTS statement to MySQL

    # Create Transactions table to track issues and restocks with a Foreign Key
    trans_table_sql = """
    CREATE TABLE IF NOT EXISTS Transactions (
        trans_id   INT          AUTO_INCREMENT PRIMARY KEY,
        item_id    INT          NOT NULL,
        date       DATE         NOT NULL,
        qty_change INT          NOT NULL,
        purpose    VARCHAR(255),
        CONSTRAINT fk_item
            FOREIGN KEY (item_id)
            REFERENCES Items(item_id)
            ON DELETE CASCADE
    )
    """                                        # SQL command definition for creating Transactions table
    cursor.execute(trans_table_sql)            # sends CREATE TABLE IF NOT EXISTS statement to MySQL

    conn.commit()                              # commits the changes to ensure schema creation is permanent
    cursor.close()                             # closes the cursor to free database resources
    conn.close()                               # closes the connection


# ----------------------------------------------------------------
# SECTION 4 : DIRECT EXECUTION TEST
# ----------------------------------------------------------------

if __name__ == "__main__":                     # checks if this script was executed directly
    print("Initializing database...")          # prints progress message to console
    initialize_database()                      # runs the database and table initialisation function
    print("Database 'LabInventory' and tables 'Items', 'Transactions' ready!")  # confirms setup success
