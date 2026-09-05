<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  Adjusted stations (FR-900, FR-904, specs/19 section 2).

  Uncertainty maps to size, which is the convention across every GeoComp
  layer: a reader scanning the map sees where the network is weak without
  consulting a legend. Constraint status maps to shape, because it is
  categorical; a fixed station is a different kind of thing from an estimated
  one, not a more certain one.

  Colours are from the Okabe-Ito palette, which stays distinguishable under
  every common colour-vision deficiency and survives greyscale printing.
  These layers end up in technical reports.

  Edit this file, or restyle the layer and save over it. GeoComp applies a
  style; it does not contain one.
-->
<qgis version="3.34.0" styleCategories="Symbology|Fields|Forms">
  <renderer-v2 type="categorizedSymbol" attr="constraint" forceraster="0" symbollevels="0" enableorderby="0">
    <categories>
      <category value="fixed" symbol="0" label="Fixed" render="true"/>
      <category value="weighted" symbol="1" label="Weighted" render="true"/>
      <category value="free" symbol="2" label="Estimated" render="true"/>
      <category value="" symbol="2" label="Estimated" render="true"/>
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
            <Option name="size" type="QString" value="3"/>
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
            <Option name="size" type="QString" value="2.6"/>
            <Option name="size_unit" type="QString" value="MM"/>
          </Option>
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
                  <Option name="expression" type="QString" value="coalesce(scale_linear(&quot;positional_uncertainty&quot;, 0, coalesce(maximum(&quot;positional_uncertainty&quot;), 1), 1.8, 6.0), 2.4)"/>
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
