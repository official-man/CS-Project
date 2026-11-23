# ================================================================
#  terminal_app.py | School Lab Inventory Manager (Terminal Menu)
#  CBSE Class 12 Computer Science Project
#
#  Architecture : Purely Procedural (no classes, zero OOP)
#  Database     : MySQL / MariaDB via mysql-connector-python
#  Platforms    : Archcraft Linux & Windows (Cross-Platform)
#
#  HOW TO RUN:
#    python terminal_app.py
# ================================================================

import os                                      # module for operating system utilities (cross-platform screen clear)
import mysql.connector                         # MySQL database connector driver for Python
from datetime import date                      # date module to obtain current calendar date for transaction timestamps
from db_config import get_connection           # imports database connection helper from db_config.py
from db_config import initialize_database      # imports database auto-initialisation helper from db_config.py


# ----------------------------------------------------------------
# SECTION 1 : UTILITY FUNCTIONS
# ----------------------------------------------------------------

def clear_screen():
    # Clears the terminal screen in a cross-platform manner.
    # Checks os.name: 'nt' represents Windows ('cls'), while others represent Linux/Unix ('clear').

    cmd = "cls" if os.name == "nt" else "clear"  # picks 'cls' on Windows and 'clear' on Linux
    os.system(cmd)                             # executes the OS clear screen command in the shell


def pause():
    # Pauses terminal output so the user can read the results
    # before returning back to the main menu.

    input("\nPress Enter to return to menu...")  # waits for user to press the Enter key before proceeding


# ----------------------------------------------------------------
# SECTION 2 : FEATURE FUNCTIONS (PROCEDURAL CRUD)
# ----------------------------------------------------------------

# ---- 2.1 ADD NEW ITEM -------------------------------------------

def add_item():
    # Prompts for item details and inserts a new row into the Items table.

    print("\n" + "-" * 40)                     # prints horizontal separator line
    print("         ➕ ADD NEW LAB ITEM")        # prints feature screen heading
    print("-" * 40)                            # prints horizontal separator line

    name = input("Enter item name: ").strip()  # prompts user for item name and removes surrounding whitespace
    if not name:                               # checks if user pressed Enter without typing any text
        print("Error: Item name cannot be empty.")  # displays friendly validation error message
        return                                 # exits function early back to menu

    qty_input = input("Enter starting quantity (default 0): ").strip()  # prompts user for initial stock count
    if qty_input == "":                        # checks if the user left the input blank
        qty = 0                                # assigns 0 as the default starting quantity
    else:                                      # executes if the user entered something
        try:                                   # starts error-handling block to catch non-numeric text
            qty = int(qty_input)               # converts the string input into an integer
            if qty < 0:                        # checks if the user entered a negative number
                print("Error: Quantity cannot be negative.")  # displays error message
                return                         # exits function early
        except ValueError:                     # catches conversion error if text contains letters/symbols
            print("Error: Quantity must be a valid whole number.")  # displays beginner-friendly error
            return                             # exits function early

    try:                                       # starts error-handling block for database operations
        conn = get_connection()               # opens an active connection to MySQL
        cursor = conn.cursor()                 # creates a cursor to execute SQL commands

        sql = "INSERT INTO Items (name, total_qty) VALUES (%s, %s)"  # parameterized SQL insert template
        cursor.execute(sql, (name, qty))       # executes insert query safely with tuple parameters
        conn.commit()                          # commits transaction to permanently save the new row to disk

        print(f"\nSuccess: Item '{name}' added successfully with quantity {qty}.")  # prints confirmation message

        cursor.close()                         # closes the cursor to release resources
        conn.close()                           # closes the database connection
    except mysql.connector.Error as err:       # catches potential database errors
        print(f"Database Error: {err}")        # prints readable database error message


# ---- 2.2 ISSUE ITEM (TAKE OUT OF STOCK) -------------------------

