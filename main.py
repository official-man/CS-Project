# ================================================================
#  main.py  |  School Lab Inventory Manager — Desktop GUI
#  CBSE Class 12 Computer Science Project
#
#  Architecture : Purely Procedural (no classes)
#  Database     : MariaDB/MySQL via mysql-connector-python
#  Interface    : tkinter Desktop GUI with ttk.Treeview tables
#
#  HOW TO RUN:
#    source venv/bin/activate
#    python main.py
# ================================================================

import tkinter as tk                       # imports the built-in tkinter module — Python's standard GUI library
from tkinter import ttk                    # imports ttk (themed tkinter) — gives us Treeview table widget
from tkinter import messagebox             # imports messagebox — shows popup alert/info/error dialogs
import mysql.connector                     # imports the MySQL driver so Python can talk to MariaDB
from datetime import date                  # imports date so we can get today's calendar date for transactions

# ----------------------------------------------------------------
# SECTION 1 : DATABASE CONNECTION
# (identical backend logic to the terminal version)
# ----------------------------------------------------------------

def get_connection():
    # Opens and returns a live connection to the local MariaDB server.
    # Uses unix_socket authentication (no password needed for root on Linux).

    conn = mysql.connector.connect(            # calls the connector's connect() function
        unix_socket = "/run/mysqld/mysqld.sock", # socket file path — MariaDB's "door" on this machine
        user        = "adhithyan",             # Linux username — MariaDB unix_socket auth matches this
        database    = "LabInventory"           # the database created by setup.sql
    )
    return conn                                # returns the connection object to the caller


# ----------------------------------------------------------------
# SECTION 2 : BACKEND / DATABASE FUNCTIONS
# (pure logic — no GUI code here; same as terminal version)
# ----------------------------------------------------------------

def db_add_item(name, qty):
    # Inserts a new row into the Items table.
    # Called when the user clicks "Add Item" button in the GUI.

    conn   = get_connection()                  # open a database connection
    cursor = conn.cursor()                     # create a cursor to send SQL commands

    sql    = "INSERT INTO Items (name, total_qty) VALUES (%s, %s)"  # INSERT template with safe placeholders
    cursor.execute(sql, (name, qty))           # sends the SQL + data to MariaDB; MariaDB inserts the row
    conn.commit()                              # permanently saves the new row to disk

    cursor.close()                             # releases the cursor from memory
    conn.close()                              # closes the database connection


def db_issue_item(item_id, qty, purpose):
    # Subtracts qty from an item's stock and logs it as a negative transaction.
    # Returns a tuple: (success: bool, message: str)
    # Called when the user clicks "Issue" button in the GUI.

    conn   = get_connection()                  # open connection
    cursor = conn.cursor()                     # create cursor

    cursor.execute("SELECT name, total_qty FROM Items WHERE item_id = %s", (item_id,))
    # ^ SELECT query: fetch the name and current stock for the given item_id
    row = cursor.fetchone()                    # get one result row; None if item_id doesn't exist

    if row is None:                            # item_id the user typed doesn't exist in the table
        cursor.close()                         # close cursor before early return
        conn.close()                          # close connection before early return
        return False, "Item ID not found."     # return failure signal and message to the GUI

    item_name, current_qty = row               # unpack the tuple into two separate variables

    if qty > current_qty:                      # check: user is trying to issue more than what's in stock
        cursor.close()                         # clean up
        conn.close()                          # clean up
        return False, f"Insufficient stock. Available: {current_qty}"  # return failure + message

    cursor.execute(
        "UPDATE Items SET total_qty = total_qty - %s WHERE item_id = %s",
        (qty, item_id)
    )                                          # UPDATE: subtract the issued qty from total_qty in Items

    cursor.execute(
        "INSERT INTO Transactions (item_id, date, qty_change, purpose) VALUES (%s, %s, %s, %s)",
        (item_id, date.today(), -qty, purpose) # negative qty_change because items are going OUT
    )                                          # INSERT: log the issue event in Transactions

    conn.commit()                              # save both UPDATE and INSERT together (atomic operation)
    cursor.close()                             # close cursor
    conn.close()                              # close connection
    return True, f"Issued {qty} unit(s) of '{item_name}'. New stock: {current_qty - qty}"
    # ^ return success signal and message to display in the GUI


