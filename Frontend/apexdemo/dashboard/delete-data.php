<?php
// Start the session
session_start();

// Check if the admin is logged in
if (!isset($_SESSION['admin_id'])) {
    // If the session variable 'admin_id' is not set, redirect to login.php
    header("Location: auth/login.php");
    exit();
}

// Include the database connection file
include '../db(1).php';

if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    // Get the table name and ID of the record to be deleted
    $table = $_POST['table'];
    $id = $_POST['id'];

    // Validate table name to avoid SQL injection
    $allowed_tables = ['salesdata']; // Add all the tables you want to allow
    if (!in_array($table, $allowed_tables)) {
        header("Location: {$_SERVER['HTTP_REFERER']}?message=Invalid+table+name");
        exit();
    }

    // Prepare the SQL statement to delete the record
    $sql = "DELETE FROM $table WHERE id = ?";

    // Prepare the statement
    if ($stmt = $conn->prepare($sql)) {
        // Bind the ID parameter
        $stmt->bind_param("i", $id);

        // Execute the statement
        if ($stmt->execute()) {
            // Redirect to the previous page with a success message
            header("Location: {$_SERVER['HTTP_REFERER']}?message=Record+deleted+successfully");
        } else {
            // Redirect to the previous page with an error message
            header("Location: {$_SERVER['HTTP_REFERER']}?message=Error+deleting+record");
        }

        // Close the statement
        $stmt->close();
    }

    // Close the database connection
    $conn->close();
} else {
    // If the request method is not POST, redirect back to the previous page
    header("Location: {$_SERVER['HTTP_REFERER']}");
}
