<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  Gravity stations (FR-700, FR-900, specs/12 section 5, specs/19 section 2).

  Shape says how a station's gravity was determined: held (the datum, chosen),
  an absolute value (measured, weighted), or relative differences alone.
  Size says how well it is known, as on every other GeoComp station layer.

  An absolute value the rest of the network cannot check - the common case of
  a lone absolute site - gets a thick reddish-purple outline, the colour the
  differences layer uses for "not testable": its value was used, and nothing
  confirmed it.

  Okabe-Ito colours, which survive colour-vision deficiencies and greyscale.
-->
<qgis version="3.34.0" styleCategories="Symbology|Fields|Forms">
  <renderer-v2 type="categorizedSymbol" attr="role" forceraster="0" symbollevels="0" enableorderby="0">
    <categories>
      <category value="held" symbol="0" label="Held (datum)" render="true"/>
      <category value="absolute" symbol="1" label="Absolute value" render="true"/>
      <category value="relative" symbol="2" label="Relative only" render="true"/>
      <category value="" symbol="2" label="Relative only" render="true"/>
    </categories>
    <symbols>
      <symbol type="marker" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleMarker" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="name" type="QString" value="triangle"/>
            <Option name="color" type="QString" value="0,0,0,255"/>
            <Option name="outline_color" type="QString" value="255,255,255,255"/>
            <Option name="outline_width" type="QString" value="0.2"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="3.2"/>
            <Option name="size_unit" type="QString" value="MM"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="marker" name="1" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleMarker" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="name" type="QString" value="square"/>
            <Option name="color" type="QString" value="86,180,233,255"/>
            <Option name="outline_color" type="QString" value="0,0,0,255"/>
            <Option name="outline_width" type="QString" value="0.2"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="3"/>
            <Option name="size_unit" type="QString" value="MM"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="outlineColor" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="type" type="int" value="3"/>
                  <Option name="expression" type="QString" value="CASE WHEN &quot;absolute_decision&quot; = 'uncheckable' THEN '204,121,167,255' WHEN &quot;absolute_decision&quot; = 'rejected' THEN '213,94,0,255' ELSE '0,0,0,255' END"/>
                </Option>
                <Option name="outlineWidth" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="type" type="int" value="3"/>
                  <Option name="expression" type="QString" value="CASE WHEN &quot;absolute_decision&quot; IN ('uncheckable', 'rejected') THEN 0.9 ELSE 0.2 END"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol type="marker" name="2" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleMarker" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="0,114,178,255"/>
            <Option name="outline_color" type="QString" value="255,255,255,255"/>
            <Option name="outline_width" type="QString" value="0.2"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="2.4"/>
            <Option name="size_unit" type="QString" value="MM"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="size" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="type" type="int" value="3"/>
                  <Option name="expression" type="QString" value="coalesce(scale_linear(&quot;sigma_si&quot;, 0, coalesce(maximum(&quot;sigma_si&quot;), 1), 1.8, 6.0), 2.4)"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <labeling type="simple">
    <settings>
      <text-style fieldName="station" fontSize="8" textColor="0,0,0,255"/>
      <placement placement="6" dist="1.5"/>
    </settings>
  </labeling>
</qgis>
