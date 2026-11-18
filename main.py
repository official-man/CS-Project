# ================================================================
#  main.py  |  School Lab Inventory Manager
#  CBSE Class 12 Computer Science Project
#
#  Architecture : Purely Procedural (no classes)
#  Database     : MySQL via mysql-connector-python
#  Interface    : Terminal text menu (print / input only)
#
#  HOW TO RUN:
#    1. Run setup.sql in MySQL once.
#    2. pip install mysql-connector-python
#    3. python main.py
# ================================================================

import mysql.connector          # imports the MySQL driver library so Python can talk to MySQL
from datetime import date       # imports the date class so we can get today's calendar date

# ----------------------------------------------------------------
# SECTION 1 : DATABASE CONNECTION
# ----------------------------------------------------------------

def get_connection():
    # This function creates and returns a live connection to the
    # MariaDB server running on this same computer via a Unix socket.
    #
    # WHY unix_socket instead of password?
    # On most Linux systems (Arch, Ubuntu, Debian), MariaDB's root
    # account uses "unix_socket" authentication — it checks your
    # Linux OS username instead of a password. Connecting with
    # password="something" will ALWAYS fail with ERROR 1698 for root.
    # Using unix_socket="/run/mysqld/mysqld.sock" bypasses that and
    # lets the OS confirm you are the root Linux user automatically.

    conn = mysql.connector.connect(            # calls the connect() function from the imported library
        unix_socket = "/run/mysqld/mysqld.sock", # path to MariaDB's socket file — the "door" to the DB server
        user        = "adhithyan",             # your Linux username — MariaDB unix_socket auth matches this
        database    = "LabInventory"           # the specific database we created in setup.sql
    )
    return conn                                # sends the connection object back to whoever called this function


# ----------------------------------------------------------------
# SECTION 2 : FEATURE FUNCTIONS
# ----------------------------------------------------------------

# ---- 2.1  ADD A NEW ITEM ----------------------------------------

def add_item():
    # Asks the user for a name and optional starting quantity,
    # then inserts a brand-new row into the Items table.

    print("\n--- ADD NEW ITEM ---")           # prints a heading so the user knows which screen they are on

    name = input("Enter item name: ").strip()  # asks the user to type the item name and removes extra spaces
    if not name:                               # checks whether the user pressed Enter without typing anything
        print("Item name cannot be empty.")    # tells the user the name is required
        return                                 # exits this function early without doing anything else

    qty_input = input("Enter starting quantity (default 0): ").strip()  # asks for starting stock level
    if qty_input == "":                        # checks if the user left the quantity blank
        qty = 0                                # sets quantity to 0 if nothing was entered
    else:
        qty = int(qty_input)                   # converts the typed string "25" into the whole number 25

    conn   = get_connection()                  # opens a fresh connection to the MySQL database
    cursor = conn.cursor()                     # creates a cursor — think of it as a "pen" that writes SQL to MySQL

    sql = "INSERT INTO Items (name, total_qty) VALUES (%s, %s)"  # the SQL template; %s are safe placeholders
    values = (name, qty)                       # a tuple holding the actual data that will fill the placeholders

    cursor.execute(sql, values)                # sends the SQL + data to MySQL; MySQL runs the INSERT
    conn.commit()                              # permanently saves the change; without this MySQL rolls it back

    print(f"Item '{name}' added successfully with quantity {qty}.")  # confirms success to the user

    cursor.close()                             # closes the cursor — releases that "pen" back to the system
    conn.close()                               # closes the database connection — frees up the network socket


# ---- 2.2  ISSUE AN ITEM (subtract stock) ------------------------

