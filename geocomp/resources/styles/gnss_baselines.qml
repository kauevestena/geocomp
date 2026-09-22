<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  GNSS baselines (FR-357, FR-902, specs/11 section 5).

  One line per determined baseline, categorised by whether it belongs to the
  independent subset. That is the distinction a reader of this layer needs
  first: n simultaneously observing stations give n(n-1)/2 baselines of which
  only n-1 carry new information, and a map that drew them alike would suggest
  a network far better observed than it is.

  Dependent baselines are drawn dashed and thin, so they read as what they are:
  present, and carrying nothing the solid ones do not already say.

  Okabe-Ito, as everywhere else in GeoComp.
-->
<qgis version="3.34.0" styleCategories="Symbology|Fields|Forms">
  <renderer-v2 type="categorizedSymbol" attr="independent" forceraster="0" symbollevels="0" enableorderby="0">
    <categories>
      <category value="yes" symbol="0" label="Independent" render="true"/>
      <category value="no" symbol="1" label="Dependent (no new information)" render="true"/>
      <category value="" symbol="2" label="Not assessed" render="true"/>
    </categories>
    <symbols>
      <symbol type="line" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="0,114,178,220"/>
            <Option name="line_width" type="QString" value="0.55"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="line" name="1" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="153,153,153,160"/>
            <Option name="line_width" type="QString" value="0.25"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="customdash" type="QString" value="2;1.5"/>
            <Option name="customdash_unit" type="QString" value="MM"/>
            <Option name="use_custom_dash" type="QString" value="1"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="line" name="2" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="230,159,0,200"/>
            <Option name="line_width" type="QString" value="0.35"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
