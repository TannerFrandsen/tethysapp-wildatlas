$(document).ready(function() {
    let map = TETHYS_MAP_VIEW.getMap();
    let layers = map.getLayers().getArray();

    // Find the first layer that has tethys_data and animal sightings defined
    let layer = layers.find(layer => layer.tethys_data !== undefined && layer.tethys_data.layer_id === "Animal Sightings" );
    if (layer) {
        const svgStyleFunct = function(feature) {
            const iconPath = feature.A.pin_path || '/static/wildatlas/images/default_icon.svg';
            feature.A.Date = formatDateToLocal(feature.A.Date)
            return new ol.style.Style({
                image: new ol.style.Icon({
                    src: iconPath,
                    scale: 0.08, // Adjust the scale as needed
                    anchor: [0.5, 0.5], // Adjust the anchor point as needed
                    anchorXUnits: 'fraction',
                    anchorYUnits: 'fraction'
                })
            });
        };
        layer.setStyle(svgStyleFunct);

    }
});

function formatDateToLocal(isoString) {
    const date = new Date(isoString);
    if (isNaN(date)) {
        return isoString; // fallback if invalid
    }
    return date.toLocaleString(); // formats to user's locale and timezone
}