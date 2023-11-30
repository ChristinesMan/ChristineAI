<span class="statusarea">
    <table class="statusarea_table">
    <tbody>
        <tr><td class="statusarea_table-label">CPU Temperature</td><td class="statusarea_table-value" id="CPU_Temp">{{SHARED_STATE.cpu_temp}}</td></tr>
        <tr><td class="statusarea_table-label">Battery Voltage</td><td class="statusarea_table-value" id="BatteryVoltage">{{SHARED_STATE.battery_voltage}}</td></tr>
        <tr><td class="statusarea_table-label">Power State</td><td class="statusarea_table-value" id="PowerState">{{SHARED_STATE.power_state}}</td></tr>
        <tr><td class="statusarea_table-label">Charging State</td><td class="statusarea_table-value" id="ChargingState">{{SHARED_STATE.charging_state}}</td></tr>
        <tr><td></td><td></td></tr>
        <tr><td class="statusarea_table-label">Light Level</td><td class="statusarea_table-value" id="LightLevelPct">{{int(round(SHARED_STATE.light_level, 2)*100)}}%</td></tr>
        <tr><td class="statusarea_table-label">Wakefulness</td><td class="statusarea_table-value" id="Wakefulness">{{int(round(SHARED_STATE.wakefulness, 2)*100)}}%</td></tr>
        <tr><td class="statusarea_table-label">Touch</td><td class="statusarea_table-value" id="TouchedLevel">{{int(round(SHARED_STATE.touched_level, 2)*100)}}%</td></tr>
        <tr><td class="statusarea_table-label">Noise</td><td class="statusarea_table-value" id="NoiseLevel">{{int(round(SHARED_STATE.noise_level, 2)*100)}}%</td></tr>
        <tr><td class="statusarea_table-label">LT Jostled</td><td class="statusarea_table-value" id="JostledLevel">{{int(round(SHARED_STATE.jostled_level, 2)*100)}}%</td></tr>
        <tr><td class="statusarea_table-label">ST Jostled</td><td class="statusarea_table-value" id="JostledShortTermLevel">{{int(round(SHARED_STATE.jostled_level_short, 2)*100)}}%</td></tr>
        <tr><td class="statusarea_table-label">SexualArousal</td><td class="statusarea_table-value" id="SexualArousal">{{int(round(SHARED_STATE.sexual_arousal, 2)*100)}}%</td></tr>
        <tr><td class="statusarea_table-label">LoverProximity</td><td class="statusarea_table-value" id="LoverProximity">{{int(round(SHARED_STATE.lover_proximity, 2)*100)}}%</td></tr>
        <tr><td class="statusarea_table-label">Horny</td><td class="statusarea_table-value" id="Horny">{{int(round(SHARED_STATE.horny, 2)*100)}}%</td></tr>
        <tr><td></td><td></td></tr>
        <tr><td class="statusarea_table-label">Laying down</td><td class="statusarea_table-value" id="IAmLayingDown">{{SHARED_STATE.is_laying_down}}</td></tr>
        <tr><td class="statusarea_table-label">Sleeping</td><td class="statusarea_table-value" id="IAmSleeping">{{SHARED_STATE.is_sleeping}}</td></tr>
        <tr><td class="statusarea_table-label">Tired</td><td class="statusarea_table-value" id="Tired">{{SHARED_STATE.is_tired}}</td></tr>
        <tr><td class="statusarea_table-label">WernickeSleeping</td><td class="statusarea_table-value" id="WernickeSleeping">{{SHARED_STATE.wernicke_sleeping}}</td></tr>
        <tr><td class="statusarea_table-label">XTilt</td><td class="statusarea_table-value" id="XTilt">{{round(SHARED_STATE.tilt_x, 3)}}</td></tr>
        <tr><td class="statusarea_table-label">YTilt</td><td class="statusarea_table-value" id="YTilt">{{round(SHARED_STATE.tilt_y, 3)}}</td></tr>
        <tr><td class="statusarea_table-label">SleepXTilt</td><td class="statusarea_table-value" id="SleepXTilt">{{round(SHARED_STATE.sleep_tilt_x, 3)}}</td></tr>
        <tr><td class="statusarea_table-label">SleepYTilt</td><td class="statusarea_table-value" id="SleepYTilt">{{round(SHARED_STATE.sleep_tilt_y, 3)}}</td></tr>
        <tr><td class="statusarea_table-label">BreathIntensity</td><td class="statusarea_table-value" id="BreathIntensity">{{round(SHARED_STATE.breath_intensity, 2)}}</td></tr>
        <tr><td></td><td></td></tr>
        <tr><td class="statusarea_table-label">ShushPleaseHoney</td><td class="statusarea_table-value" id="ShushPleaseHoney">{{SHARED_STATE.shush_please_honey}}</td></tr>
    </tbody>
    </table>
</span>
