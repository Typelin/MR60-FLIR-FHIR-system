/** @file
 * @brief ACS Measurement Polygon API
 * @author Teledyne FLIR 
 * @copyright Copyright 2026: Teledyne FLIR 
 */

#ifndef ACS_MEASUREMENT_POLYGON_H
#define ACS_MEASUREMENT_POLYGON_H

#include <acs/common.h>
#include <acs/measurement_area.h>
#include <acs/measurement_marker.h>
#include <acs/measurement_shape.h>

#ifdef __cplusplus
extern "C"
{
#endif
    
    /** @struct ACS_MeasurementPolygon
        @brief Represents a polygon shaped measurement area.
        @see   Single polygon:
        @see   ACS_Measurements_addPolygon
        @see   ACS_Measurements_findPolygon
        @see   ACS_Measurements_movePolygon
        @see   ACS_Measurements_removePolygon
        @see   Multiple polygons:
        @see   ACS_Measurements_getAllPolygons
        @see   ACS_ListMeasurementPolygon
    */
    typedef struct ACS_MeasurementPolygon_ ACS_MeasurementPolygon;

    /** @brief Set the location and shape of the polygon.
     *
     *  @note All position coordinates (x, y) are expressed in pixels relative to the thermal image resolution. For example, in a 640x480 image, valid coordinates range from (0,0) to (639,479).
     *  @param polygon     The polygon object.
     *  @param points      A list with the polygon's points (vertices) in 2D coordinates.
     *
     *  @remarks        Coordinates should be positive values and within the image. A minimum of 3 points is required to define a polygon.
     *  @relatesalso    ACS_MeasurementPolygon
     */
    ACS_API void ACS_MeasurementPolygon_setPolygon(ACS_MeasurementPolygon* polygon, const ACS_ListPoint* points);

    /** @brief Move the location of the polygon with a given offset. All points (vertices) will be offset with the provided x-axis and y-axis offset value.
     *
     *  @note All position coordinates (x, y) are expressed in pixels relative to the thermal image resolution. For example, in a 640x480 image, valid coordinates range from (0,0) to (639,479).
     *  @param polygon     The polygon object.
     *  @param xOffset     The x-offset to move the polygon, negative values will move it left, positive values will move it right.
     *  @param yOffset     The y-offset to move the polygon, negative values will move it up, positive values will move it down.
     *
     *  @relatesalso    ACS_MeasurementPolygon
     */
    ACS_API void ACS_MeasurementPolygon_offsetPolygon(ACS_MeasurementPolygon* polygon, int xOffset, int yOffset);

    /** @brief Get the points that define the location and shape of the polygon.
     *
     *  @note All position coordinates (x, y) are expressed in pixels relative to the thermal image resolution. For example, in a 640x480 image, valid coordinates range from (0,0) to (639,479).
     *  @param polygon     The polygon object.
     *  @return            A list with the polygon's points (vertices) in 2D coordinates.
     * 
     *  @relatesalso    ACS_MeasurementPolygon
     */
    ACS_API ACS_OWN(ACS_ListPoint*, ACS_ListPoint_free) ACS_MeasurementPolygon_getPolygonPoints(const ACS_MeasurementPolygon* polygon);

    /** @brief Get the area aspect of the measurement.
     *  @relatesalso    ACS_MeasurementPolygon
     */
    ACS_API ACS_BORROW_FROM(const ACS_MeasurementArea*, polygon) ACS_MeasurementPolygon_asMeasurementArea(const ACS_MeasurementPolygon* polygon);

    /** @brief Get the marker aspect of the measurement.
     *  @relatesalso    ACS_MeasurementPolygon
     */
    ACS_API ACS_BORROW_FROM(const ACS_MeasurementMarker*, polygon) ACS_MeasurementPolygon_asMeasurementMarker(const ACS_MeasurementPolygon* polygon);

    /** @brief Get the shape aspect of the measurement.
     *  @relatesalso    ACS_MeasurementPolygon
     */
    ACS_API ACS_BORROW_FROM(const ACS_MeasurementShape*, polygon) ACS_MeasurementPolygon_asMeasurementShape(const ACS_MeasurementPolygon* polygon);

    /** @brief Gets the local thermal parameters for the polygon.
     *  @relatesalso    ACS_LocalThermalParameters
     */
    ACS_API ACS_BORROW_FROM(ACS_LocalThermalParameters*, polygon) ACS_MeasurementPolygon_getLocalThermalParameters(const ACS_MeasurementPolygon* polygon);

#ifdef __cplusplus
}
#endif

#endif // ACS_MEASUREMENT_POLYGON_H
