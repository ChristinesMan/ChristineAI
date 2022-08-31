<h1>New Sound</h1>
<form id="formAjax" action="/New_Sound" method="post">
Folder: <input id="folder" type="text" name="folder"/><br/>
File:   <input id="fileAjax" type="file" name="filename"/><br/>
        <input id="submit" type="submit" value="Upload"/></form><div id="status"></div><br/><br/>

<script type="text/javascript">

    // Thank you, https://uploadcare.com/blog/file-upload-ajax/
    var myForm = document.getElementById('formAjax');  // Our HTML form's ID
    var myFolder = document.getElementById('folder');  // text field for the folder in which to place the new sound
    var myFile = document.getElementById('fileAjax');  // Our HTML files' ID
    var statusP = document.getElementById('status');

    myForm.onsubmit = function(event) {
        event.preventDefault();

        statusP.innerHTML = 'Uploading and processing...';

        // Get the files from the form input
        var files = myFile.files;

        // Create a FormData object
        var formData = new FormData();

        // Select only the first file from the input array
        var file = files[0]; 

        // Check the file type
        if (file.type != 'audio/x-wav') {
            statusP.innerHTML = 'The file selected is not a wav audio.';
            return;
        }

        // Add the folder name to the AJAX request
        formData.append('folder', myFolder.value);
        // Add the file to the AJAX request
        formData.append('fileAjax', file, file.name);

        // Set up the request
        var xhr = new XMLHttpRequest();

        // Open the connection
        xhr.open('POST', '/New_Sound', true);

        // Set up a handler for when the task for the request is complete
        xhr.onload = function () {
          if (xhr.status == 200) {
            statusP.innerHTML = 'Done!';
          } else {
            statusP.innerHTML = 'Upload error.';
          }
        };

        // Send the data.
        xhr.overrideMimeType('text/plain')
        xhr.send(formData);
    }
</script>