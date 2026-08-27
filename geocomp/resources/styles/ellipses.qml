<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  Error ellipses (FR-901, FR-904, specs/19 section 3).

  Outline heavy, fill almost absent. An ellipse is a boundary, and a solid one
  hides the station it belongs to and every observation running through it.

  The exaggeration factor and the confidence level are stated by the layer
  name, which GeoComp composes when it builds the layer, and repeated on every
  feature so a selected ellipse says what it is. Neither is a decoration:
  specs/19 calls an unstated exaggeration the one thing that turns a quality
  visualisation into a misrepresentation.
-->
<qgis version="3.34.0" styleCategories="Symbology|Fields|Forms">
  <renderer-v2 type="singleSymbol" forceraster="0" symbollevels="0" enableorderby="0">
    <symbols>
      <symbol type="fill" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="color" type="QString" value="213,94,0,26"/>
            <Option name="outline_color" type="QString" value="213,94,0,255"/>
            <Option name="outline_width" type="QString" value="0.4"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="style" type="QString" value="solid"/>
            <Option name="joinstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
