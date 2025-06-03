
create database game_1


USE game_1;

-- Users table
CREATE TABLE Users (
    UserId      INT IDENTITY(1,1) PRIMARY KEY,
    Name        VARCHAR(100) NOT NULL,
    Email       VARCHAR(150) NOT NULL UNIQUE,
    Phone       VARCHAR(20) NULL UNIQUE,
    Role        VARCHAR(20) NOT NULL
);

USE game_1;

-- Games table
CREATE TABLE Games (
    GameId      INT IDENTITY(1,1) PRIMARY KEY,
    GameTitle   VARCHAR(200) NOT NULL UNIQUE,
    Description VARCHAR(MAX) NULL,
    Genre       VARCHAR(50) NULL,
    Price       DECIMAL(10,2) NOT NULL,
    Platform    VARCHAR(50) NULL
);

-- Orders table (TotalAmount allows NULL, calculated by trigger)
CREATE TABLE Orders (
    OrderId      INT IDENTITY(1,1) PRIMARY KEY,
    UserId       INT NOT NULL,
    OrderDate    DATE NOT NULL DEFAULT GETDATE(),
    OrderTime    TIME NOT NULL DEFAULT CONVERT(TIME, GETDATE()),
    Status       VARCHAR(30) NOT NULL,
    TotalAmount  DECIMAL(12,2) NULL, -- Total amount will be calculated automatically by the trigger
    FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE
);

USE game_1;

-- Payments table
CREATE TABLE Payments (
    PaymentId      INT IDENTITY(1,1) PRIMARY KEY,
    OrderId        INT NOT NULL UNIQUE,
    PaymentDate    DATE NOT NULL DEFAULT GETDATE(),
    PaymentTime    TIME NOT NULL DEFAULT CONVERT(TIME, GETDATE()),
    PaymentMethod  NVARCHAR(50) NOT NULL,
    PaymentStatus  NVARCHAR(30) NOT NULL,
    FOREIGN KEY (OrderId) REFERENCES Orders(OrderId) ON DELETE CASCADE
);

-- Inventory table
CREATE TABLE Inventory (
    InventoryId   INT IDENTITY(1,1) PRIMARY KEY,
    GameId        INT NOT NULL,
    StockQuantity INT NOT NULL DEFAULT 0,
    FOREIGN KEY (GameId) REFERENCES Games(GameId) ON DELETE CASCADE
);

use game_1
select * from Cart;
-- Cart table
CREATE TABLE Cart (
    CartId       INT IDENTITY(1,1) PRIMARY KEY,
    OrderId      INT NULL,
    UserId       INT NOT NULL,
    GameId       INT NOT NULL,
    Quantity     INT NOT NULL DEFAULT 1 CHECK (Quantity > 0),
    TotalAmount  DECIMAL(12,2) NULL CHECK (TotalAmount >= 0),  -- Allow NULL, will be calculated by the trigger
    FOREIGN KEY (OrderId) REFERENCES Orders(OrderId) ON DELETE NO ACTION,
    FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE,
    FOREIGN KEY (GameId) REFERENCES Games(GameId) ON DELETE CASCADE
);


USE game_1;
go
-- Trigger to auto-calculate Cart TotalAmount when an item is added to the Cart
CREATE TRIGGER UpdateCartTotalAmount
ON Cart
AFTER INSERT
AS
BEGIN
    UPDATE c
    SET c.TotalAmount = g.Price * c.Quantity
    FROM Cart c
    JOIN Games g ON c.GameId = g.GameId
    WHERE c.CartId IN (SELECT CartId FROM inserted);
END;

use game_1
go
-- Trigger to update the Order TotalAmount when Cart items are added/updated
use game_1
go
CREATE TRIGGER UpdateOrderTotal
ON Cart
AFTER INSERT, UPDATE
AS
BEGIN
    -- Update the TotalAmount for each affected Order
    UPDATE o
    SET o.TotalAmount = (
        SELECT SUM(c.TotalAmount)
        FROM Cart c
        WHERE c.OrderId = o.OrderId
    )
    FROM Orders o
    WHERE o.OrderId IN (SELECT DISTINCT OrderId FROM inserted WHERE OrderId IS NOT NULL);
END;

use game_1
-- Query to check the inserted data and calculate TotalAmount
SELECT c.CartId, c.OrderId, c.UserId, c.GameId, c.Quantity, c.TotalAmount, g.Price AS GamePrice
FROM Cart c
JOIN Games g ON c.GameId = g.GameId;

USE GAME_1
SELECT * FROM Orders

use game_1
select *from Cart
USE game_1;

DELETE FROM Orders WHERE UserId = 2;
 
 use game_1
 go
 CREATE TRIGGER ReduceInventoryOnAddToCart
ON Cart
AFTER INSERT
AS
BEGIN
    UPDATE i
    SET i.StockQuantity = i.StockQuantity - c.Quantity
    FROM Inventory i
    JOIN inserted c ON i.GameId = c.GameId
    WHERE i.StockQuantity >= c.Quantity;