def db_restock_item(item_id, qty, purpose):
    # Adds qty to an item's stock and logs it as a positive transaction.
    # Returns a tuple: (success: bool, message: str)
    # Called when the user clicks "Restock" button in the GUI.

    conn   = get_connection()                  # open connection
    cursor = conn.cursor()                     # create cursor

    cursor.execute("SELECT name FROM Items WHERE item_id = %s", (item_id,))
    # ^ SELECT: check that this item_id exists in the Items table
    row = cursor.fetchone()                    # get one result row; None if not found

    if row is None:                            # item_id doesn't exist
        cursor.close()                         # clean up
        conn.close()                          # clean up
        return False, "Item ID not found."     # return failure signal to GUI

    item_name = row[0]                         # row is a tuple like ("Beaker",); [0] picks the first element

    cursor.execute(
        "UPDATE Items SET total_qty = total_qty + %s WHERE item_id = %s",
        (qty, item_id)
    )                                          # UPDATE: add the restocked qty to total_qty in Items

    cursor.execute(
        "INSERT INTO Transactions (item_id, date, qty_change, purpose) VALUES (%s, %s, %s, %s)",
        (item_id, date.today(), qty, purpose)  # positive qty_change because items are coming IN
    )                                          # INSERT: log the restock event in Transactions

    conn.commit()                              # permanently save both changes together
    cursor.close()                             # close cursor
    conn.close()                              # close connection
    return True, f"Restocked '{item_name}' by {qty} unit(s)."  # return success + message to GUI


def db_fetch_inventory(threshold=None):
    # Fetches all rows from Items table.
    # If threshold is given (an integer), returns only rows where total_qty <= threshold.
    # Returns a list of tuples: [(item_id, name, total_qty), ...]

    conn   = get_connection()                  # open connection
    cursor = conn.cursor()                     # create cursor

    if threshold is None:                      # no filter: fetch ALL items
        cursor.execute("SELECT item_id, name, total_qty FROM Items ORDER BY item_id")
        # ^ SELECT all rows sorted by item_id ascending
    else:                                      # filter mode: only fetch low-stock items
        cursor.execute(
            "SELECT item_id, name, total_qty FROM Items WHERE total_qty <= %s ORDER BY total_qty",
            (threshold,)
        )                                      # WHERE clause filters rows; (threshold,) is a single-element tuple

    rows = cursor.fetchall()                   # fetch all matching rows as a list of tuples
    cursor.close()                             # close cursor
    conn.close()                              # close connection
    return rows                                # return the list of tuples to the GUI function that called this


def db_fetch_transactions():
    # Fetches all transaction records joined with item names.
    # Returns a list of tuples: [(trans_id, name, date, qty_change, purpose), ...]

    conn   = get_connection()                  # open connection
    cursor = conn.cursor()                     # create cursor

    cursor.execute("""
        SELECT t.trans_id,
               i.name,
               t.date,
               t.qty_change,
               t.purpose
        FROM   Transactions t
        JOIN   Items i ON t.item_id = i.item_id
        ORDER  BY t.trans_id DESC
    """)                                       # JOIN: combines Transactions and Items on matching item_id
    # ORDER BY trans_id DESC shows the newest transaction first

    rows = cursor.fetchall()                   # fetch all rows as a list of tuples
    cursor.close()                             # close cursor
    conn.close()                              # close connection
    return rows                                # return the list to the GUI function that called this


# ----------------------------------------------------------------
# SECTION 3 : GUI ACTION FUNCTIONS
# These functions are called directly by tkinter Button widgets.
# Each one reads from Entry widgets, calls a backend function,
# shows a messagebox result, and refreshes the Treeview table.
# ----------------------------------------------------------------

