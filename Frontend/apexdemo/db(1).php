<?php
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "u840048117_Apex_demo";

// Create connection
$conn = new mysqli($servername, $username,"", $dbname);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Set the character set to UTF-8 (optional)
$conn->set_charset("utf8");

?>