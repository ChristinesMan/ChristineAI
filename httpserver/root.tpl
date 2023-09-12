<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <head>
    <title>Christine's Brain</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <link rel="icon" href="data:,">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>

    <script src="multipurpose_tabcontent/js/jquery.multipurpose_tabcontent.js"></script>
    <link type="text/css" rel="stylesheet" href="multipurpose_tabcontent/css/style.css" />

    <link rel="stylesheet" href="/guts.css" type="text/css">
    <script src="/guts.js"></script>

    <script type="text/javascript">
        $(document).ready(function(){

            $('.tab_wrapper').champ();

        });
    </script>
</head>
<body>

    <div class="tab_wrapper">
        <ul>
            <li>Status</li>
            <li>Control</li>
            <li>Sounds</li>
            <li>Collections</li>
            <li>Upload</li>
            <li>Text To Speech</li>
        </ul>

        <div class="content_wrapper">
          <div class="tab_content" endpoint="/status">
          </div>
          <div class="tab_content" endpoint="/control">
          </div>
          <div class="tab_content" endpoint="/sounds">
          </div>
          <div class="tab_content" endpoint="/collections">
          </div>
          <div class="tab_content" endpoint="/upload">
          </div>
          <div class="tab_content" endpoint="/tts">
          </div>
      </div>
    </div>

</body>
</html>
