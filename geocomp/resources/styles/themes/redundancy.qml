<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  Redundancy number (FR-902; specs/19 section 4, P12b).

  The map specs/19 singles out: a network can pass every test while holding
  observations whose blunders no test could see, and this is where they show.
  r is the share of an error that appears in the observation's own residual.
  Below 0.01 GeoComp calls an observation uncheckable (UNCHECKABLE_REDUNDANCY
  in core/statistics/reliability.py) and its MDB is not finite. The class
  expression makes that test itself, so the uncheckable class and the first
  band meet exactly at 0.01 (they once left a gap below it, where an r was
  drawn in no class), and an r a rounding error below zero is uncheckable. The other
  bands — 0.1, 0.3, 0.5 — are GeoComp's reading aid, not a standard: at 0.5
  and above at least half of a blunder shows in its own residual.

  Colours are Okabe-Ito, distinguishable under every common colour-vision
  deficiency; worse is warmer and wider, so the map reads in greyscale too.
  Uncheckable is drawn black and dashed, as prominently as the worst class:
  an observation whose blunder cannot be detected is not a good observation.
-->
<qgis version="3.34.0" styleCategories="Symbology">
  <renderer-v2 type="graduatedSymbol" attr='CASE WHEN "redundancy" IS NULL THEN -2 WHEN "redundancy" &lt; 0.01 THEN -1 ELSE "redundancy" END' graduatedMethod="GraduatedColor" forceraster="0" symbollevels="0" enableorderby="0">
    <ranges>
      <range lower="-2.5" upper="-1.5" symbol="0" label="Not computed" render="true"/>
      <range lower="-1.5" upper="-0.5" symbol="1" label="Uncheckable (r below 0.01)" render="true"/>
      <range lower="0.01" upper="0.1" symbol="2" label="r 0.01 to 0.1" render="true"/>
      <range lower="0.1" upper="0.3" symbol="3" label="r 0.1 to 0.3" render="true"/>
      <range lower="0.3" upper="0.5" symbol="4" label="r 0.3 to 0.5" render="true"/>
      <range lower="0.5" upper="1.000001" symbol="5" label="r 0.5 to 1" render="true"/>
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
            <Option name="line_color" type="QString" value="0,0,0,255"/>
            <Option name="line_width" type="QString" value="1.0"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="dash"/>
            <Option name="capstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="line" name="2" alpha="1" clip_to_extent="1" force_rhr="0">
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
            <Option name="line_color" type="QString" value="86,180,233,255"/>
            <Option name="line_width" type="QString" value="0.5"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="solid"/>
            <Option name="capstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="line" name="5" alpha="1" clip_to_extent="1" force_rhr="0">
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
    </symbols>
  </renderer-v2>
</qgis>