def issue_item():
    # Deducts stock quantity from an existing item and logs the issue in Transactions.

    print("\n" + "-" * 40)                     # prints horizontal separator line
    print("          📤 ISSUE LAB ITEM")        # prints feature screen heading
    print("-" * 40)                            # prints horizontal separator line

    id_input = input("Enter Item ID to issue: ").strip()  # prompts for the unique ID of the item
    try:                                       # starts error handling for numeric conversion
        item_id = int(id_input)                # converts typed text into integer ID
        if item_id <= 0:                       # checks for non-positive ID values
            print("Error: Item ID must be a positive integer.")  # prints validation error
            return                             # exits function early
    except ValueError:                         # catches invalid non-numeric input
        print("Error: Item ID must be a valid whole number.")  # prints validation error
        return                                 # exits function early

    qty_input = input("Enter quantity to issue: ").strip()  # prompts for how many units to issue
    try:                                       # starts error handling for numeric quantity
        qty = int(qty_input)                   # converts typed text into integer quantity
        if qty <= 0:                           # checks that quantity is at least 1
            print("Error: Quantity to issue must be greater than 0.")  # prints validation error
            return                             # exits function early
    except ValueError:                         # catches invalid non-numeric input
        print("Error: Quantity must be a valid whole number.")  # prints validation error
        return                                 # exits function early

    purpose = input("Enter purpose (e.g. Class 12 Lab): ").strip()  # prompts for optional reason for issuing

    try:                                       # starts error-handling block for database operations
        conn = get_connection()               # opens database connection
        cursor = conn.cursor()                 # creates database cursor

        # Check if the requested item exists and has sufficient stock
        cursor.execute("SELECT name, total_qty FROM Items WHERE item_id = %s", (item_id,))  # queries item row
        row = cursor.fetchone()                # fetches matching row tuple (name, total_qty)

        if row is None:                        # checks if no row was returned by MySQL
            print(f"Error: Item with ID {item_id} does not exist.")  # prints not-found message
            cursor.close()                     # closes cursor
            conn.close()                       # closes connection
            return                             # exits function early

        item_name, current_qty = row           # unpacks the fetched tuple into two variables

        if qty > current_qty:                  # checks if requested quantity exceeds available stock
            print(f"Error: Insufficient stock. Item '{item_name}' currently has {current_qty} unit(s).")
            cursor.close()                     # closes cursor
            conn.close()                       # closes connection
            return                             # exits function early

        # Update stock count in Items table
        update_sql = "UPDATE Items SET total_qty = total_qty - %s WHERE item_id = %s"  # SQL update query
        cursor.execute(update_sql, (qty, item_id))  # executes the stock deduction

        # Insert audit log record in Transactions table with negative qty_change
        trans_sql = "INSERT INTO Transactions (item_id, date, qty_change, purpose) VALUES (%s, %s, %s, %s)"
        cursor.execute(trans_sql, (item_id, date.today(), -qty, purpose))  # executes transaction log insert

        conn.commit()                          # commits both update and insert atomically
        print(f"\nSuccess: Issued {qty} unit(s) of '{item_name}'. New balance: {current_qty - qty} unit(s).")

        cursor.close()                         # closes cursor
        conn.close()                           # closes connection
    except mysql.connector.Error as err:       # catches potential database errors
        print(f"Database Error: {err}")        # prints readable database error message


# ---- 2.3 RESTOCK ITEM (ADD TO STOCK) ----------------------------

def restock_item():
    # Adds stock quantity to an existing item and logs the restock in Transactions.

    print("\n" + "-" * 40)                     # prints horizontal separator line
    print("         📥 RESTOCK LAB ITEM")       # prints feature screen heading
    print("-" * 40)                            # prints horizontal separator line

    id_input = input("Enter Item ID to restock: ").strip()  # prompts for the ID of the item to restock
    try:                                       # starts error handling for numeric conversion
        item_id = int(id_input)                # converts typed text into integer ID
        if item_id <= 0:                       # checks for non-positive ID values
            print("Error: Item ID must be a positive integer.")  # prints validation error
            return                             # exits function early
    except ValueError:                         # catches invalid non-numeric input
        print("Error: Item ID must be a valid whole number.")  # prints validation error
        return                                 # exits function early

    qty_input = input("Enter quantity to add: ").strip()  # prompts for how many units to add
    try:                                       # starts error handling for numeric quantity
        qty = int(qty_input)                   # converts typed text into integer quantity
        if qty <= 0:                           # checks that quantity is at least 1
            print("Error: Quantity to restock must be greater than 0.")  # prints validation error
            return                             # exits function early
    except ValueError:                         # catches invalid non-numeric input
        print("Error: Quantity must be a valid whole number.")  # prints validation error
        return                                 # exits function early

    purpose = input("Enter purpose (e.g. Annual Purchase): ").strip()  # prompts for optional restock details

    try:                                       # starts error-handling block for database operations
        conn = get_connection()               # opens database connection
        cursor = conn.cursor()                 # creates database cursor

        # Check if the requested item exists in Items table
        cursor.execute("SELECT name, total_qty FROM Items WHERE item_id = %s", (item_id,))  # queries item row
        row = cursor.fetchone()                # fetches matching row tuple (name, total_qty)

        if row is None:                        # checks if no row was returned
            print(f"Error: Item with ID {item_id} does not exist.")  # prints not-found message
            cursor.close()                     # closes cursor
            conn.close()                       # closes connection
            return                             # exits function early

        item_name, current_qty = row           # unpacks fetched tuple into variables

        # Update stock count in Items table
        update_sql = "UPDATE Items SET total_qty = total_qty + %s WHERE item_id = %s"  # SQL update query
        cursor.execute(update_sql, (qty, item_id))  # executes the stock addition

        # Insert audit log record in Transactions table with positive qty_change
        trans_sql = "INSERT INTO Transactions (item_id, date, qty_change, purpose) VALUES (%s, %s, %s, %s)"
        cursor.execute(trans_sql, (item_id, date.today(), qty, purpose))  # executes transaction log insert

        conn.commit()                          # commits both update and insert atomically
        print(f"\nSuccess: Restocked '{item_name}' by {qty} unit(s). New balance: {current_qty + qty} unit(s).")

        cursor.close()                         # closes cursor
        conn.close()                           # closes connection
    except mysql.connector.Error as err:       # catches potential database errors
        print(f"Database Error: {err}")        # prints readable database error message