def issue_item():
    # Lets the user subtract a quantity from an existing item
    # and logs the event as a negative qty_change in Transactions.

    print("\n--- ISSUE ITEM ---")              # heading for this screen

    item_id   = int(input("Enter Item ID to issue: "))          # gets the item_id number from the user
    qty       = int(input("Enter quantity to issue: "))          # gets how many units to subtract
    purpose   = input("Enter purpose (e.g. lab name): ").strip() # gets an optional reason for issuing

    conn   = get_connection()                  # opens a new database connection
    cursor = conn.cursor()                     # creates the cursor to send SQL commands

    # First, check that the item exists AND has enough stock.
    cursor.execute("SELECT name, total_qty FROM Items WHERE item_id = %s", (item_id,))
    # ^ sends a SELECT query to MySQL to fetch the name and quantity for this specific item_id

    row = cursor.fetchone()                    # retrieves exactly one result row from MySQL; None if not found

    if row is None:                            # checks whether MySQL returned nothing (item doesn't exist)
        print("Item not found.")               # informs the user the ID they typed doesn't exist
        cursor.close()                         # closes cursor before leaving the function
        conn.close()                           # closes connection before leaving the function
        return                                 # exits the function early

    item_name, current_qty = row               # unpacks the tuple — item_name gets name, current_qty gets total_qty

    if qty > current_qty:                      # checks whether user is trying to issue more than what's in stock
        print(f"Insufficient stock. Available: {current_qty}")  # tells the user how much stock is left
        cursor.close()                         # closes cursor cleanly
        conn.close()                           # closes connection cleanly
        return                                 # exits early without making any database changes

    # Update the Items table: subtract the issued quantity from total_qty.
    update_sql    = "UPDATE Items SET total_qty = total_qty - %s WHERE item_id = %s"
    # ^ SQL template: total_qty = total_qty - (the number the user typed)
    update_values = (qty, item_id)             # tuple with the values to fill in the two %s placeholders

    cursor.execute(update_sql, update_values)  # sends the UPDATE command to MySQL; MySQL adjusts the number

    # Log the event in Transactions with a NEGATIVE qty_change.
    log_sql = """
        INSERT INTO Transactions (item_id, date, qty_change, purpose)
        VALUES (%s, %s, %s, %s)
    """                                        # multi-line SQL string; easier to read than one long line
    today         = date.today()               # gets today's date from the operating system (e.g. 2026-11-18)
    log_values    = (item_id, today, -qty, purpose)
    # ^ negative qty because items are going OUT of the inventory

    cursor.execute(log_sql, log_values)        # sends the INSERT to MySQL; MySQL saves the transaction log row

    conn.commit()                              # permanently saves BOTH the UPDATE and the INSERT together

    print(f"Issued {qty} unit(s) of '{item_name}'. New stock: {current_qty - qty}")
    # ^ shows the user the updated stock level after subtraction

    cursor.close()                             # closes cursor
    conn.close()                              # closes connection


# ---- 2.3  RESTOCK AN ITEM (add stock) ---------------------------

def restock_item():
    # Lets the user add quantity to an existing item
    # and logs the event as a positive qty_change in Transactions.

    print("\n--- RESTOCK ITEM ---")            # heading for this screen

    item_id = int(input("Enter Item ID to restock: "))    # asks for the item_id of the item being restocked
    qty     = int(input("Enter quantity to add: "))        # asks how many new units arrived
    purpose = input("Enter source/reason: ").strip()       # optional note about where the new stock came from

    conn   = get_connection()                  # opens database connection
    cursor = conn.cursor()                     # creates the cursor

    # Verify the item_id actually exists in the Items table.
    cursor.execute("SELECT name FROM Items WHERE item_id = %s", (item_id,))
    # ^ sends SELECT to MySQL; fetches the name column for this item_id

    row = cursor.fetchone()                    # gets one row from the result; None if no match

    if row is None:                            # item_id typed by user does not exist in the table
        print("Item not found.")               # tells the user
        cursor.close()                         # clean up cursor
        conn.close()                           # clean up connection
        return                                 # exits early

    item_name = row[0]                         # row is a tuple like ("Beaker 250ml",); [0] picks the first element

    # Update Items table: add the restocked quantity to total_qty.
    update_sql    = "UPDATE Items SET total_qty = total_qty + %s WHERE item_id = %s"
    # ^ total_qty = total_qty + the new units coming in
    update_values = (qty, item_id)             # fills in the two %s placeholders

    cursor.execute(update_sql, update_values)  # MySQL runs the UPDATE; total_qty increases

    # Log the event in Transactions with a POSITIVE qty_change.
    log_sql = """
        INSERT INTO Transactions (item_id, date, qty_change, purpose)
        VALUES (%s, %s, %s, %s)
    """                                        # INSERT template for the transaction log
    today      = date.today()                  # today's date from the OS
    log_values = (item_id, today, qty, purpose)
    # ^ positive qty because items are coming INTO the inventory

    cursor.execute(log_sql, log_values)        # MySQL inserts the transaction log row

    conn.commit()                              # permanently saves both the UPDATE and INSERT

    print(f"Restocked '{item_name}' by {qty} unit(s).")  # confirms the action to the user

    cursor.close()                             # closes cursor
    conn.close()                              # closes connection


