<table class="table table-header-rotated">
  <thead>
    <tr>
      <!-- First column header is not rotated -->
      <th></th>
      <!-- Following headers are rotated -->
% for collection in sounds.soundsdb.Collections():
        <th class="rotate"><div class="rotatediv"><span class="rotatedivspan">{{collection}}</span></div></th>
% end
    </tr> 
  </thead>
  <tbody>
<%
for Sound in sounds.soundsdb.All():
  SoundId = Sound['id']
  SoundName = Sound['name']
%>
    <tr>
      <th class="row-header">{{SoundName}}</th>
<%
  for collection, ischecked in sounds.soundsdb.CollectionsForSound(sound_id = SoundId):
    if ischecked:
        checked = 'checked="checked" '
    else:
        checked = ''
    end
%>
      <td><input {{checked}}type="checkbox" onchange="CollectionHit('/CollectionUpdate', '{{SoundId}}', '{{collection}}', this.checked); return false;"></td>
% end
    </tr>
% end
  </tbody>
</table>