def action_add_item(entry_name, entry_qty, tree_inventory):
    # Called when the user clicks the "Add Item" button.
    # Reads the Entry fields, validates them, calls db_add_item(),
    # shows a popup result, and refreshes the inventory table.

    name = entry_name.get().strip()            # .get() reads the current text from the Entry widget; .strip() removes spaces
    if not name:                               # check: user left the name field blank
        messagebox.showerror("Error", "Item name cannot be empty.")  # show a red error popup
        return                                 # stop here — do not proceed to database

    qty_str = entry_qty.get().strip()          # read the quantity Entry field text
    if not qty_str.isdigit():                  # isdigit() checks every character is a number (0-9)
        messagebox.showerror("Error", "Quantity must be a whole number.")  # show error popup
        return                                 # stop here

    qty = int(qty_str)                         # convert the string "25" into the integer 25

    db_add_item(name, qty)                     # call the backend function to INSERT into Items table

    messagebox.showinfo("Success", f"Item '{name}' added with quantity {qty}.")
    # ^ showinfo() shows a green info popup with the success message

    entry_name.delete(0, tk.END)               # clear the name Entry field (0 = start, tk.END = end of text)
    entry_qty.delete(0, tk.END)                # clear the qty Entry field

    refresh_inventory(tree_inventory)          # reload the Treeview table so the new item appears immediately


def action_issue_item(entry_id, entry_qty, entry_purpose, tree_inventory, tree_transactions):
    # Called when the user clicks the "Issue" button.
    # Reads Entry fields, calls db_issue_item(), shows result, refreshes both tables.

    id_str  = entry_id.get().strip()           # read item ID Entry field
    qty_str = entry_qty.get().strip()          # read quantity Entry field
    purpose = entry_purpose.get().strip()      # read purpose Entry field

    if not id_str.isdigit() or not qty_str.isdigit():  # validate both inputs are numbers
        messagebox.showerror("Error", "Item ID and Quantity must be whole numbers.")
        return                                 # stop if validation fails

    success, msg = db_issue_item(int(id_str), int(qty_str), purpose)
    # ^ calls the backend issue function; it returns (True/False, message string)

    if success:                                # if db_issue_item returned True (operation worked)
        messagebox.showinfo("Success", msg)    # show a green success popup
        entry_id.delete(0, tk.END)             # clear the ID field
        entry_qty.delete(0, tk.END)            # clear the qty field
        entry_purpose.delete(0, tk.END)        # clear the purpose field
        refresh_inventory(tree_inventory)      # reload inventory Treeview to show updated stock
        refresh_transactions(tree_transactions) # reload transaction Treeview to show the new log entry
    else:                                      # db_issue_item returned False (something went wrong)
        messagebox.showerror("Error", msg)     # show a red error popup with the reason


def action_restock_item(entry_id, entry_qty, entry_purpose, tree_inventory, tree_transactions):
    # Called when the user clicks the "Restock" button.
    # Reads Entry fields, calls db_restock_item(), shows result, refreshes both tables.

    id_str  = entry_id.get().strip()           # read item ID Entry field
    qty_str = entry_qty.get().strip()          # read quantity Entry field
    purpose = entry_purpose.get().strip()      # read purpose Entry field

    if not id_str.isdigit() or not qty_str.isdigit():  # validate both are numbers
        messagebox.showerror("Error", "Item ID and Quantity must be whole numbers.")
        return                                 # stop if invalid

    success, msg = db_restock_item(int(id_str), int(qty_str), purpose)
    # ^ calls the backend restock function; returns (True/False, message string)

    if success:                                # operation succeeded
        messagebox.showinfo("Success", msg)    # green popup
        entry_id.delete(0, tk.END)             # clear fields
        entry_qty.delete(0, tk.END)            # clear fields
        entry_purpose.delete(0, tk.END)        # clear fields
        refresh_inventory(tree_inventory)      # reload inventory table
        refresh_transactions(tree_transactions) # reload transaction table
    else:                                      # operation failed (item not found, etc.)
        messagebox.showerror("Error", msg)     # red error popup


