<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  Minimal detectable bias (FR-902; specs/19 section 4, P12b).

  Drawn as the displacement an undetectable blunder would put at the far end
  of the sight, in metres (the mdb_displacement field): a length's MDB is one
  already, an angle's is the MDB times its sight. On the raw MDB a 2-arcsecond
  direction and a 1 mm distance could not share a scale. An observation whose
  MDB has no length — a gravity difference in a combined solution — is drawn
  thin and grey, and its MDB is in the table.

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
  <renderer-v2 type="graduatedSymbol" attr='CASE WHEN "redundancy" IS NULL THEN -2 WHEN "mdb" IS NULL THEN -1 WHEN "mdb_displacement" IS NULL THEN -3 ELSE "mdb_displacement" END' graduatedMethod="GraduatedColor" forceraster="0" symbollevels="0" enableorderby="0">
    <ranges>
      <range lower="-3.5" upper="-2.5" symbol="0" label="MDB not a length (see the table)" render="true"/>
      <range lower="-2.5" upper="-1.5" symbol="1" label="Not computed" render="true"/>
      <range lower="-1.5" upper="-0.5" symbol="2" label="Uncheckable: no finite MDB" render="true"/>
      <range lower="0" upper="0.25" symbol="3" label="" render="true"/>
      <range lower="0.25" upper="0.5" symbol="4" label="" render="true"/>
      <range lower="0.5" upper="0.75" symbol="5" label="" render="true"/>
      <range lower="0.75" upper="1" symbol="6" label="" render="true"/>
    </ranges>
    <symbols>
      <symbol type="line" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="150,150,150,255"/>
            <Option name="line_width" type="QString" value="0.3"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="solid"/>
            <Option name="capstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="line" name="1" alpha="1" clip_to_extent="1" force_rhr="0">
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
      <symbol type="line" name="2" alpha="1" clip_to_extent="1" force_rhr="0">
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
      <symbol type="line" name="3" alpha="1" clip_to_extent="1" force_rhr="0">
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
            <Option name="line_color" type="QString" value="230,159,0,255"/>
            <Option name="line_width" type="QString" value="0.7"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="solid"/>
            <Option name="capstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="line" name="6" alpha="1" clip_to_extent="1" force_rhr="0">
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
