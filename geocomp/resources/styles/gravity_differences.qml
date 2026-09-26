<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  Gravity differences (FR-700, FR-900, FR-904, specs/12 section 5).

  Categorised by the w-test's decision, like the residuals layer, with one
  difference: "not testable" is drawn as prominently as a blunder candidate,
  in a colour of its own. A gravity network is small and weakly redundant, so
  a difference no blunder in which could be detected is common, and it is the
  warning specs/12 section 5 asks to be shown rather than left in a table.

  A rejected difference stays visible: GeoComp never rejects automatically
  (FR-255), so what is drawn here is a candidate.
-->
<qgis version="3.34.0" styleCategories="Symbology|Fields|Forms">
  <renderer-v2 type="categorizedSymbol" attr="decision" forceraster="0" symbollevels="1" enableorderby="0">
    <categories>
      <category value="rejected" symbol="0" label="Blunder candidate" render="true"/>
      <category value="uncheckable" symbol="1" label="Not testable" render="true"/>
      <category value="accepted" symbol="2" label="Passes the w-test" render="true"/>
      <category value="" symbol="1" label="Not testable" render="true"/>
    </categories>
    <symbols>
      <symbol type="line" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="2" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="213,94,0,255"/>
            <Option name="line_width" type="QString" value="1"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="solid"/>
            <Option name="capstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="line" name="1" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="1" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="204,121,167,255"/>
            <Option name="line_width" type="QString" value="1"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="dash"/>
            <Option name="capstyle" type="QString" value="flat"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="line" name="2" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="0,158,115,255"/>
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
