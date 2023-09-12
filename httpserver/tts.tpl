<h1>Text To Speech</h1>
<form id="formAjax" action="/Honey_Say_Text" method="post">
Text: <input id="text" type="text" name="text"/><br/>
      <input id="submit" type="submit" value="SAY"/></form><div id="status"></div><br/><br/>

<script type="text/javascript">

    // Thank you, https://uploadcare.com/blog/file-upload-ajax/
    var myForm = document.getElementById('formAjax');
    var myText = document.getElementById('text');
    var statusP = document.getElementById('status');

    myForm.onsubmit = function(event) {
        event.preventDefault();

        statusP.innerHTML = 'Processing...';

        // Create a FormData object
        var formData = new FormData();

        // Add the text to the AJAX request
        formData.append('text', myText.value);

        // Set up the request
        var xhr = new XMLHttpRequest();

        // Open the connection
        xhr.open('POST', '/Honey_Say_Text', true);

        // Set up a handler for when the task for the request is complete
        xhr.onload = function () {
          if (xhr.status == 200) {
            statusP.innerHTML = 'Done!';
          } else {
            statusP.innerHTML = 'Error.';
          }
        };

        // Send the data.
        xhr.overrideMimeType('text/plain')
        xhr.send(formData);
    }
</script>