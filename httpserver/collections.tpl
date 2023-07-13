<table class="table table-header-rotated">
  <thead>
    <tr>
      <!-- First column header is not rotated -->
      <th></th>
      <!-- Following headers are rotated -->
        <th class="rotate"><div class="rotatediv"><span class="rotatedivspan">PLAY</span></div></th>
% for collection in sounds.soundsdb.collection_names_as_list():
        <th class="rotate"><div class="rotatediv"><span class="rotatedivspan">{{collection}}</span></div></th>
% end
    </tr> 
  </thead>
  <tbody>
<%
for sound in sounds.soundsdb.all():
  sound_id = sound['id']
  sound_name = sound['name']
%>
    <tr>
      <th class="row-header">{{sound_name}}</th>
      <td><button class="btn" onClick="ButtonHit('/Honey_Say', 'sound_id', '{{sound_id}}'); return false;"><i class="fa fa-play-circle-o" aria-hidden="true"></i></button></td>
<%
  for collection, is_checked in sounds.soundsdb.collections_for_sound(sound_id = sound_id):
    if is_checked:
        checked = 'checked="checked" '
    else:
        checked = ''
    end
%>
      <td><input {{checked}}type="checkbox" onchange="CollectionHit('/CollectionUpdate', '{{sound_id}}', '{{collection}}', this.checked); return false;"></td>
% end
    </tr>
% end
  </tbody>
</table>
