import os
import folium

from src.tools.routing import COORDS


def generate_route_map(
    original_coords: list,
    alt_coords: list,
    risk_polygon: list,
    output_path: str = "output/route_map.html",
) -> str:
    """Generate an HTML route map and return the absolute path."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    m = folium.Map(location=[24.0, -90.0], zoom_start=5, tiles="OpenStreetMap")

    # City markers — COORDS is [lon, lat], folium needs [lat, lon]
    city_labels = {"veracruz": "Veracruz", "houston": "Houston", "tampa": "Tampa", "panama": "Panama"}
    for key, label in city_labels.items():
        if key in COORDS:
            lon, lat = COORDS[key]
            folium.Marker(location=[lat, lon], popup=label, tooltip=label).add_to(m)

    # Original route — red polyline (coords are [lon, lat], flip to [lat, lon])
    if original_coords:
        folium.PolyLine(
            locations=[[c[1], c[0]] for c in original_coords],
            color="#cc0000",
            weight=4,
            tooltip="Original route",
        ).add_to(m)

    # Alternative route — green polyline
    if alt_coords:
        folium.PolyLine(
            locations=[[c[1], c[0]] for c in alt_coords],
            color="#008800",
            weight=4,
            tooltip="Alternative route",
        ).add_to(m)

    # Risk zone polygon — semi-transparent red
    if risk_polygon:
        folium.Polygon(
            locations=[[c[1], c[0]] for c in risk_polygon],
            color="#990000",
            fill=True,
            fill_opacity=0.25,
            tooltip="Risk zone",
        ).add_to(m)

    abs_path = os.path.abspath(output_path)
    m.save(abs_path)
    return abs_path