def action_low_stock(entry_threshold, tree_inventory):
    # Called when the user clicks the "Show Low Stock" button.
    # Reads the threshold Entry, calls db_fetch_inventory(threshold),
    # and reloads the inventory Treeview with only low-stock items.

    t_str = entry_threshold.get().strip()      # read the threshold Entry field text
    if not t_str.isdigit():                    # check it's a number
        messagebox.showerror("Error", "Threshold must be a whole number.")
        return                                 # stop if invalid

    threshold = int(t_str)                     # convert string to integer
    rows = db_fetch_inventory(threshold)       # fetch only items with total_qty <= threshold

    load_treeview(tree_inventory, rows)        # load the filtered rows into the Treeview

    if not rows:                               # if no items matched the threshold
        messagebox.showinfo("Low Stock", f"No items at or below {threshold} units.")
        # ^ inform the user that everything is adequately stocked


def action_show_all(tree_inventory):
    # Called when the user clicks the "Show All Items" button.
    # Removes the low-stock filter and shows the complete inventory again.

    refresh_inventory(tree_inventory)          # call the standard full-refresh function


# ----------------------------------------------------------------
# SECTION 4 : TREEVIEW HELPER FUNCTIONS
# Treeview is the ttk widget that displays data in a table with
# rows and columns — like a spreadsheet inside the GUI window.
# ----------------------------------------------------------------

def load_treeview(tree, rows):
    # Clears all existing rows from a Treeview widget and loads new rows.
    # 'tree'  = the Treeview widget object
    # 'rows'  = a list of tuples fetched from MariaDB

    for item in tree.get_children():           # get_children() returns all current row IDs in the Treeview
        tree.delete(item)                      # delete each existing row one by one (clears the table)

    for row in rows:                           # loop through each tuple in the rows list from the database
        tree.insert("", tk.END, values=row)    # insert() adds a new row at the bottom ("" = no parent; it's a top-level row)
        # values=row   : the tuple values fill the columns in order
        # tk.END       : places the new row at the very end of the table


def refresh_inventory(tree_inventory):
    # Fetches ALL inventory items from MariaDB and reloads the inventory Treeview.
    # This is called after any add/issue/restock operation to keep the display live.

    rows = db_fetch_inventory()                # call the backend with no threshold (fetch everything)
    load_treeview(tree_inventory, rows)        # clear the old rows and insert the fresh data


def refresh_transactions(tree_transactions):
    # Fetches ALL transaction records from MariaDB and reloads the transaction Treeview.
    # Called after every issue or restock so the log updates instantly.

    rows = db_fetch_transactions()             # call the backend to get all transaction rows
    load_treeview(tree_transactions, rows)     # clear and reload the Treeview


# ----------------------------------------------------------------
# SECTION 5 : GUI BUILDER FUNCTIONS
# These functions create each visual section (tab/frame) of the
# window using tkinter widgets. They return any widgets that
# action functions will need to read (Entry fields, Treeviews).
# ----------------------------------------------------------------

def build_add_item_frame(parent, tree_inventory):
    # Builds the "Add Item" section inside the given parent frame.
    # Returns nothing — the button's command is wired up internally.

    frame = tk.LabelFrame(parent, text="Add New Lab Item", padx=10, pady=10, font=("Arial", 11, "bold"))
    # ^ LabelFrame is a container widget with a visible border and a label title

    frame.pack(fill="x", padx=15, pady=10)    # pack() places the frame in its parent; fill="x" stretches it horizontally

    tk.Label(frame, text="Item Name:", font=("Arial", 10)).grid(row=0, column=0, sticky="w", pady=4)
    # ^ Label widget displays static text; grid() places it in row 0, column 0 of the frame's grid layout
    # sticky="w" means align to the west (left) edge of its cell

    entry_name = tk.Entry(frame, width=30, font=("Arial", 10))  # Entry is a single-line text input box
    entry_name.grid(row=0, column=1, padx=10, pady=4)           # place it in row 0, column 1

    tk.Label(frame, text="Starting Qty:", font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=4)
    # ^ another static label for the quantity field

    entry_qty = tk.Entry(frame, width=10, font=("Arial", 10))   # narrower Entry for the number
    entry_qty.grid(row=1, column=1, sticky="w", padx=10, pady=4) # place in row 1, column 1

    btn = tk.Button(                           # Button widget — clicking it triggers a function
        frame,
        text    = "➕ Add Item",               # label text shown on the button face
        font    = ("Arial", 10, "bold"),
        bg      = "#4CAF50",                   # background colour (green) for a positive action
        fg      = "white",                     # text colour on the button
        command = lambda: action_add_item(entry_name, entry_qty, tree_inventory)
        # command= tells tkinter WHICH function to call when the button is clicked
        # lambda: wraps the call so we can pass arguments (entry_name, etc.) to the function
        # Without lambda, action_add_item() would run immediately at startup instead of on click
    )
    btn.grid(row=2, column=1, sticky="w", padx=10, pady=8)       # place the button in row 2


