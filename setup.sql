-- ============================================================
--  setup.sql  |  School Lab Inventory Manager
--  CBSE Class 12 Computer Science Project
--  Run this file ONCE in MySQL to initialise the database.
-- ============================================================

-- Step 1: Create the database if it does not already exist.
CREATE DATABASE IF NOT EXISTS LabInventory;

-- Step 2: Switch to the LabInventory database so all
--         subsequent statements apply to it.
USE LabInventory;

-- ============================================================
-- TABLE 1 : Items
--   Stores the master list of every lab item.
-- ============================================================
CREATE TABLE IF NOT EXISTS Items (
    item_id   INT          AUTO_INCREMENT PRIMARY KEY,
    -- item_id  : unique number assigned automatically by MySQL
    --            for every new row; cannot be NULL.

    name      VARCHAR(100) NOT NULL,
    -- name     : the descriptive name of the lab item
    --            (e.g. "Beaker 250ml"); maximum 100 characters.

    total_qty INT          NOT NULL DEFAULT 0
    -- total_qty: running count of how many units are
    --            currently in stock; starts at 0 if not given.
);

-- ============================================================
-- TABLE 2 : Transactions
--   Records every issue or restock event as a separate row.
-- ============================================================
CREATE TABLE IF NOT EXISTS Transactions (
    trans_id   INT          AUTO_INCREMENT PRIMARY KEY,
    -- trans_id : unique serial number for each transaction log.

    item_id    INT          NOT NULL,
    -- item_id  : links this transaction to a row in Items;
    --            cannot be NULL.

    date       DATE         NOT NULL,
    -- date     : the calendar date on which the event occurred;
    --            stored in YYYY-MM-DD format by MySQL.

    qty_change INT          NOT NULL,
    -- qty_change: positive value = restock (items added),
    --             negative value = issue (items taken out).

    purpose    VARCHAR(255),
    -- purpose  : optional free-text reason for the transaction
    --            (e.g. "Class 11B chemistry lab").

    -- Foreign key constraint: item_id here MUST match a valid
    -- item_id that already exists in the Items table.
    -- ON DELETE CASCADE means: if an Item is deleted, all its
    -- related transaction rows are automatically deleted too.
    CONSTRAINT fk_item
        FOREIGN KEY (item_id)
        REFERENCES Items(item_id)
        ON DELETE CASCADE
);

-- ============================================================
-- Confirm setup is complete.
-- ============================================================
SELECT 'Database and tables created successfully.' AS Status;
