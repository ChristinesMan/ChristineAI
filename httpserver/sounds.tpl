<table class="soundstable">
    <thead>
        <tr>
            <th></th>
            <th></th>
            <th></th>
            <th>NAME</th>
            <th width="8%">BaseVol</th>
            <th width="8%">ProxVol</th>
            <th width="8%">Intensity</th>
            <th width="8%">Cuteness</th>
            <th width="8%">TempoRange</th>
            <th width="8%">ReplayWait</th>
        </tr> 
    </thead>
<tbody>

% for collection in sounds.soundsdb.AllSoundsByCollection():
    <tr>
        <th></th>
        <td colspan="11"><h1>Collection: {{collection['name']}}</h1></td>
    </tr>
<%
for Sound in collection['sounds']:
    SoundId = Sound['id']
    SoundName = Sound['name']
    SoundBaseVolumeAdjust = str(Sound['base_volume_adjust'])
    SoundProximityVolumeAdjust = str(Sound['proximity_volume_adjust'])
    SoundIntensity = str(Sound['intensity'])
    SoundCuteness = str(Sound['cuteness'])
    SoundTempoRange = str(Sound['tempo_range'])
    SoundReplayWait = str(Sound['replay_wait'])
%>
    <tr>
        <th>{{SoundId}}</th>
        <td><button class="btn" onClick="ButtonHit('/Honey_Say', 'sound_id', '{{SoundId}}'); return false;"><i class="fa fa-play-circle-o" aria-hidden="true"></i></button></td>
        <td><button class="btn" onClick="if (window.confirm('Press OK to REALLY delete the sound')) { ButtonHit('/Delete_Sound', 'sound_id', '{{SoundId}}'); this.parentElement.parentElement.remove(); } return false;"><i class="fa fa-trash-o" aria-hidden="true"></i></button></td>
        <td>{{SoundName}}</td>
        <td class="sounddata">
            <select class="base_volume_adjust" onchange="ButtonHit('/BaseVolChange', 'sound_id', '{{SoundId}}', 'volume', this.value); return false;">
<%
for select_option in ['0.2', '0.5', '1.0', '2.0', '3.0', '4.0', '5.0', '10.0', '15.0', '20.0', '25.0', '30.0', '40.0', '50.0']:
    if select_option == SoundBaseVolumeAdjust:
        optionselected = 'selected="true" '
    else:
        optionselected = ''
    end
%>
                <option {{optionselected}}value="{{select_option}}">{{select_option}}</option>
% end
            </select>
        </td>
        <td class="sounddata">
            <select class="proximity_volume_adjust" onchange="ButtonHit('/ProximityVolChange', 'sound_id', '{{SoundId}}', 'volume', this.value); return false;">
<%
for select_option in ['1.0', '0.95', '0.9', '0.85', '0.8', '0.75', '0.7', '0.65', '0.6', '0.55', '0.5']:
    if select_option == SoundProximityVolumeAdjust:
        optionselected = 'selected="true" '
    else:
        optionselected = ''
    end
%>
                <option {{optionselected}}value="{{select_option}}">{{select_option}}</option>
% end
            </select>
        </td>
        <td class="sounddata">
            <select class="intensity" onchange="ButtonHit('/IntensityChange', 'sound_id', '{{SoundId}}', 'intensity', this.value); return false;">
<%
for select_option in ['0.0', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9', '1.0']:
    if select_option == SoundIntensity:
        optionselected = 'selected="true" '
    else:
        optionselected = ''
    end
%>
                <option {{optionselected}}value="{{select_option}}">{{select_option}}</option>
% end
            </select>
        </td>
        <td class="sounddata">
            <select class="cuteness" onchange="ButtonHit('/CutenessChange', 'sound_id', '{{SoundId}}', 'cuteness', this.value); return false;">
<%
for select_option in ['0.0', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9', '1.0']:
    if select_option == SoundCuteness:
        optionselected = 'selected="true" '
    else:
        optionselected = ''
    end
%>
                <option {{optionselected}}value="{{select_option}}">{{select_option}}</option>
% end
            </select>
        </td>
        <td class="sounddata">
            <select class="tempo_range" onchange="ButtonHit('/TempoRangeChange', 'sound_id', '{{SoundId}}', 'tempo_range', this.value); return false;">
<%
for select_option in ['0.0', '0.01', '0.02', '0.03', '0.04', '0.05', '0.06', '0.07', '0.08', '0.09', '0.10', '0.11', '0.12', '0.13', '0.14', '0.15', '0.16', '0.17', '0.18', '0.19', '0.20', '0.21']:
    if select_option == SoundTempoRange:
        optionselected = 'selected="true" '
    else:
        optionselected = ''
    end
%>
                <option {{optionselected}}value="{{select_option}}">{{select_option}}</option>
% end
            </select>
        </td>
        <td class="sounddata">
            <select class="replay_wait" onchange="ButtonHit('/ReplayWaitChange', 'sound_id', '{{SoundId}}', 'replay_wait', this.value); return false;">
<%
for select_option in [('No wait', '0'), ('3 seconds', '3'), ('5 seconds', '5'), ('30 seconds', '30'), ('1 minute', '60'), ('5 minutes', '300'), ('30 minutes', '1800'), ('1 hour', '3600'), ('2 hours', '7200'), ('5 hours', '18000'), ('8 hours', '28800'), ('12 hours', '43200'), ('24 hours', '86400'), ('48 hours', '172800'), ('96 hours', '345600')]:
    if select_option[1] == SoundReplayWait:
        optionselected = 'selected="true" '
    else:
        optionselected = ''
    end
%>
                <option {{optionselected}}value="{{select_option[1]}}">{{select_option[0]}}</option>
% end
            </select>
        </td>

    </tr>
% end
% end

    </tbody>
</table>

<script type="text/javascript">

    // var coll = document.getElementsByClassName("collapsible");
    // var i;

    // for (i = 0; i < coll.length; i++) {
    //   coll[i].addEventListener("click", function() {
    //     this.classList.toggle("active");
    //     var sound_detail_div = this.nextElementSibling.nextElementSibling;
    //     if (sound_detail_div.style.display === "block") {
    //       sound_detail_div.style.display = "none";
    //     } else {
    //       sound_detail_div.style.display = "block";
    //       FetchSoundDetail(sound_detail_div.attributes['sound_id'].value, sound_detail_div);
    //     }
    //   });
    // }

</script>
