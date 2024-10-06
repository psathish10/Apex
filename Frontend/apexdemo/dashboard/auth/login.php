<?php
// Include the database connection file
include '../../db(1).php';
session_start();

if (!empty($_SESSION)) {
  // Unset all session variables
  $_SESSION = array();

  // If you want to destroy the session, also delete the session cookie.
  if (ini_get("session.use_cookies")) {
      $params = session_get_cookie_params();
      setcookie(session_name(), '', time() - 42000,
          $params["path"], $params["domain"],
          $params["secure"], $params["httponly"]
      );
  }

  // Finally, destroy the session
  session_destroy();
}

$error = ''; // Variable to store error message

// Check if the form is submitted
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // Get the input values
    $username = trim($_POST['username']);
    $password = trim($_POST['password']);

    // Validate the inputs
    if (empty($username) || empty($password)) {
        $error = "Username and Password are required!";
    } else {
        // Prepare a SQL statement to prevent SQL injection
        $stmt = $conn->prepare("SELECT admin_id, password_hash FROM admin_login WHERE email = ?");
        $stmt->bind_param("s", $username);
        $stmt->execute();
        $stmt->store_result();

        // Check if the username exists
        if ($stmt->num_rows > 0) {
          // print all rows with details
            $stmt->bind_result($admin_id, $password_hash);
            $stmt->fetch();

            // Verify the password
            if ($password == $password_hash) {
                // Store the admin ID in the session
                $_SESSION['admin_id'] = $admin_id;

                // Redirect to the dashboard or homepage
                header("Location: ../");
                exit();
            } else {
                $error = "Invalid Password!";
            }
        } else {
            $error = "Invalid Username!";
        }
        $stmt->close();
    }
}

$conn->close();
?>

<!doctype html>
<html lang="en" dir="ltr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Apex Demo Sign in</title>
    <link rel="shortcut icon" href="../../assets/images/apx-fav.png">
    <link rel="stylesheet" href="../../assets/css/core/libs.min.css">
    <link rel="stylesheet" href="../../assets/css/hope-ui.min1fc6.css?v=4.0.0">
    <link rel="stylesheet" href="../../assets/css/custom.min1fc6.css?v=4.0.0">
    <link rel="stylesheet" href="../../assets/css/dark.min.css">
    <link rel="stylesheet" href="../../assets/css/customizer.min.css">
    <link rel="stylesheet" href="../../assets/css/rtl.min.css">
</head>
<body class="" data-bs-spy="scroll" data-bs-target="#elements-section" data-bs-offset="0" tabindex="0">
    <div id="loading">
      <div class="loader simple-loader">
          <div class="loader-body"></div>
      </div>
    </div>
    <div class="wrapper">
        <section class="login-content">
            <div class="row m-0 align-items-center bg-white vh-100">
                <div class="col-md-6">
                    <div class="row justify-content-center">
                        <div class="col-md-10">
                            <div class="card card-transparent shadow-none d-flex justify-content-center mb-0 auth-card">
                                <div class="card-body">
                                    <a href="../index.html" class="navbar-brand d-flex align-items-center mb-3">
                                        <div class="logo-main">
                                            <div class="logo-normal">
                                                <!-- Logo SVG Here -->
                                            </div>
                                        </div>
                                        <h2 class="">Apex Laboratories Demo </h2>
                                    </a>
                                    <h2 class="mb-2 text-center">Sign In</h2>
                                    <p class="text-center">Login to stay connected.</p>
                                    <?php if (!empty($error)): ?>
                                        <div class="alert alert-danger" role="alert">
                                            <?php echo $error; ?>
                                        </div>
                                    <?php endif; ?>
                                    <form method="POST" action="">
                                        <div class="row">
                                            <div class="col-lg-12">
                                                <div class="form-group">
                                                    <label for="email" class="form-label">Email</label>
                                                    <input type="text" name="username" class="form-control" id="email" placeholder="Enter your email">
                                                </div>
                                            </div>
                                            <div class="col-lg-12">
                                                <div class="form-group">
                                                    <label for="password" class="form-label">Password</label>
                                                    <input type="password" name="password" class="form-control" id="password" placeholder="Enter your password">
                                                </div>
                                            </div>
                                            <div class="col-lg-12 d-flex justify-content-between">
                                                <div class="form-check mb-3">
                                                    <input type="checkbox" class="form-check-input" id="customCheck1">
                                                    <label class="form-check-label" for="customCheck1">Remember Me</label>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="d-flex justify-content-center">
                                            <button type="submit" class="btn btn-primary">Sign In</button>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="sign-bg">
                        <!-- SVG Background Here -->
                    </div>
                </div>
                <div class="col-md-6  d-flex justify-content-center align-items-center p-0 mt-n1 vh-100 overflow-hidden">
                    <img src="../../assets/images/auth/01.jpg" width="500px" height="500px" class=" gradient-main animated-scaleX" alt="images">
                </div>
            </div>
        </section>
    </div>
    <script src="../../assets/js/core/libs.min.js"></script>
    <script src="../../assets/js/core/external.min.js"></script>
    <script src="../../assets/js/charts/widgetcharts.js"></script>
    <script src="../../assets/js/charts/vectore-chart.js"></script>
    <script src="../../assets/js/charts/dashboard.js"></script>
    <script src="../../assets/js/plugins/fslightbox.js"></script>
    <script src="../../assets/js/plugins/setting.js"></script>
    <script src="../../assets/js/plugins/slider-tabs.js"></script>
    <script src="../../assets/js/plugins/form-wizard.js"></script>
    <script src="../../assets/js/hope-ui.js" defer></script>
</body>
</html>
