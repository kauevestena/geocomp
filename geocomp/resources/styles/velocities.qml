<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  Station velocities from a series of epochs (FR-836, FR-837, FR-838;
  specs/14 sections 6 and 7).

  Each arrow is one year's motion, exaggerated by the factor the layer's name
  states. Significant means the velocity differs from zero at the chosen
  confidence; an alert, that the speed crossed a velocity threshold.
-->
<qgis version="3.34.0" styleCategories="Symbology|Fields|Forms">
  <renderer-v2 type="categorizedSymbol" attr="category" forceraster="0" symbollevels="0" enableorderby="0">
    <categories>
      <category value="alert" symbol="0" label="Alert: a velocity threshold crossed" render="true"/>
      <category value="significant" symbol="1" label="Significant velocity" render="true"/>
      <category value="not significant" symbol="2" label="Not significant" render="true"/>
    </categories>
    <symbols>
      <symbol type="line" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="ArrowLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="arrow_width" type="QString" value="0.8"/>
            <Option name="arrow_width_unit" type="QString" value="MM"/>
            <Option name="arrow_start_width" type="QString" value="0.8"/>
            <Option name="arrow_start_width_unit" type="QString" value="MM"/>
            <Option name="head_length" type="QString" value="3"/>
            <Option name="head_length_unit" type="QString" value="MM"/>
            <Option name="head_thickness" type="QString" value="2.4"/>
            <Option name="head_thickness_unit" type="QString" value="MM"/>
            <Option name="head_type" type="QString" value="0"/>
            <Option name="arrow_type" type="QString" value="0"/>
            <Option name="is_curved" type="QString" value="0"/>
            <Option name="is_repeated" type="QString" value="0"/>
            <Option name="ring_filter" type="QString" value="0"/>
          </Option>
          <symbol type="fill" name="@0@0" alpha="1" clip_to_extent="1" force_rhr="0">
            <layer class="SimpleFill" pass="0" locked="0" enabled="1">
              <Option type="Map">
                <Option name="color" type="QString" value="213,94,0,255"/>
                <Option name="outline_color" type="QString" value="213,94,0,255"/>
                <Option name="outline_width" type="QString" value="0"/>
                <Option name="outline_style" type="QString" value="solid"/>
                <Option name="style" type="QString" value="solid"/>
              </Option>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol type="line" name="1" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="ArrowLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="arrow_width" type="QString" value="0.6"/>
            <Option name="arrow_width_unit" type="QString" value="MM"/>
            <Option name="arrow_start_width" type="QString" value="0.6"/>
            <Option name="arrow_start_width_unit" type="QString" value="MM"/>
            <Option name="head_length" type="QString" value="2.5"/>
            <Option name="head_length_unit" type="QString" value="MM"/>
            <Option name="head_thickness" type="QString" value="2"/>
            <Option name="head_thickness_unit" type="QString" value="MM"/>
            <Option name="head_type" type="QString" value="0"/>
            <Option name="arrow_type" type="QString" value="0"/>
            <Option name="is_curved" type="QString" value="0"/>
            <Option name="is_repeated" type="QString" value="0"/>
            <Option name="ring_filter" type="QString" value="0"/>
          </Option>
          <symbol type="fill" name="@1@0" alpha="1" clip_to_extent="1" force_rhr="0">
            <layer class="SimpleFill" pass="0" locked="0" enabled="1">
              <Option type="Map">
                <Option name="color" type="QString" value="0,114,178,255"/>
                <Option name="outline_color" type="QString" value="0,114,178,255"/>
                <Option name="outline_width" type="QString" value="0"/>
                <Option name="outline_style" type="QString" value="solid"/>
                <Option name="style" type="QString" value="solid"/>
              </Option>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol type="line" name="2" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="ArrowLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="arrow_width" type="QString" value="0.3"/>
            <Option name="arrow_width_unit" type="QString" value="MM"/>
            <Option name="arrow_start_width" type="QString" value="0.3"/>
            <Option name="arrow_start_width_unit" type="QString" value="MM"/>
            <Option name="head_length" type="QString" value="1.6"/>
            <Option name="head_length_unit" type="QString" value="MM"/>
            <Option name="head_thickness" type="QString" value="1.28"/>
            <Option name="head_thickness_unit" type="QString" value="MM"/>
            <Option name="head_type" type="QString" value="0"/>
            <Option name="arrow_type" type="QString" value="0"/>
            <Option name="is_curved" type="QString" value="0"/>
            <Option name="is_repeated" type="QString" value="0"/>
            <Option name="ring_filter" type="QString" value="0"/>
          </Option>
          <symbol type="fill" name="@2@0" alpha="1" clip_to_extent="1" force_rhr="0">
            <layer class="SimpleFill" pass="0" locked="0" enabled="1">
              <Option type="Map">
                <Option name="color" type="QString" value="120,120,120,255"/>
                <Option name="outline_color" type="QString" value="120,120,120,255"/>
                <Option name="outline_width" type="QString" value="0"/>
                <Option name="outline_style" type="QString" value="solid"/>
                <Option name="style" type="QString" value="solid"/>
              </Option>
            </layer>
          </symbol>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
