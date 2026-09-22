<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  GNSS trajectory (FR-357, FR-902, specs/11 section 4.3).

  One point per solution epoch, categorised by RTKLIB's Q. This is the map
  specs/11 section 5 calls "the fastest way to see what a campaign actually
  achieved": a fixed solution and a float one differ by two orders of magnitude
  in accuracy and by nothing at all in appearance, so the status is the first
  thing the symbol has to say.

  Fixed is the largest and most saturated symbol, and everything else is drawn
  smaller and paler in roughly descending order of trust. That ordering is the
  point: a trajectory that is mostly pale is one whose ambiguities did not
  resolve, and it should look like that from across the room.

  Okabe-Ito, as everywhere else in GeoComp.
-->
<qgis version="3.34.0" styleCategories="Symbology|Fields|Forms">
  <renderer-v2 type="categorizedSymbol" attr="status" forceraster="0" symbollevels="0" enableorderby="0">
    <categories>
      <category value="FIXED" symbol="0" label="Fixed (ambiguities resolved)" render="true"/>
      <category value="FLOAT" symbol="1" label="Float" render="true"/>
      <category value="DGPS" symbol="2" label="DGPS" render="true"/>
      <category value="SBAS" symbol="3" label="SBAS" render="true"/>
      <category value="PPP" symbol="4" label="PPP" render="true"/>
      <category value="SINGLE" symbol="5" label="Single (no differential)" render="true"/>
    </categories>
    <symbols>
      <symbol type="marker" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleMarker" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="0,114,178,255"/>
            <Option name="outline_color" type="QString" value="255,255,255,180"/>
            <Option name="outline_width" type="QString" value="0.1"/>
            <Option name="size" type="QString" value="2.2"/>
            <Option name="size_unit" type="QString" value="MM"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="marker" name="1" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleMarker" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="230,159,0,220"/>
            <Option name="outline_color" type="QString" value="255,255,255,160"/>
            <Option name="outline_width" type="QString" value="0.1"/>
            <Option name="size" type="QString" value="1.8"/>
            <Option name="size_unit" type="QString" value="MM"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="marker" name="2" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleMarker" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="0,158,115,200"/>
            <Option name="outline_color" type="QString" value="255,255,255,140"/>
            <Option name="outline_width" type="QString" value="0.1"/>
            <Option name="size" type="QString" value="1.6"/>
            <Option name="size_unit" type="QString" value="MM"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="marker" name="3" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleMarker" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="86,180,233,200"/>
            <Option name="outline_color" type="QString" value="255,255,255,140"/>
            <Option name="outline_width" type="QString" value="0.1"/>
            <Option name="size" type="QString" value="1.6"/>
            <Option name="size_unit" type="QString" value="MM"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="marker" name="4" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleMarker" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="204,121,167,200"/>
            <Option name="outline_color" type="QString" value="255,255,255,140"/>
            <Option name="outline_width" type="QString" value="0.1"/>
            <Option name="size" type="QString" value="1.6"/>
            <Option name="size_unit" type="QString" value="MM"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="marker" name="5" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleMarker" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="160,160,160,170"/>
            <Option name="outline_color" type="QString" value="255,255,255,120"/>
            <Option name="outline_width" type="QString" value="0.1"/>
            <Option name="size" type="QString" value="1.3"/>
            <Option name="size_unit" type="QString" value="MM"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