END;

USE game_1;
GO

USE game_1;
GO

Create PROCEDURE add_game_item
    @UserId INT,
    @GameTitle VARCHAR(200),
    @Description VARCHAR(MAX),
    @Genre VARCHAR(50),
    @Price DECIMAL(10,2),
    @Platform VARCHAR(50)
AS
BEGIN
    IF EXISTS (
        SELECT 1 FROM Users WHERE UserId = @UserId AND Role = 'admin'
    )
    BEGIN
        -- Insert into Games
        INSERT INTO Games (GameTitle, Description, Genre, Price, Platform)
        VALUES (@GameTitle, @Description, @Genre, @Price, @Platform);

        -- Insert into Inventory with StockQuantity = 1 (get GameId using SCOPE_IDENTITY)
        DECLARE @NewGameId INT = SCOPE_IDENTITY();

        INSERT INTO Inventory (GameId, StockQuantity)
        VALUES (@NewGameId, 1);
    END
    ELSE
    BEGIN
        RAISERROR('Permission denied. Only admins can add games.', 16, 1);
    END
END;


use game_1
drop procedure add_game_item;


USE game_1;
GO

CREATE PROCEDURE remove_user
    @AdminUserId INT,  -- Admin ID to check role
    @UserIdToRemove INT  -- ID of the user to remove
AS
BEGIN
    IF EXISTS (
        SELECT 1 FROM Users WHERE UserId = @AdminUserId AND Role = 'admin'
    )
    BEGIN
        -- Delete the user from Users table
        DELETE FROM Users WHERE UserId = @UserIdToRemove;
    END
    ELSE
    BEGIN
        RAISERROR('Permission denied. Only admins can remove users.', 16, 1);
    END
END;




USE game_1;
GO

CREATE PROCEDURE remove_inventory_quantity
    @GameId INT,      -- Game ID to update
    @Quantity INT     -- Quantity to remove
AS
BEGIN
    DECLARE @CurrentStock INT;

    -- Get the current stock quantity for the game
    SELECT @CurrentStock = StockQuantity 
    FROM Inventory 
    WHERE GameId = @GameId;

    -- Check if the current stock is enough to remove the requested quantity
    IF @CurrentStock >= @Quantity
    BEGIN
        -- Update the inventory by reducing the specified quantity
        UPDATE Inventory
        SET StockQuantity = StockQuantity - @Quantity
        WHERE GameId = @GameId;
    END
    ELSE
    BEGIN
        -- Raise error if the requested removal quantity exceeds the available stock
        RAISERROR('Not enough stock available to remove. Current stock: %d', 16, 1, @CurrentStock);
    END
END;

-- to delete games


USE game_1;
GO

CREATE PROCEDURE remove_game
    @GameId INT  -- Game ID to be removed
AS
BEGIN
    IF EXISTS (SELECT 1 FROM Games WHERE GameId = @GameId) 
    BEGIN
        DELETE FROM Games WHERE GameId = @GameId;
    END
    ELSE
    BEGIN
        RAISERROR('Cannot remove game. Game is linked to inventory, cart', 16, 1);
    END
END;

use game_1
 SELECT g.GameId, g.GameTitle, i.StockQuantity
        FROM Games g
        JOIN Inventory i ON g.GameId = i.GameId
        ORDER BY g.GameTitle



		
USE game_1;
GO

CREATE PROCEDURE add_inventory_quantity
    @GameId INT,      -- Game ID to update
    @Quantity INT     -- Quantity to add
AS
BEGIN
    -- Check if the game exists in inventory
    IF EXISTS (SELECT 1 FROM Inventory WHERE GameId = @GameId)
    BEGIN
        -- Increase the stock quantity
        UPDATE Inventory
        SET StockQuantity = StockQuantity + @Quantity
        WHERE GameId = @GameId;
    END
    ELSE
    BEGIN
        -- Optionally, handle case where GameId does not exist
        RAISERROR('Game with ID %d does not exist in inventory.', 16, 1, @GameId);
    END
END;


use game_1
CREATE INDEX UserDetails ON Users(UserId,Name,Role);


USE game_1;
GO

ALTER TABLE Users
ADD Password VARCHAR(100) NOT NULL DEFAULT 'changeme';  -- You can hash passwords later for real apps
UPDATE Users
SET Password = 'admin123'
WHERE Name = 'Anwaar';  -- Set for admin

UPDATE Users
SET Password = 'user123'
WHERE Role = 'customer';  -- Set default for all customers

ALTER PROCEDURE add_game_item
    @AdminId INT,
    @AdminPassword VARCHAR(100),
    @GameTitle VARCHAR(200),
    @Description VARCHAR(MAX),
    @Genre VARCHAR(50),
    @Price DECIMAL(10,2),
    @Platform VARCHAR(50)
