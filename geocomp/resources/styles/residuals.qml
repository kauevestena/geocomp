<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  Residual vectors (FR-900, FR-902, FR-904, specs/19 section 2).

  Significance is categorical, not continuous: the w-test returns one of three
  answers and the map shows three symbols. A continuous ramp over the
  standardised residual would blur the decision that was actually made.

  A rejected observation stays visible. One that vanished from the map could
  not be reconsidered, and reconsidering is the normal case: GeoComp never
  rejects automatically (FR-255), so what is drawn here is a candidate.

  Not testable is a fourth colour rather than a shade of a third, because an
  observation with a redundancy number near zero is not a passing observation.
  Nothing was tested at all.
-->
<qgis version="3.34.0" styleCategories="Symbology|Fields|Forms">
  <renderer-v2 type="categorizedSymbol" attr="decision" forceraster="0" symbollevels="1" enableorderby="0">
    <categories>
      <category value="rejected" symbol="0" label="Blunder candidate" render="true"/>
      <category value="accepted" symbol="1" label="Passes the w-test" render="true"/>
      <category value="uncheckable" symbol="2" label="Not testable" render="true"/>
      <category value="" symbol="2" label="Not testable" render="true"/>
    </categories>
    <symbols>
      <symbol type="line" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="2" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="213,94,0,255"/>
            <Option name="line_width" type="QString" value="0.9"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="solid"/>
            <Option name="capstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="line" name="1" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleLine" pass="1" locked="0" enabled="1">
          <Option type="Map">
            <Option name="line_color" type="QString" value="0,158,115,255"/>
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
            <Option name="line_color" type="QString" value="120,120,120,255"/>
            <Option name="line_width" type="QString" value="0.5"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="line_style" type="QString" value="dash"/>
            <Option name="capstyle" type="QString" value="flat"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