# ---- 2.4 VIEW FULL INVENTORY ------------------------------------

def view_inventory():
    # Retrieves all records from the Items table and displays them in a neat table.

    print("\n" + "=" * 55)                     # prints horizontal separator line
    print("               📦 FULL LAB INVENTORY")  # prints feature screen heading
    print("=" * 55)                            # prints horizontal separator line

    try:                                       # starts error-handling block for database operations
        conn = get_connection()               # opens database connection
        cursor = conn.cursor()                 # creates database cursor

        cursor.execute("SELECT item_id, name, total_qty FROM Items ORDER BY item_id")  # queries all items
        rows = cursor.fetchall()               # fetches all resulting rows as a list of tuples

        if not rows:                           # checks if the inventory table is completely empty
            print("No items found in the inventory.")  # informs the user that table has no rows
        else:                                  # executes if rows exist
            print(f"{'ID':<6} {'Item Name':<32} {'Qty in Stock':<15}")  # prints aligned column headers
            print("-" * 55)                    # prints separator under headers
            for row in rows:                   # iterates through each item tuple in the results list
                item_id, name, qty = row       # unpacks tuple into individual column variables
                print(f"{item_id:<6} {name:<32} {qty:<15}")  # prints row formatted with fixed column widths

        cursor.close()                         # closes cursor
        conn.close()                           # closes connection
    except mysql.connector.Error as err:       # catches potential database errors
        print(f"Database Error: {err}")        # prints readable database error message


# ---- 2.5 CHECK LOW STOCK ALERT ----------------------------------

def check_low_stock():
    # Prompts for a threshold quantity and displays items at or below that threshold.

    print("\n" + "=" * 55)                     # prints horizontal separator line
    print("             ⚠️  LOW STOCK ALERT MONITOR")  # prints feature screen heading
    print("=" * 55)                            # prints horizontal separator line

    thresh_input = input("Enter minimum stock threshold: ").strip()  # prompts user for threshold value
    try:                                       # starts error handling for numeric input
        threshold = int(thresh_input)          # converts typed text into integer threshold
        if threshold < 0:                      # checks for negative threshold
            print("Error: Threshold cannot be negative.")  # displays error message
            return                             # exits function early
    except ValueError:                         # catches non-numeric input
        print("Error: Threshold must be a valid whole number.")  # displays error message
        return                                 # exits function early

    try:                                       # starts error-handling block for database operations
        conn = get_connection()               # opens database connection
        cursor = conn.cursor()                 # creates database cursor

        sql = "SELECT item_id, name, total_qty FROM Items WHERE total_qty <= %s ORDER BY total_qty ASC"
        cursor.execute(sql, (threshold,))      # sends parameterized query with threshold filter
        rows = cursor.fetchall()               # fetches all low-stock rows as a list of tuples

        if not rows:                           # checks if no items fell below the given threshold
            print(f"\nAll items have stock above {threshold}. No low stock warnings!")  # reassurance message
        else:                                  # executes if low-stock items exist
            print(f"\nItems with stock <= {threshold}:")  # displays alert subheader
            print(f"{'ID':<6} {'Item Name':<32} {'Qty in Stock':<15}")  # prints aligned column headers
            print("-" * 55)                    # prints separator line
            for row in rows:                   # iterates through each low-stock item tuple
                item_id, name, qty = row       # unpacks item tuple
                print(f"{item_id:<6} {name:<32} {qty:<15}")  # prints formatted row

        cursor.close()                         # closes cursor
        conn.close()                           # closes connection
    except mysql.connector.Error as err:       # catches potential database errors
        print(f"Database Error: {err}")        # prints readable database error message


# ---- 2.6 VIEW TRANSACTION HISTORY -------------------------------