def build_issue_restock_frame(parent, tree_inventory, tree_transactions):
    # Builds the "Issue / Restock" section.
    # Both operations share the same input fields (ID, Qty, Purpose).

    frame = tk.LabelFrame(parent, text="Issue / Restock Item", padx=10, pady=10, font=("Arial", 11, "bold"))
    frame.pack(fill="x", padx=15, pady=10)    # stretch the frame horizontally across the window

    tk.Label(frame, text="Item ID:", font=("Arial", 10)).grid(row=0, column=0, sticky="w", pady=4)
    entry_id = tk.Entry(frame, width=10, font=("Arial", 10))      # Entry for the item_id number
    entry_id.grid(row=0, column=1, sticky="w", padx=10, pady=4)

    tk.Label(frame, text="Quantity:", font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=4)
    entry_qty = tk.Entry(frame, width=10, font=("Arial", 10))     # Entry for how many units
    entry_qty.grid(row=1, column=1, sticky="w", padx=10, pady=4)

    tk.Label(frame, text="Purpose:", font=("Arial", 10)).grid(row=2, column=0, sticky="w", pady=4)
    entry_purpose = tk.Entry(frame, width=30, font=("Arial", 10)) # Entry for the reason/purpose text
    entry_purpose.grid(row=2, column=1, padx=10, pady=4)

    btn_issue = tk.Button(
        frame,
        text    = "📤 Issue Item",             # label on the Issue button
        font    = ("Arial", 10, "bold"),
        bg      = "#f44336",                   # red background — signals items leaving stock
        fg      = "white",
        command = lambda: action_issue_item(entry_id, entry_qty, entry_purpose, tree_inventory, tree_transactions)
        # lambda passes all needed widget references to action_issue_item when the button is clicked
    )
    btn_issue.grid(row=3, column=1, sticky="w", padx=10, pady=5)  # place Issue button in row 3

    btn_restock = tk.Button(
        frame,
        text    = "📥 Restock Item",           # label on the Restock button
        font    = ("Arial", 10, "bold"),
        bg      = "#2196F3",                   # blue background — signals items entering stock
        fg      = "white",
        command = lambda: action_restock_item(entry_id, entry_qty, entry_purpose, tree_inventory, tree_transactions)
        # same Entry widgets shared between Issue and Restock — user fills them, then clicks whichever applies
    )
    btn_restock.grid(row=3, column=2, sticky="w", padx=5, pady=5) # place Restock button in row 3, column 2


