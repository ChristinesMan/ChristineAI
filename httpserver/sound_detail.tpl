<%
    SoundId = str(Sound['id'])
    SoundName = Sound['name']
    SoundBaseVolumeAdjust = str(Sound['base_volume_adjust'])
    SoundProximityVolumeAdjust = str(Sound['proximity_volume_adjust'])
    SoundIntensity = str(Sound['intensity'])
    SoundCuteness = str(Sound['cuteness'])
    SoundTempoRange = str(Sound['tempo_range'])
    SoundReplayWait = str(Sound['replay_wait'])
%>
Sound ID: {{SoundId}}<br/>

<button class="btn" onClick="if (window.confirm('Press OK to REALLY delete the sound')) { ButtonHit('/Delete_Sound', 'sound_id', '{{SoundId}}'); document.getElementById('Sound{{SoundId}}').remove(); } return false;"><i class="fa fa-trash-o" aria-hidden="true"></i></button>Delete Sound<br/>

Base volume adjust
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
</select><br/>

Proximity volume adjust
<select class="proximity_volume_adjust" onchange="ButtonHit('/ProximityVolChange', 'sound_id', '{{SoundId}}', 'volume', this.value); return false;">
<%
for select_option in ['0.2', '0.5', '1.0', '2.0', '3.0', '4.0', '5.0', '10.0', '15.0', '20.0', '25.0', '30.0', '40.0', '50.0']:
    if select_option == SoundProximityVolumeAdjust:
        optionselected = 'selected="true" '
    else:
        optionselected = ''
    end
%>
    <option {{optionselected}}value="{{select_option}}">{{select_option}}</option>
% end
</select><br/>

Intensity
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
</select><br/>

Cuteness
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
</select><br/>

Tempo Range
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
</select><br/>

Replay Wait
<select class="replay_wait" onchange="ButtonHit('/ReplayWaitChange', 'sound_id', '{{SoundId}}', 'replay_wait', this.value); return false;">
<%
for select_option in [('No wait', '0'), ('3 seconds', '3'), ('5 seconds', '5'), ('30 seconds', '30'), ('1 minute', '60'), ('5 minutes', '300'), ('30 minutes', '1800'), ('1 hour', '3600'), ('2 hours', '7200'), ('5 hours', '18000'), ('8 hours', '28800'), ('12 hours', '43200'), ('24 hours', '86400'), ('48 hours', '172800')]:
    if select_option[1] == SoundReplayWait:
        optionselected = 'selected="true" '
    else:
        optionselected = ''
    end
%>
    <option {{optionselected}}value="{{select_option[1]}}">{{select_option[0]}}</option>
% end
</select><br/>


<h5>Collections</h5>
<%
for collection, ischecked in CollectionsForSound:
    if ischecked:
        checked = ' checked="checked"'
    else:
        checked = ''
    end
%>
    <input type="checkbox" class="collection_checkbox" onchange="CollectionHit('/CollectionUpdate', '{{SoundId}}', '{{collection}}', this.checked); return false;"{{checked}}/>{{collection}}<br/>
% end