AS
BEGIN
    -- Verify admin credentials
    IF EXISTS (
        SELECT 1
        FROM Users
        WHERE UserId = @AdminId AND Role = 'admin' AND Password = @AdminPassword
    )
    BEGIN
        -- Check if the game title already exists to avoid UNIQUE constraint violation
        IF EXISTS (
            SELECT 1 FROM Games WHERE GameTitle = @GameTitle
        )
        BEGIN
            RAISERROR('Game title already exists.', 16, 1);
            RETURN;
        END

        -- Insert into Games
        INSERT INTO Games (GameTitle, Description, Genre, Price, Platform)
        VALUES (@GameTitle, @Description, @Genre, @Price, @Platform);

        -- Get the newly inserted GameId
        DECLARE @NewGameId INT = SCOPE_IDENTITY();

        -- Insert into Inventory with initial StockQuantity = 1
        INSERT INTO Inventory (GameId, StockQuantity)
        VALUES (@NewGameId, 1);

        PRINT 'Game added successfully.';
    END
    ELSE
    BEGIN
        RAISERROR('Permission denied. Invalid admin credentials.', 16, 1);
    END
END;


ALTER PROCEDURE remove_user
    @AdminId INT,
    @AdminPassword VARCHAR(100),
    @UserIdToRemove INT
AS
BEGIN
    -- Check if the requesting user is an admin and the password is correct
    IF EXISTS (
        SELECT 1
        FROM Users
        WHERE UserId = @AdminId AND Role = 'admin' AND Password = @AdminPassword
    )
    BEGIN
        IF EXISTS (
            SELECT 1
            FROM Users
            WHERE UserId = @UserIdToRemove
        )
        BEGIN
            DELETE FROM Users
            WHERE UserId = @UserIdToRemove;

            PRINT 'User removed successfully.';
        END
        ELSE
        BEGIN
            PRINT 'User not found.';
        END
    END
    ELSE
    BEGIN
        RAISERROR('Permission denied. Invalid admin credentials.', 16, 1);
    END
END;


use game_1
DROP TRIGGER IF EXISTS ReduceInventoryOnAddToCart
use game_1
select * from users;

update users
set Role = 'customer'
where Email = 'luqman@example.com'

UPDATE Users
SET Password = 'user123'
WHERE Name = 'Luqman';  -- Set for admin

USE game_1;
GO

-- Add ImageURL column to Games table
ALTER TABLE Games
ADD ImageURL VARCHAR(500) NULL;

USE game_1;
GO

USE game_1;
GO

ALTER PROCEDURE add_game_item
    @AdminId INT,
    -- Removed @AdminPassword VARCHAR(100),
    @GameTitle VARCHAR(200),
    @Description VARCHAR(MAX),
    @Genre VARCHAR(50),
    @Price DECIMAL(10,2),
    @Platform VARCHAR(50),
    @ImageURL VARCHAR(500)
AS
BEGIN
    -- Verify that the UserId has the 'admin' role
    IF EXISTS (
        SELECT 1
        FROM Users
        WHERE UserId = @AdminId AND Role = 'admin'
    )
    BEGIN
        -- Check if the game title already exists to avoid UNIQUE constraint violation
        IF EXISTS (
            SELECT 1 FROM Games WHERE GameTitle = @GameTitle
        )
        BEGIN
            RAISERROR('Game title already exists.', 16, 1);
            RETURN;
        END

        -- Insert into Games
        INSERT INTO Games (GameTitle, Description, Genre, Price, Platform, ImageURL)
        VALUES (@GameTitle, @Description, @Genre, @Price, @Platform, @ImageURL);

        -- Get the newly inserted GameId
        DECLARE @NewGameId INT = SCOPE_IDENTITY();

        -- Insert into Inventory with initial StockQuantity = 1
        INSERT INTO Inventory (GameId, StockQuantity)
        VALUES (@NewGameId, 1);

        PRINT 'Game added successfully.';
    END
    ELSE
    BEGIN
        -- This error will now only occur if the user is not found or not an admin
        RAISERROR('Permission denied. User is not authorized to add games.', 16, 1);
    END
END;

select*from Users;
SELECT * FROM Users WHERE Email IS NULL OR Phone IS NULL;
DELETE FROM Users WHERE Email IS NULL OR Phone IS NULL;


ALTER PROCEDURE remove_user
    @AdminId INT,
    @AdminPassword VARCHAR(100),
    @UserIdToRemove INT
AS
BEGIN
    -- Check if the requesting user is an admin and the password is correct
    IF EXISTS (
        SELECT 1
        FROM Users
        WHERE UserId = @AdminId AND Role = 'admin' AND Password = @AdminPassword
    )
    BEGIN
        -- Check if the user exists
        IF EXISTS (
            SELECT 1
            FROM Users
            WHERE UserId = @UserIdToRemove
        )
        BEGIN
            -- Just delete the user; ON DELETE CASCADE will handle Cart and Orders
            DELETE FROM Users
            WHERE UserId = @UserIdToRemove;

            PRINT 'User removed successfully.';
        END
        ELSE
        BEGIN
            PRINT 'User not found.';
        END
    END
    ELSE
    BEGIN
        RAISERROR('Permission denied. Invalid admin credentials.', 16, 1);
    END
END;