def build_inventory_frame(parent):
    # Builds the "Inventory Table" section with a Treeview and Low Stock filter.
    # Returns the Treeview widget so other functions can refresh it.

    frame = tk.LabelFrame(parent, text="📦 Live Inventory", padx=10, pady=10, font=("Arial", 11, "bold"))
    frame.pack(fill="both", expand=True, padx=15, pady=10)
    # fill="both" and expand=True makes this frame grow to fill remaining window space

    # --- Low Stock Filter bar ---
    filter_bar = tk.Frame(frame)               # Frame is an invisible container to group widgets in a row
    filter_bar.pack(fill="x", pady=(0, 8))     # place the filter bar at the top of the inventory section

    tk.Label(filter_bar, text="Low Stock Threshold:", font=("Arial", 10)).pack(side="left")
    # pack(side="left") places widgets left-to-right inside filter_bar

    entry_threshold = tk.Entry(filter_bar, width=6, font=("Arial", 10))  # small Entry for the threshold number
    entry_threshold.pack(side="left", padx=6)  # pack to the left, next to the label

    # Treeview widget — will be created below; we pre-declare it here so the lambda can reference it
    # (Python closures capture the variable name, not its current value at this point)
    tree_holder = [None]                       # list used as a mutable container so the lambda can reference tree after it's built

    btn_low = tk.Button(
        filter_bar,
        text    = "🔴 Show Low Stock",
        font    = ("Arial", 10, "bold"),
        bg      = "#FF9800",                   # orange — warning colour
        fg      = "white",
        command = lambda: action_low_stock(entry_threshold, tree_holder[0])
        # tree_holder[0] will be the Treeview object once it's assigned below
    )
    btn_low.pack(side="left", padx=4)          # place the button to the right of the threshold entry

    btn_all = tk.Button(
        filter_bar,
        text    = "🟢 Show All",
        font    = ("Arial", 10, "bold"),
        bg      = "#607D8B",                   # grey-blue — neutral "reset" colour
        fg      = "white",
        command = lambda: action_show_all(tree_holder[0])
        # clicking this removes the low-stock filter and shows everything again
    )
    btn_all.pack(side="left", padx=4)          # place next to the low-stock button

    # --- Inventory Treeview (the actual table) ---
    columns = ("ID", "Item Name", "Qty in Stock")  # column header names as a tuple
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)
    # Treeview: displays tabular data with sortable columns
    # columns=     : defines the logical column identifiers
    # show="headings": hide the default empty first column (shows only our named columns)
    # height=12    : shows 12 rows before the scrollbar activates

    for col in columns:                        # loop through each column name
        tree.heading(col, text=col)            # heading() sets the displayed title for each column header
        tree.column(col, width=180, anchor="center")  # column() sets the pixel width and text alignment

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    # Scrollbar widget — connected to the Treeview's vertical scroll position
    tree.configure(yscrollcommand=scrollbar.set)
    # yscrollcommand links the Treeview's scroll position to the Scrollbar's position
    tree.bind("<Button-4>", lambda event: tree.yview_scroll(-1, "units"))  # mouse wheel up on Linux
    tree.bind("<Button-5>", lambda event: tree.yview_scroll(1, "units"))   # mouse wheel down on Linux
    tree.bind("<MouseWheel>", lambda event: tree.yview_scroll(int(-1 * (event.delta / 120)), "units"))  # mouse wheel on Windows/Mac

    tree.pack(side="left", fill="both", expand=True)   # place Treeview on the left, expanding to fill space
    scrollbar.pack(side="right", fill="y")             # place Scrollbar on the right edge, full height

    tree_holder[0] = tree                      # store the actual Treeview object in the holder list

    return tree                                # return the Treeview so callers can call refresh_inventory() on it


def build_transactions_frame(parent):
    # Builds the "Transaction History" section with a Treeview table.
    # Returns the Treeview widget so other functions can refresh it.

    frame = tk.LabelFrame(parent, text="📋 Transaction History", padx=10, pady=10, font=("Arial", 11, "bold"))
    frame.pack(fill="both", expand=True, padx=15, pady=10)
    # fill="both", expand=True: frame grows to use all available vertical space

    columns = ("TID", "Item Name", "Date", "Qty Change", "Purpose")  # column headers
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
    # height=10: shows 10 transaction rows before scrolling

    col_widths = {"TID": 60, "Item Name": 180, "Date": 110, "Qty Change": 100, "Purpose": 220}
    # dictionary mapping column name → pixel width; different widths for different data lengths

    for col in columns:                        # loop through each column name
        tree.heading(col, text=col)            # set the column header label
        tree.column(col, width=col_widths[col], anchor="center")  # set the column width from the dictionary

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    # vertical scrollbar linked to this Treeview's scroll position
    tree.configure(yscrollcommand=scrollbar.set)  # connect them so scrollbar moves with table
    tree.bind("<Button-4>", lambda event: tree.yview_scroll(-1, "units"))  # mouse wheel up on Linux
    tree.bind("<Button-5>", lambda event: tree.yview_scroll(1, "units"))   # mouse wheel down on Linux
    tree.bind("<MouseWheel>", lambda event: tree.yview_scroll(int(-1 * (event.delta / 120)), "units"))  # mouse wheel on Windows/Mac

    tree.pack(side="left", fill="both", expand=True)   # Treeview on the left
    scrollbar.pack(side="right", fill="y")             # Scrollbar on the right

    return tree                                # return the Treeview widget reference


