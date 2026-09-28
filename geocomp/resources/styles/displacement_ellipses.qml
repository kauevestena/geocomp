<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  Displacement confidence ellipses, at each arrow's tip (FR-834, FR-901;
  specs/14 section 4.1, specs/19 section 3).

  Drawn where the displacement ends so a reader can see whether zero, the
  arrow's tail, lies inside: inside is "not significant", outside is
  "significant". Outlines with a faint fill, so the arrow stays visible
  through its own ellipse. Same categories and colours as the arrows.
-->
<qgis version="3.34.0" styleCategories="Symbology|Fields|Forms">
  <renderer-v2 type="categorizedSymbol" attr="category" forceraster="0" symbollevels="0" enableorderby="0">
    <categories>
      <category value="alert" symbol="0" label="Alert: a threshold crossed" render="true"/>
      <category value="significant" symbol="1" label="Significant motion" render="true"/>
      <category value="not significant" symbol="2" label="Not significant" render="true"/>
    </categories>
    <symbols>
      <symbol type="fill" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="color" type="QString" value="213,94,0,40"/>
            <Option name="outline_color" type="QString" value="213,94,0,255"/>
            <Option name="outline_width" type="QString" value="0.6"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="fill" name="1" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="color" type="QString" value="0,114,178,40"/>
            <Option name="outline_color" type="QString" value="0,114,178,255"/>
            <Option name="outline_width" type="QString" value="0.5"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="fill" name="2" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="color" type="QString" value="120,120,120,40"/>
            <Option name="outline_color" type="QString" value="120,120,120,255"/>
            <Option name="outline_width" type="QString" value="0.3"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="outline_style" type="QString" value="dash"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
