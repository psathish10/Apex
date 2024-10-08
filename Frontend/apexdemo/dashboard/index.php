<?php  

session_start();

// Check if the admin is logged in
if (!isset($_SESSION['admin_id'])) {
    header("Location: auth/login.php");
    exit();
}

// Include the database connection file
include '../db(1).php';

// Query to fetch data from the updated table
$sql = "SELECT `id`, `Stockist_Code`, `Stockist_Name`, `Bill_No`, `Bill_Date`, `Chemist_Code`, `Chemist_Name`, `Address`, `City`, `Pin_Code`, `Material_Code`, `Material_Name`, `Batch_No`, `Sale_Qty`, `Free_Qty`, `Rate`, `Value`,`from_date`,`to_date` FROM `salesdata` ORDER BY id DESC";
$result = $conn->query($sql);

// Check for query errors
if (!$result) {
    die("Query failed: " . $conn->error);
}

include '../includes/header.php';
?>

<div class="container-fluid content-inner mt-n5 py-0">
<div class="row">
   <div class="col-md-12 col-lg-12">
      <div class="col-md-12">
         <div class="card">
            <div class="card-header d-flex justify-content-between">
               <div class="header-title">
                  <h4 class="card-title">Stockist Details</h4>
               </div>
            </div>
            <?php if (isset($_GET['message'])) { ?>
                <div class='alert m-5 alert-warning alert-dismissible fade show' role="alert">
                    <?php echo htmlspecialchars($_GET['message']); ?>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            <?php } ?>
            <div class="card-body">
               <div class="table-responsive">
                  <table id="datatable" class="table table-striped" data-toggle="data-table">
                        <thead>
                           <tr>
                              <th>id</th>
                              <th>Stockist Code</th>
                              <th>Stockist Name</th>
                              <th>Bill No</th>
                              <th>Bill Date</th>
                              <th>Chemist Code</th>
                              <th>Chemist Name</th>
                              <th>Address</th>
                              <th>City</th>
                              <th>Pin Code</th>
                              <th>Material Code</th>
                              <th>Material Name</th>
                              <th>Batch No</th>
                              <th>Sale Qty</th>
                              <th>Free Qty</th>
                              <th>Rate</th>
                              <th>Value</th>
                              <th>Action</th>
                              <th> From Date</th>
                              <th>To Date</th>
                           </tr>
                        </thead>
                        <tbody>
                        <?php
                              if ($result->num_rows > 0) {
                                 // Output data of each row
                                 while ($row = $result->fetch_assoc()) {
                        ?>
                           <tr>
                              <td><?php echo htmlspecialchars($row["id"]); ?></td>
                              <td><?php echo htmlspecialchars($row["Stockist_Code"]); ?></td>
                              <td><?php echo htmlspecialchars($row["Stockist_Name"]); ?></td>
                              <td><?php echo htmlspecialchars($row["Bill_No"]); ?></td>
                              <td><?php echo htmlspecialchars($row["Bill_Date"]); ?></td>
                              <td><?php echo htmlspecialchars($row["Chemist_Code"]); ?></td>
                              <td><?php echo htmlspecialchars($row["Chemist_Name"]); ?></td>
                              <td><?php echo htmlspecialchars($row["Address"]); ?></td>
                              <td><?php echo htmlspecialchars($row["City"]); ?></td>
                              <td><?php echo htmlspecialchars($row["Pin_Code"]); ?></td>
                              <td><?php echo htmlspecialchars($row["Material_Code"]); ?></td>
                              <td><?php echo htmlspecialchars($row["Material_Name"]); ?></td>
                              <td><?php echo htmlspecialchars($row["Batch_No"]); ?></td>
                              <td><?php echo htmlspecialchars($row["Sale_Qty"]); ?></td>
                              <td><?php echo htmlspecialchars($row["Free_Qty"]); ?></td>
                              <td><?php echo htmlspecialchars($row["Rate"]); ?></td>
                              <td><?php echo htmlspecialchars($row["Value"]); ?></td>
                              <td><?php echo htmlspecialchars($row["from_date"]); ?></td>
                              <td><?php echo htmlspecialchars($row["to_date"]); ?></td>
                              <td>
                                    <form method="POST" action="delete-data.php" onsubmit="return confirm('Are you sure you want to delete this entry?');">
                                       <input type="hidden" name="table" value="salesdata">
                                       <input type="hidden" name="id" value="<?php echo htmlspecialchars($row['id']); ?>">
                                       <button type="submit" class="btn btn-danger btn-sm">Delete</button>
                                    </form>
                              </td>
                           </tr>
                        <?php
                                 }
                              } else {
                                 echo "<tr><td colspan='17'>No results found</td></tr>";
                              }
                        ?>
                        </tbody>
                        <tfoot>
                              <tr>
                                 <th>id</th>
                                 <th>Stockist Code</th>
                                 <th>Stockist Name</th>
                                 <th>Bill No</th>
                                 <th>Bill Date</th>
                                 <th>Chemist Code</th>
                                 <th>Chemist Name</th>
                                 <th>Address</th>
                                 <th>City</th>
                                 <th>Pin Code</th>
                                 <th>Material Code</th>
                                 <th>Material Name</th>
                                 <th>Batch No</th>
                                 <th>Sale Qty</th>
                                 <th>Free Qty</th>
                                 <th>Rate</th>
                                 <th>Value</th>
                                 <th>Action</th>
                              </tr>
                        </tfoot>
                  </table>
               </div>
            </div>
         </div>
         </div>  
      </div>
   </div> 
</div>

<?php 
// Close the database connection after all processing is done
$conn->close(); 
include_once "../includes/footer.php"; 
?>
