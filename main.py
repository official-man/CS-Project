# ================================================================
#  main.py | School Lab Inventory Manager (Application Launcher)
#  CBSE Class 12 Computer Science Project
#
#  Architecture : Purely Procedural (no classes, zero OOP)
#  Platforms    : Archcraft Linux & Windows (Cross-Platform)
#
#  HOW TO RUN:
#    python main.py             (Interactive Launcher)
#    python terminal_app.py     (Direct Terminal Version)
#    python gui_app.py          (Direct Tkinter Desktop GUI Version)
# ================================================================

import terminal_app                           # imports procedural terminal interface module
import gui_app                                # imports procedural tkinter GUI desktop module


def main():
    # Provides an interactive entry point allowing the user
    # to choose between the GUI desktop app and the Terminal menu.

    print("=" * 52)                            # prints banner top border
    print("       🔬 SCHOOL LAB INVENTORY MANAGER")  # prints project title
    print("       CBSE Class 12 Computer Science Project")  # prints curriculum banner
    print("=" * 52)                            # prints separator line
    print("  1. 🖥️  Launch Desktop GUI (gui_app.py)")  # option 1
    print("  2. 📟 Launch Terminal Menu (terminal_app.py)")  # option 2
    print("  3. ❌ Exit")                      # option 3
    print("=" * 52)                            # prints bottom menu border

    choice = input("Select interface (1-3, default 1): ").strip()  # reads user choice

    if choice in ("1", ""):                    # default or option 1 launches Tkinter GUI
        print("\nLaunching Desktop GUI...")    # status message
        gui_app.build_main_window()            # launches Tkinter desktop interface
    elif choice == "2":                        # option 2 launches terminal menu
        terminal_app.main()                    # launches procedural terminal menu loop
    elif choice == "3":                        # option 3 exits launcher
        print("\nGoodbye!\n")                  # prints farewell message
    else:                                      # handles invalid choices gracefully
        print("\nInvalid choice. Launching Desktop GUI by default...")
        gui_app.build_main_window()            # launches GUI by default


if __name__ == "__main__":                     # ensures script runs only when directly executed
    main()                                     # invokes launcher function
