<span class="statusarea">
    <table class="statusarea_table">
    <tbody>
        <tr><td class="statusarea_table-label">CPU Temperature</td><td class="statusarea_table-value" id="CPU_Temp">{{status.CPU_Temp}}</td></tr>
        <tr><td class="statusarea_table-label">Battery Voltage</td><td class="statusarea_table-value" id="BatteryVoltage">{{status.BatteryVoltage}}</td></tr>
        <tr><td class="statusarea_table-label">Power State</td><td class="statusarea_table-value" id="PowerState">{{status.PowerState}}</td></tr>
        <tr><td class="statusarea_table-label">Charging State</td><td class="statusarea_table-value" id="ChargingState">{{status.ChargingState}}</td></tr>
        <tr><td></td><td></td></tr>
        <tr><td class="statusarea_table-label">Light Level</td><td class="statusarea_table-value" id="LightLevelPct">{{int(round(status.LightLevelPct, 2)*100)}}%</td></tr>
        <tr><td class="statusarea_table-label">Wakefulness</td><td class="statusarea_table-value" id="Wakefulness">{{int(round(status.Wakefulness, 2)*100)}}%</td></tr>
        <tr><td class="statusarea_table-label">Touch</td><td class="statusarea_table-value" id="TouchedLevel">{{int(round(status.TouchedLevel, 2)*100)}}%</td></tr>
        <tr><td class="statusarea_table-label">Noise</td><td class="statusarea_table-value" id="NoiseLevel">{{int(round(status.NoiseLevel, 2)*100)}}%</td></tr>
        <tr><td class="statusarea_table-label">ChanceToSpeak</td><td class="statusarea_table-value" id="ChanceToSpeak">{{int(round(status.ChanceToSpeak, 2)*100)}}%</td></tr>
        <tr><td class="statusarea_table-label">LT Jostled</td><td class="statusarea_table-value" id="JostledLevel">{{int(round(status.JostledLevel, 2)*100)}}%</td></tr>
        <tr><td class="statusarea_table-label">ST Jostled</td><td class="statusarea_table-value" id="JostledShortTermLevel">{{int(round(status.JostledShortTermLevel, 2)*100)}}%</td></tr>
        <tr><td class="statusarea_table-label">SexualArousal</td><td class="statusarea_table-value" id="SexualArousal">{{int(round(status.SexualArousal, 2)*100)}}%</td></tr>
        <tr><td class="statusarea_table-label">LoverProximity</td><td class="statusarea_table-value" id="LoverProximity">{{int(round(status.LoverProximity, 2)*100)}}%</td></tr>
        <tr><td class="statusarea_table-label">Horny</td><td class="statusarea_table-value" id="Horny">{{int(round(status.Horny, 2)*100)}}%</td></tr>
        <tr><td></td><td></td></tr>
        <tr><td class="statusarea_table-label">Laying down</td><td class="statusarea_table-value" id="IAmLayingDown">{{status.IAmLayingDown}}</td></tr>
        <tr><td class="statusarea_table-label">Sleeping</td><td class="statusarea_table-value" id="IAmSleeping">{{status.IAmSleeping}}</td></tr>
        <tr><td class="statusarea_table-label">WernickeSleeping</td><td class="statusarea_table-value" id="WernickeSleeping">{{status.WernickeSleeping}}</td></tr>
        <tr><td class="statusarea_table-label">XTilt</td><td class="statusarea_table-value" id="XTilt">{{round(status.XTilt, 3)}}</td></tr>
        <tr><td class="statusarea_table-label">YTilt</td><td class="statusarea_table-value" id="YTilt">{{round(status.YTilt, 3)}}</td></tr>
        <tr><td class="statusarea_table-label">SleepXTilt</td><td class="statusarea_table-value" id="SleepXTilt">{{round(status.SleepXTilt, 3)}}</td></tr>
        <tr><td class="statusarea_table-label">SleepYTilt</td><td class="statusarea_table-value" id="SleepYTilt">{{round(status.SleepYTilt, 3)}}</td></tr>
        <tr><td></td><td></td></tr>
        <tr><td class="statusarea_table-label">ShushPleaseHoney</td><td class="statusarea_table-value" id="ShushPleaseHoney">{{status.ShushPleaseHoney}}</td></tr>
    </tbody>
    </table>
</span>