def view_transactions():
    # Displays transaction audit log by performing an INNER JOIN on Transactions and Items.

    print("\n" + "=" * 78)                     # prints horizontal separator line
    print("                      📋 TRANSACTION AUDIT LOG")  # prints feature screen heading
    print("=" * 78)                            # prints horizontal separator line

    try:                                       # starts error-handling block for database operations
        conn = get_connection()               # opens database connection
        cursor = conn.cursor()                 # creates database cursor

        # SQL JOIN query combining Transactions table with Items table to fetch item name
        sql = """
        SELECT t.trans_id,
               i.name,
               t.date,
               t.qty_change,
               t.purpose
        FROM   Transactions t
        JOIN   Items i ON t.item_id = i.item_id
        ORDER  BY t.trans_id DESC
        """                                    # query string ordering newest transactions first
        cursor.execute(sql)                    # executes the join query
        rows = cursor.fetchall()               # fetches all transaction records as a list of tuples

        if not rows:                           # checks if no transaction records exist
            print("No transactions recorded yet.")  # informs user that log is empty
        else:                                  # executes if transaction rows exist
            print(f"{'TID':<6} {'Item Name':<24} {'Date':<12} {'Qty Change':<12} {'Purpose'}")  # headers
            print("-" * 78)                    # prints separator line
            for row in rows:                   # iterates through each transaction record tuple
                tid, name, dt, change, purp = row  # unpacks the 5-column tuple into distinct variables
                purp_str = purp if purp else "N/A"  # substitutes "N/A" if purpose was left empty/NULL
                change_str = f"+{change}" if change > 0 else str(change)  # adds '+' sign for positive restocks
                print(f"{tid:<6} {name:<24} {str(dt):<12} {change_str:<12} {purp_str}")  # prints aligned row

        cursor.close()                         # closes cursor
        conn.close()                           # closes connection
    except mysql.connector.Error as err:       # catches potential database errors
        print(f"Database Error: {err}")        # prints readable database error message


# ----------------------------------------------------------------
# SECTION 3 : MAIN MENU LOOP
# ----------------------------------------------------------------

def main():
    # Main program entry point. Runs an unbroken while True loop
    # that only terminates when the user explicitly chooses option 7.

    initialize_database()                      # ensures database and tables exist prior to user interactions

    while True:                                # infinite loop to keep menu active until explicit user exit
        print("\n" + "=" * 50)                 # top banner border
        print("     🔬 SCHOOL LAB INVENTORY MANAGER")  # main menu title
        print("     CBSE Class 12 Computer Science Project")  # project subtitle
        print("=" * 50)                        # border separator
        print("  1. ➕ Add New Item")           # menu option 1
        print("  2. 📤 Issue Item (Take Out)")  # menu option 2
        print("  3. 📥 Restock Item (Add In)")  # menu option 3
        print("  4. 📦 View Full Inventory")    # menu option 4
        print("  5. ⚠️  Check Low Stock Alert")  # menu option 5
        print("  6. 📋 View Transaction History")  # menu option 6
        print("  7. ❌ Exit")                  # menu option 7
        print("=" * 50)                        # bottom menu border

        choice = input("Enter your choice (1-7): ").strip()  # prompts user for menu selection

        if choice == "1":                      # checks if option 1 was chosen
            add_item()                         # calls add item function
            pause()                            # pauses so user can see result before menu re-displays
        elif choice == "2":                    # checks if option 2 was chosen
            issue_item()                       # calls issue item function
            pause()                            # pauses so user can see result
        elif choice == "3":                    # checks if option 3 was chosen
            restock_item()                     # calls restock item function
            pause()                            # pauses so user can see result
        elif choice == "4":                    # checks if option 4 was chosen
            view_inventory()                   # calls inventory view function
            pause()                            # pauses so user can see table
        elif choice == "5":                    # checks if option 5 was chosen
            check_low_stock()                  # calls low stock monitor function
            pause()                            # pauses so user can see alerts
        elif choice == "6":                    # checks if option 6 was chosen
            view_transactions()                # calls transaction log view function
            pause()                            # pauses so user can see audit log
        elif choice == "7":                    # checks if option 7 was chosen
            print("\nExiting School Lab Inventory Manager. Goodbye!\n")  # prints farewell message
            break                              # breaks out of the while True loop to terminate program cleanly
        else:                                  # handles any unrecognized input
            print("\nError: Invalid choice. Please enter a number from 1 to 7.")  # friendly invalid input alert
            pause()                            # pauses before returning to menu


# ----------------------------------------------------------------
# SECTION 4 : PROGRAM START GUARD
# ----------------------------------------------------------------

if __name__ == "__main__":                     # ensures main() only executes when run directly as a script
    main()                                     # invokes the main menu loop function
