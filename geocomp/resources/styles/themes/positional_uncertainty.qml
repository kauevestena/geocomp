<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  Positional uncertainty (FR-902; specs/19 section 4, P12b).

  Uncertainty maps to size — the convention across every GeoComp layer —
  and to colour, so the weakest stations stand out at any scale.

  The four data classes are FITTED to the layer when GeoComp loads it: their
  bounds are the quartiles of the values present, so each holds about a
  quarter of the features and the map shows where THIS network is weakest
  (core/visualization/classes.py). The bounds below are placeholders. What
  this file fixes is how each class looks — the colour and the size — and the
  classes that are not data: uncheckable, not computed. Restyle freely; to keep
  your own bounds, save the style under another name.

  Colours are Okabe-Ito, distinguishable under every common colour-vision
  deficiency; worse is warmer and wider, so the map reads in greyscale too.
  Uncheckable is drawn black and dashed, as prominently as the worst class:
  an observation whose blunder cannot be detected is not a good observation.
-->
<qgis version="3.34.0" styleCategories="Symbology">
  <renderer-v2 type="graduatedSymbol" attr='CASE WHEN "positional_uncertainty" IS NULL THEN -2 ELSE "positional_uncertainty" END' graduatedMethod="GraduatedColor" forceraster="0" symbollevels="0" enableorderby="0">
    <ranges>
      <range lower="-2.5" upper="-1.5" symbol="0" label="Not computed" render="true"/>
      <range lower="0" upper="0.25" symbol="1" label="" render="true"/>
      <range lower="0.25" upper="0.5" symbol="2" label="" render="true"/>
      <range lower="0.5" upper="0.75" symbol="3" label="" render="true"/>
      <range lower="0.75" upper="1" symbol="4" label="" render="true"/>
    </ranges>
    <symbols>
      <symbol type="marker" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleMarker" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="150,150,150,255"/>
            <Option name="outline_color" type="QString" value="35,35,35,255"/>
            <Option name="outline_width" type="QString" value="0.2"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="1.6"/>
            <Option name="size_unit" type="QString" value="MM"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="marker" name="1" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleMarker" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="0,114,178,255"/>
            <Option name="outline_color" type="QString" value="35,35,35,255"/>
            <Option name="outline_width" type="QString" value="0.2"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="2.0"/>
            <Option name="size_unit" type="QString" value="MM"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="marker" name="2" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleMarker" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="86,180,233,255"/>
            <Option name="outline_color" type="QString" value="35,35,35,255"/>
            <Option name="outline_width" type="QString" value="0.2"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="2.8"/>
            <Option name="size_unit" type="QString" value="MM"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="marker" name="3" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleMarker" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="230,159,0,255"/>
            <Option name="outline_color" type="QString" value="35,35,35,255"/>
            <Option name="outline_width" type="QString" value="0.2"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="3.6"/>
            <Option name="size_unit" type="QString" value="MM"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="marker" name="4" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleMarker" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="213,94,0,255"/>
            <Option name="outline_color" type="QString" value="35,35,35,255"/>
            <Option name="outline_width" type="QString" value="0.2"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="4.4"/>
            <Option name="size_unit" type="QString" value="MM"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
