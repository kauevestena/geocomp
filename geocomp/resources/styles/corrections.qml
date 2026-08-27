<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  Coordinate correction vectors (FR-900, FR-901, FR-904).

  The shift from each station's approximate position to its adjusted one, drawn
  as an arrow. Unlike a residual, this is a genuine two-dimensional vector, so
  it is drawn at a scale, and the layer name states that scale.

  Arrows rather than plain lines because direction is the information: a
  cluster of corrections all pointing the same way says the approximate
  coordinates were shifted as a block, while a single long one pointing
  somewhere of its own says a blunder is near that station.
-->
<qgis version="3.34.0" styleCategories="Symbology|Fields|Forms">
  <renderer-v2 type="singleSymbol" forceraster="0" symbollevels="0" enableorderby="0">
    <symbols>
      <symbol type="line" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="ArrowLine" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="arrow_width" type="QString" value="0.5"/>
            <Option name="arrow_width_unit" type="QString" value="MM"/>
            <Option name="arrow_start_width" type="QString" value="0.5"/>
            <Option name="arrow_start_width_unit" type="QString" value="MM"/>
            <Option name="head_length" type="QString" value="2"/>
            <Option name="head_length_unit" type="QString" value="MM"/>
            <Option name="head_thickness" type="QString" value="1.6"/>
            <Option name="head_thickness_unit" type="QString" value="MM"/>
            <Option name="head_type" type="QString" value="0"/>
            <Option name="arrow_type" type="QString" value="0"/>
            <Option name="is_curved" type="QString" value="0"/>
            <Option name="is_repeated" type="QString" value="0"/>
            <Option name="ring_filter" type="QString" value="0"/>
          </Option>
          <symbol type="fill" name="@0@0" alpha="1" clip_to_extent="1" force_rhr="0">
            <layer class="SimpleFill" pass="0" locked="0" enabled="1">
              <Option type="Map">
                <Option name="color" type="QString" value="204,121,167,255"/>
                <Option name="outline_color" type="QString" value="204,121,167,255"/>
                <Option name="outline_width" type="QString" value="0"/>
                <Option name="outline_style" type="QString" value="solid"/>
                <Option name="style" type="QString" value="solid"/>
              </Option>
            </layer>
          </symbol>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