# ----------------------------------------------------------------
# SECTION 6 : MAIN WINDOW BUILDER
# This function creates the root window, assembles all sections,
# and starts the tkinter event loop.
# ----------------------------------------------------------------

def build_main_window():
    # Creates the root application window and assembles the GUI tabs.
    # This is the main function that starts the tkinter event loop.

    root = tk.Tk()                             # Tk() creates the main application window
    root.title("School Lab Inventory Manager — CBSE Class 12 CS Project")  # sets window title

    root.geometry("800x650")                   # sets window size: 800 width x 650 height in pixels
    root.resizable(True, True)                 # allows resizing the window
    root.configure(bg="#f5f5f5")               # sets window background colour to light grey

    # --- Title Banner ---
    banner = tk.Label(
        root,
        text   = "🔬 School Lab Inventory Manager",   # heading text
        font   = ("Arial", 16, "bold"),
        bg     = "#1565C0",                    # dark blue background
        fg     = "white",                      # white text
        pady   = 10                            # vertical padding
    )
    banner.pack(fill="x")                      # stretches banner across top

    subtitle = tk.Label(
        root,
        text = "CBSE Class 12 Computer Science Project  |  Procedural Python + MariaDB",
        font = ("Arial", 9),
        bg   = "#1976D2",                      # slightly lighter blue
        fg   = "#E3F2FD"                       # very light blue text
    )
    subtitle.pack(fill="x")                    # places subtitle below banner

    # --- Notebook (Tabbed Interface) ---
    # ttk.Notebook creates simple, clean tabs — each section gets its own view.
    # This avoids complex window-level scrolling and fits perfectly on any screen.
    notebook = ttk.Notebook(root)              # creates the Notebook widget to hold tabs
    notebook.pack(fill="both", expand=True, padx=10, pady=10)  # stretches to fill remaining window space

    # --- Tab 1: Manage Items (Add / Issue / Restock) ---
    tab_manage = tk.Frame(notebook, bg="#f5f5f5")    # container frame for Tab 1
    notebook.add(tab_manage, text="  ✏️ Manage Items  ")  # adds Tab 1 to Notebook

    # --- Tab 2: Inventory Table ---
    tab_inventory = tk.Frame(notebook, bg="#f5f5f5")  # container frame for Tab 2
    notebook.add(tab_inventory, text="  📦 Live Inventory  ")  # adds Tab 2 to Notebook

    # --- Tab 3: Transaction History ---
    tab_transactions = tk.Frame(notebook, bg="#f5f5f5")  # container frame for Tab 3
    notebook.add(tab_transactions, text="  📋 Transactions  ")  # adds Tab 3 to Notebook

    # --- Build Treeview tables in their respective tabs ---
    tree_inventory = build_inventory_frame(tab_inventory)  # places inventory table in Tab 2
    tree_transactions = build_transactions_frame(tab_transactions)  # places transaction table in Tab 3

    # --- Build input forms in Tab 1 ---
    build_add_item_frame(tab_manage, tree_inventory)  # puts Add Item form in Tab 1
    build_issue_restock_frame(tab_manage, tree_inventory, tree_transactions)  # puts Issue/Restock form in Tab 1

    # --- Initial data load: populate tables from MariaDB ---
    refresh_inventory(tree_inventory)          # fills inventory table with current database records
    refresh_transactions(tree_transactions)    # fills transaction table with current database records

    root.mainloop()                            # starts tkinter event loop to process user interaction


# ----------------------------------------------------------------
# SECTION 7 : PROGRAM ENTRY POINT
# ----------------------------------------------------------------

if __name__ == "__main__":                     # only run when this file is executed directly (not imported)
    build_main_window()                        # call the main window builder to launch the GUI
