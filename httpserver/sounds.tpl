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
