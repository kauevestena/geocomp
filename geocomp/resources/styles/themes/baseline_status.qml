<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  GNSS solution status (FR-902; specs/19 section 4, P12b).

  The status of the run each baseline came from, in the trajectory layer's
  colours, so a fixed baseline and a fixed epoch look alike. Single is
  dashed: a baseline from undifferenced positions is not a baseline anyone
  should combine without noticing.
-->
<qgis version="3.34.0" styleCategories="Symbology">
  <renderer-v2 type="categorizedSymbol" attr="solution_status" forceraster="0" symbollevels="0" enableorderby="0">
    <categories>
      <category value="FIXED" symbol="0" label="Fixed (ambiguities resolved)" render="true"/>
      <category value="FLOAT" symbol="1" label="Float" render="true"/>
      <category value="DGPS" symbol="2" label="DGPS" render="true"/>
      <category value="SBAS" symbol="3" label="SBAS" render="true"/>
      <category value="PPP" symbol="4" label="PPP" render="true"/>
      <category value="SINGLE" symbol="5" label="Single (no differential)" render="true"/>
      <category value="" symbol="6" label="Not recorded" render="true"/>
    </categories>
    <symbols>
      <symbol type="line" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="0,114,178,255"/>
            <Option name="line_width" type="QString" value="0.7"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="solid"/>
            <Option name="capstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="line" name="1" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="230,159,0,255"/>
            <Option name="line_width" type="QString" value="0.6"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="solid"/>
            <Option name="capstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="line" name="2" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="0,158,115,255"/>
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
            <Option name="line_color" type="QString" value="86,180,233,255"/>
            <Option name="line_width" type="QString" value="0.5"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="solid"/>
            <Option name="capstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="line" name="4" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="204,121,167,255"/>
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
            <Option name="line_color" type="QString" value="150,150,150,255"/>
            <Option name="line_width" type="QString" value="0.5"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="dash"/>
            <Option name="capstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="line" name="6" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="150,150,150,255"/>
            <Option name="line_width" type="QString" value="0.3"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="dot"/>
            <Option name="capstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