# ---- 2.4  VIEW COMPLETE INVENTORY --------------------------------

def view_inventory():
    # Fetches and prints every row from the Items table
    # so the user can see the full current stock.

    print("\n--- COMPLETE INVENTORY ---")      # heading for this screen

    conn   = get_connection()                  # opens database connection
    cursor = conn.cursor()                     # creates cursor

    cursor.execute("SELECT item_id, name, total_qty FROM Items ORDER BY item_id")
    # ^ tells MySQL to retrieve ALL rows from Items, sorted by item_id ascending

    rows = cursor.fetchall()                   # fetches every result row at once into a Python list of tuples

    if not rows:                               # checks whether the list is empty (no items added yet)
        print("No items found in inventory.")  # tells the user the table is empty
    else:
        # Print a table header with fixed-width columns using string formatting.
        print(f"\n{'ID':<6} {'Item Name':<30} {'Qty in Stock':<15}")
        # ^ :<6 means left-align in a field 6 chars wide; makes columns line up neatly
        print("-" * 55)                        # prints 55 dashes to form a visual separator line

        for row in rows:                       # loops through each tuple in the rows list one by one
            item_id, name, qty = row           # unpacks each tuple into three separate variables
            print(f"{item_id:<6} {name:<30} {qty:<15}")
            # ^ prints one row of the table with the same column widths as the header

    cursor.close()                             # closes cursor
    conn.close()                              # closes connection


# ---- 2.5  CHECK LOW STOCK ----------------------------------------

def check_low_stock():
    # Asks the user for a threshold number, then queries MySQL
    # to find all items whose total_qty is at or below that number.

    print("\n--- LOW STOCK ALERT ---")         # heading for this screen

    threshold = int(input("Enter minimum stock threshold: "))
    # ^ user types a number; items at or below this will be flagged

    conn   = get_connection()                  # opens database connection
    cursor = conn.cursor()                     # creates cursor

    sql    = "SELECT item_id, name, total_qty FROM Items WHERE total_qty <= %s ORDER BY total_qty"
    # ^ SELECT query with a WHERE filter; <= means "less than or equal to"
    # ^ ORDER BY total_qty shows the most critically low items first

    cursor.execute(sql, (threshold,))          # sends the query; (threshold,) is a single-element tuple — the comma is mandatory

    rows = cursor.fetchall()                   # gets all matching rows into a Python list

    if not rows:                               # empty list means no items are below the threshold
        print(f"All items have stock above {threshold}. No alerts.")
        # ^ good news message
    else:
        print(f"\nItems with stock <= {threshold}:\n")  # sub-heading
        print(f"{'ID':<6} {'Item Name':<30} {'Qty in Stock':<15}")  # column headers
        print("-" * 55)                        # separator line

        for row in rows:                       # loops through each low-stock item
            item_id, name, qty = row           # unpacks the tuple
            print(f"{item_id:<6} {name:<30} {qty:<15}")  # prints one row

    cursor.close()                             # closes cursor
    conn.close()                              # closes connection


# ---- 2.6  VIEW TRANSACTION HISTORY (bonus) -----------------------

