<?php

// ini_set('display_errors', 1);
// ini_set('display_startup_errors', 1);
// error_reporting(E_ALL);

$string = file_get_contents("trader_info.json");
if ($string === false) {
    // deal with error...
}

$json_a = json_decode($string, true);
if ($json_a === null) {
    // deal with error...
}

function pluses($x) {
	if ($x > 0) {
		$x = "+$x";
	}
	return $x;
}

function minuses($x) {
	return str_replace("-", "&ndash;", $x);
}

foreach ($json_a as $key => $val) {
    switch ($key) {
    	case 'open_pos':
    		if ($val == true) {
    			$openpos = "Open";
    			$openpos_type = "danger";
    		} else {
    			$openpos = "Closed (&mdash;)";
    			$openpos_type = "success";
    		}
    		break;
    	case 'open_pos_trend_perc':
    		if (isset($val)) {
    			$val = pluses($val);
    			$val = minuses($val);
    			$opentrend = " ($val%)";
    		}
    		else {
    			$opentrend = "";
    		}
    		break;
    	case 'assets_perc':
			$val = pluses($val);
			$val = minuses($val);
			$assets_perc = "$val%";
    		break;
    	case 'apy_perc':
			$val = pluses($val);
			$val = minuses($val);
			$apy_perc = " ($val%&nbsp;APY)";
    		break;
    };
}


?>
<!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8">
	<meta http-equiv="refresh" content="60;url=index.php">
    <link href="bootstrap.css" rel="stylesheet">
    <link rel="icon" type="image/png" href="currency-exchange_1f4b1.png">
	<title>Hypetrader Assets</title>
	<style type="text/css">
	</style>
	<script type="text/javascript" src="jquery-3.6.0.min.js"></script>
</head>
<body>
	<nav class="navbar navbar-light bg-light text-center" style="display: inherit;">
		<div class="container-fluid text-center" style="display: inherit;">
			<a class="navbar-brand" href="#" style="font-size: 1.8em !important;">
				<img src="currency-exchange_1f4b1.png" alt="" class="d-inline-block align-text-top" width="40" height="36"> Hypetrader Assets <img src='BNB.png' width='35' class="d-inline-block align-text-top">
			</a>
		</div>
	</nav>

	<div class="container-fluid" style="margin-top: 20px;">
		<div class="d-flex justify-content-center">
			<div class="d-inline-block">
				<?php echo "<div class='p-2 fs-4 mb-2 bg-primary bg-gradient text-white text-center'>".$json_a['timestamp']."</div>"; ?>
			</div>
			<div class="d-inline-block">
				<?php echo "<div class='p-2 fs-4 mb-2 bg-info bg-gradient text-white text-center'>$assets_perc$apy_perc</div>"; ?>
			</div>
			<div class="d-inline-block">
				<?php echo "<div class='p-2 fs-4 mb-2 bg-$openpos_type bg-gradient text-white text-center'>$openpos$opentrend</div>"; ?>
			</div>
		</div>
	</div>

	<div class="container-fluid">
		<div class="d-flex justify-content-center">
			<div class="d-inline-block">
				<img class="no-cache img-fluid" src="signal-classification.png" border="0">
			</div>
			<div class="d-inline-block">
				<img class="no-cache img-fluid" src="assets.png" border="0">
			</div>
		</div>
	</div>

	<script type="text/javascript">
		var nods = document.getElementsByClassName('no-cache');
		for (var i = 0; i < nods.length; i++)
		{
		    nods[i].attributes['src'].value += "?random=" + Math.random();
		}
	</script>
</body>
</html>