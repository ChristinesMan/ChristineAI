        function ButtonHit(endpoint, data1, val1, data2=null, val2=null) {
          //console.log('ButtonHit');
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            //console.log('this.readyState = ' + this.readyState + '  this.status = ' + this.status);
            if (this.readyState == 4 && this.status == 200) {
              //console.log('ButtonHitDone');
              //document.getElementById("demo").innerHTML = this.responseText;
            }
          };
          xhttp.open("POST", endpoint, true);
          xhttp.overrideMimeType('text/plain')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          if ( data2 == null ) {
              xhttp.send(data1+'='+val1);
          } else {
              xhttp.send(data1+'='+val1+'&'+data2+'='+val2);
          }
        }

        function StatusUpdate() {
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            //console.log('StatusUpdate this.readyState = ' + this.readyState + '  this.status = ' + this.status);
            if (this.readyState == 4 && this.status == 200) {
              var status = JSON.parse(this.responseText);
              document.getElementById("CPU_Temp").innerHTML = status.CPU_Temp + '&deg;C';
              document.getElementById("LightLevelPct").innerHTML = (status.LightLevelPct * 100).toPrecision(2) + '%';
              document.getElementById("Wakefulness").innerHTML = (status.Wakefulness * 100).toPrecision(2) + '%';
              document.getElementById("TouchedLevel").innerHTML = (status.TouchedLevel * 100).toPrecision(2) + '%';
              document.getElementById("NoiseLevel").innerHTML = (status.NoiseLevel * 100).toPrecision(2) + '%';
              document.getElementById("ChanceToSpeak").innerHTML = (status.ChanceToSpeak * 100).toPrecision(2) + '%';
              document.getElementById("JostledLevel").innerHTML = (status.JostledLevel * 100).toPrecision(2) + '%';
              document.getElementById("SexualArousal").innerHTML = (status.SexualArousal * 100).toPrecision(2) + '%';
              document.getElementById("LoverProximity").innerHTML = (status.LoverProximity * 100).toPrecision(2) + '%';
              document.getElementById("IAmLayingDown").innerHTML = status.IAmLayingDown;
              document.getElementById("IAmSleeping").innerHTML = status.IAmSleeping;
              document.getElementById("ShushPleaseHoney").innerHTML = status.ShushPleaseHoney;
              document.getElementById("StarTrekMode").innerHTML = status.StarTrekMode;
              document.getElementById("BatteryVoltage").innerHTML = status.BatteryVoltage;
              document.getElementById("PowerState").innerHTML = status.PowerState;
              document.getElementById("ChargingState").innerHTML = status.ChargingState;
              setTimeout(StatusUpdate, 1000);
            }
          };
          xhttp.open("POST", "/Status_Update", true);
          xhttp.overrideMimeType('application/json')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send('LOVE');
        }

        function FetchSoundDetail(sound_id, detail_div) {
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
              detail_div.innerHTML = this.responseText;
            }
          };
          xhttp.open("POST", "/Sound_Detail", true);
          xhttp.overrideMimeType('text/html')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send('sound_id='+sound_id);
        }

        function CollectionHit(endpoint, id, name=null, state=null) {
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
              //console.log('ButtonHitDone');
            }
          };
          xhttp.open("POST", endpoint, true);
          xhttp.overrideMimeType('text/plain')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send('sound_id='+id+'&collectionname='+name+'&collectionstate='+state);
        }

        function StartRecord() {
          var form = document.getElementById('recordform');
          var distance = recordform.elements['distance'].value
          var word = recordform.elements['word'].value
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
              //console.log('ButtonHitDone');
            }
          };
          xhttp.open("POST", "/RecordingStart", true);
          xhttp.overrideMimeType('text/plain')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send(distance + ',' + word);
        }

        function StopRecord() {
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
              //console.log('ButtonHitDone');
            }
          };
          xhttp.open("POST", "/RecordingStop", true);
          xhttp.overrideMimeType('text/plain')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send('juststopit');
        }
