<%
for Row in AllSounds:
    SoundId = str(Row['id'])
    SoundName = str(Row['name'])
%>
    <span id="Sound{{SoundId}}">
        <button class="btn" onClick="ButtonHit('/Honey_Say', 'sound_id', '{{SoundId}}'); return false;"><i class="fa fa-play-circle-o" aria-hidden="true"></i></button><a href="javascript:void(0);" class="collapsible">{{SoundName}}</a><br/>
        <div class="sound_detail" sound_id="{{SoundId}}"><div class="loadingspinner"></div></div>
    </span>
% end

<script type="text/javascript">

    var coll = document.getElementsByClassName("collapsible");
    var i;

    for (i = 0; i < coll.length; i++) {
      coll[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var sound_detail_div = this.nextElementSibling.nextElementSibling;
        if (sound_detail_div.style.display === "block") {
          sound_detail_div.style.display = "none";
        } else {
          sound_detail_div.style.display = "block";
          FetchSoundDetail(sound_detail_div.attributes['sound_id'].value, sound_detail_div);
        }
      });
    }

</script>