def view_transactions():
    # Shows a full log of every issue and restock event
    # by joining the Transactions table with the Items table.

    print("\n--- TRANSACTION HISTORY ---")     # heading for this screen

    conn   = get_connection()                  # opens database connection
    cursor = conn.cursor()                     # creates cursor

    sql = """
        SELECT t.trans_id,
               i.name,
               t.date,
               t.qty_change,
               t.purpose
        FROM   Transactions t
        JOIN   Items i ON t.item_id = i.item_id
        ORDER  BY t.trans_id DESC
    """
    # ^ JOIN merges Transactions and Items on the matching item_id column
    # ^ ORDER BY trans_id DESC shows the newest transaction first

    cursor.execute(sql)                        # sends the JOIN query to MySQL
    rows = cursor.fetchall()                   # fetches all result rows into a list

    if not rows:                               # list is empty — no transactions logged yet
        print("No transactions found.")        # tells the user
    else:
        print(f"\n{'TID':<6} {'Item':<25} {'Date':<14} {'Qty Change':<12} {'Purpose'}")
        # ^ column headers; Qty Change will be negative for issues, positive for restocks
        print("-" * 75)                        # separator line

        for row in rows:                       # loops through each transaction row
            tid, name, dt, change, purp = row  # unpacks the 5-column tuple
            purp = purp if purp else "N/A"     # if purpose is NULL in MySQL, replace with "N/A"
            change_str = f"+{change}" if change > 0 else str(change)
            # ^ adds a "+" prefix to positive numbers so the user can tell restocks from issues at a glance
            print(f"{tid:<6} {name:<25} {str(dt):<14} {change_str:<12} {purp}")
            # ^ prints one transaction row

    cursor.close()                             # closes cursor
    conn.close()                              # closes connection


# ----------------------------------------------------------------
# SECTION 3 : MAIN MENU (the program entry point)
# ----------------------------------------------------------------

def main():
    # This is the main control loop of the entire program.
    # It prints a menu, reads the user's choice, and calls
    # the matching function. It keeps looping until the user
    # chooses to exit.

    while True:                                # True means loop forever until we explicitly break out
        print("\n" + "=" * 45)                 # prints a visual top border for the menu
        print("   SCHOOL LAB INVENTORY MANAGER")        # program title
        print("   CBSE Class 12 CS Project")            # subtitle
        print("=" * 45)                        # bottom border of the title area
        print("  1. Add New Item")             # menu option 1
        print("  2. Issue Item")               # menu option 2
        print("  3. Restock Item")             # menu option 3
        print("  4. View Full Inventory")      # menu option 4
        print("  5. Check Low Stock Alert")    # menu option 5
        print("  6. View Transaction History") # menu option 6
        print("  7. Exit")                     # menu option 7
        print("-" * 45)                        # separator line before the prompt

        choice = input("Enter your choice (1-7): ").strip()
        # ^ reads whatever the user types and removes leading/trailing spaces

        if choice == "1":                      # checks if user typed "1"
            add_item()                         # calls the add_item function defined above
        elif choice == "2":                    # checks if user typed "2"
            issue_item()                       # calls the issue_item function
        elif choice == "3":                    # checks if user typed "3"
            restock_item()                     # calls the restock_item function
        elif choice == "4":                    # checks if user typed "4"
            view_inventory()                   # calls the view_inventory function
        elif choice == "5":                    # checks if user typed "5"
            check_low_stock()                  # calls the check_low_stock function
        elif choice == "6":                    # checks if user typed "6"
            view_transactions()                # calls the view_transactions function
        elif choice == "7":                    # checks if user typed "7"
            print("Exiting. Goodbye!")         # prints a farewell message
            break                              # breaks out of the while True loop, ending the program
        else:
            print("Invalid choice. Please enter a number between 1 and 7.")
            # ^ tells the user their input was not a valid menu option


# ----------------------------------------------------------------
# SECTION 4 : PROGRAM START
# ----------------------------------------------------------------

# This is a standard Python guard. The block below runs ONLY
# when this file is executed directly (python main.py).
# It does NOT run if this file is imported by another script.

if __name__ == "__main__":                     # checks whether Python launched this file directly
    main()                                     # calls the main function to start the program loop
