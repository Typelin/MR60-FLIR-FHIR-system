/** @file
 * @brief ACS Measurement Area API
 * @author Teledyne FLIR 
 * @copyright Copyright 2023: Teledyne FLIR 
 */

#ifndef ACS_MEASUREMENT_AREA_H
#define ACS_MEASUREMENT_AREA_H

#include <acs/common.h>

#ifdef __cplusplus
extern "C"
{
#endif

    /** @struct ACS_AreaDimensions
     *  @brief Struct describing area calculation for specified measurement tool.
     * 
     *  @note   Some fields are only applicable for specific measurement tools. See description for each field for details.
     *  @note   When field is inapplicable for a specified measurement type, field's value will evaluate to default value of 0.0.
     *  @note   Unit of area value (area, height, width, length, radiusX, radiusY) is determined by the distance unit set for the image (when the image was captured), see @ref ACS_ThermalImage_getDistanceUnit.
     */
    typedef struct ACS_AreaDimensions_
    {
        double area;             //!< Area dimension value - only applicable for rectangle and circle (evaluates to 0.0 for other types)
        double height;           //!< Height dimension value - only applicable for rectangle (evaluates to 0.0 for other types)
        double width;            //!< Width dimension value - only applicable for rectangle (evaluates to 0.0 for other types)
        double length;           //!< Length dimension value - only applicable for line (evaluates to 0.0 for other types)
        double radiusX;          //!< Radius X dimension value - only applicable for ellipse (evaluates to 0.0 for other types)
        double radiusY;          //!< Radius Y dimension value - only applicable for ellipse (evaluates to 0.0 for other types)
        bool valid;              //!< Dimension status - true when calculation is valid and accurate, otherwise false
    } ACS_AreaDimensions;

    /** @struct ACS_MeasurementArea
        @brief Represents the area aspect of measurements types which have an area. */
    typedef struct ACS_MeasurementArea_ ACS_MeasurementArea;

    /** @brief Get the width of the area.
     * 
     *  @note All position coordinates (x, y) and dimension values (width, height) are expressed in pixels relative to the thermal image resolution. For example, in a 640x480 image, valid coordinates range from (0,0) to (639,479).
     *  @relatesalso    ACS_MeasurementArea
     */
    ACS_API int ACS_MeasurementArea_getWidth(const ACS_MeasurementArea* area);

    /** @brief Get the height of the area.
     * 
     *  @note All position coordinates (x, y) and dimension values (width, height) are expressed in pixels relative to the thermal image resolution. For example, in a 640x480 image, valid coordinates range from (0,0) to (639,479).
     *  @relatesalso    ACS_MeasurementArea
     */
    ACS_API int ACS_MeasurementArea_getHeight(const ACS_MeasurementArea* area);

    /** @brief See if area calculations are enabled.
     *
     *  @return         true if area is calculated
     *  @relatesalso    ACS_MeasurementArea
     */
    ACS_API bool ACS_MeasurementArea_getAreaCalc(const ACS_MeasurementArea* area);

    /** @brief Enable area calculations.
     *  @relatesalso    ACS_MeasurementArea
     */
    ACS_API void ACS_MeasurementArea_setAreaCalc(ACS_MeasurementArea* area, bool enable);

    /** @brief Get area dimensions, these are only valid if area calculations are enabled
     *  @relatesalso    ACS_MeasurementArea
     */
    ACS_API ACS_AreaDimensions ACS_MeasurementArea_getAreaDimensions(const ACS_MeasurementArea* area);

#ifdef __cplusplus
}
#endif

#endif // ACS_MEASUREMENT_AREA_H
