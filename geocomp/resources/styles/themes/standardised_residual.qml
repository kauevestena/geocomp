<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  Standardised residual |w| (FR-902; specs/19 section 4, P12b).

  Fixed bands of one, two and three: w is a standard normal variate when the
  model holds, so |w| below 1 is ordinary in every network and 3 is not. The
  bands are a reading aid; the decision the w-test made at its own critical
  value is the layer's default style, and this map does not replace it.

  Colours are Okabe-Ito, distinguishable under every common colour-vision
  deficiency; worse is warmer and wider, so the map reads in greyscale too.
  Uncheckable is drawn black and dashed, as prominently as the worst class:
  an observation whose blunder cannot be detected is not a good observation.
-->
<qgis version="3.34.0" styleCategories="Symbology">
  <renderer-v2 type="graduatedSymbol" attr='CASE WHEN "standardised" IS NULL THEN -2 ELSE abs("standardised") END' graduatedMethod="GraduatedColor" forceraster="0" symbollevels="0" enableorderby="0">
    <ranges>
      <range lower="-2.5" upper="-1.5" symbol="0" label="Not tested" render="true"/>
      <range lower="0" upper="1" symbol="1" label="|w| below 1" render="true"/>
      <range lower="1" upper="2" symbol="2" label="|w| 1 to 2" render="true"/>
      <range lower="2" upper="3" symbol="3" label="|w| 2 to 3" render="true"/>
      <range lower="3" upper="1000000000000.0" symbol="4" label="|w| 3 or more" render="true"/>
    </ranges>
    <symbols>
      <symbol type="line" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="150,150,150,255"/>
            <Option name="line_width" type="QString" value="0.3"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="dash"/>
            <Option name="capstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="line" name="1" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="0,114,178,255"/>
            <Option name="line_width" type="QString" value="0.4"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="solid"/>
            <Option name="capstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="line" name="2" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="86,180,233,255"/>
            <Option name="line_width" type="QString" value="0.5"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="solid"/>
            <Option name="capstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="line" name="3" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="230,159,0,255"/>
            <Option name="line_width" type="QString" value="0.7"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="solid"/>
            <Option name="capstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="line" name="4" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="213,94,0,255"/>
            <Option name="line_width" type="QString" value="0.9"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="solid"/>
            <Option name="capstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
