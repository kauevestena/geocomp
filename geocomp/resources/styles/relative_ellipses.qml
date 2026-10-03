<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  Relative error ellipses (specs/19 section 3 item 4; P12c-6): how well the
  line between two stations is known, drawn at the line's middle.

  The absolute ellipses' treatment in another colour, dashed, so the two can be
  shown together and told apart: outline heavy, fill almost absent.

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
            <Option name="color" type="QString" value="0,114,178,26"/>
            <Option name="outline_color" type="QString" value="0,114,178,255"/>
            <Option name="outline_width" type="QString" value="0.4"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="outline_style" type="QString" value="dash"/>
            <Option name="style" type="QString" value="solid"/>
            <Option name="joinstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
