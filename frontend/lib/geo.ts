import { feature, mesh } from "topojson-client";
import type { Topology, GeometryCollection } from "topojson-specification";
import type { FeatureCollection, MultiLineString, Polygon, MultiPolygon } from "geojson";

// us-atlas ships a pre-built TopoJSON file
import usTopology from "us-atlas/counties-10m.json";

const topo = usTopology as unknown as Topology;

// FIPS prefixes to exclude (AK, HI, territories)
const EXCLUDED_FIPS = ["02", "15", "60", "66", "69", "72", "78"];

function isExcluded(id: string): boolean {
  const prefix = id.padStart(5, "0").slice(0, 2);
  return EXCLUDED_FIPS.includes(prefix);
}

/** All continental US county polygons as GeoJSON */
export function getUSCountiesGeoJSON(): FeatureCollection<Polygon | MultiPolygon> {
  const counties = feature(
    topo,
    topo.objects.counties as GeometryCollection
  ) as FeatureCollection<Polygon | MultiPolygon>;

  counties.features = counties.features.filter(
    (f) => !isExcluded(String(f.id))
  );

  // Ensure every feature has a padded FIPS id in properties
  counties.features.forEach((f, idx) => {
    const fips = String(f.id).padStart(5, "0");
    f.properties = { ...f.properties, fips };
    f.id = idx; // numeric id for MapLibre feature-state
  });

  return counties;
}

/** State boundary lines (interior only, for rendering between states) */
export function getUSStatesBorders(): MultiLineString {
  const states = topo.objects.states as GeometryCollection;
  return mesh(topo, states, (a, b) => a !== b) as MultiLineString;
}

/** Nation outline */
export function getUSNationOutline(): MultiLineString {
  const nation = topo.objects.nation as GeometryCollection;
  return mesh(topo, nation) as MultiLineString;
}
