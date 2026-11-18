-- grant_access.sql
-- Run this ONCE with: sudo mariadb < grant_access.sql
-- This grants your Linux user full access to the LabInventory database.

-- Create the 'adhithyan' user using unix_socket authentication.
-- unix_socket means: MariaDB checks the Linux OS username instead of a password.
CREATE USER IF NOT EXISTS 'adhithyan'@'localhost' IDENTIFIED VIA unix_socket;

-- Give this user full control over the LabInventory database only.
GRANT ALL PRIVILEGES ON LabInventory.* TO 'adhithyan'@'localhost';

-- Apply the changes immediately.
FLUSH PRIVILEGES;

-- Confirm it worked.
SELECT 'Access granted to adhithyan for LabInventory.' AS Status;
