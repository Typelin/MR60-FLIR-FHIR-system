/** @file
 * @brief ACS Color API
 * @author Teledyne FLIR
 * @copyright Copyright 2025: Teledyne FLIR
 */

#ifndef ACS_COLOR_H
#define ACS_COLOR_H

#include <acs/common.h>


#ifdef __cplusplus
extern "C"
{
#endif

    /** @brief Color described by Luminance (Y), Chrominance blue (Cb) and Chrominance red (Cr). BT.601 Y 16:235, Cb/Cr 16:240. */
    typedef struct ACS_Ycbcr_
    {
        unsigned char y;    //!< Luminance          unit = 1/255
        unsigned char cb;   //!< Chrominance (blue) unit = 1/255
        unsigned char cr;   //!< Chrominance (red)  unit = 1/255
    } ACS_Ycbcr;

    /** @brief RGB color */
    typedef struct ACS_Rgb_
    {
        unsigned char r;
        unsigned char g;
        unsigned char b;
    } ACS_Rgb;

    /** @struct ACS_ListYcbcr
     * @brief Represents a list of Ycbcr colors.
     * @relatesalso ACS_Ycbcr
     */
    typedef struct ACS_ListYcbcr_ ACS_ListYcbcr;

    /** @brief Retrieves the number of elements in the list.
     * @returns Number of elements in the list.
     * @relatesalso ACS_ListYcbcr
     */
    ACS_API size_t ACS_ListYcbcr_size(const ACS_ListYcbcr* list);


    /**@brief Create an empty list of Ycbcr colors. */
    ACS_API ACS_OWN(ACS_ListYcbcr*, ACS_ListYcbcr_free) ACS_ListYcbcr_create(void);

    /**@brief Frees a list of colors */
    ACS_API void ACS_ListYcbcr_free(const ACS_ListYcbcr* list);

    /** @brief Retrieves item at specified index if it exists.
     * @param index Index of object to retrieve.
     * @remarks returned object is only valid if the index is in range.
     * @returns Valid object if index was in range, otherwise a garbage value.
     * @relatesalso ACS_ListYcbcr
     */
    ACS_API ACS_Ycbcr ACS_ListYcbcr_item(ACS_ListYcbcr* list, size_t index);

    /** @brief Adds a new Ycbcr color to the list.
     * @relatesalso ACS_ListYcbcr
     */
    ACS_API void ACS_ListYcbcr_addItem(ACS_ListYcbcr* list, ACS_Ycbcr newItem);

    /** @brief Removes an item from the list
     * @relatesalso ACS_ListYcbcr
     */
    ACS_API void ACS_ListYcbcr_removeItem(ACS_ListYcbcr* list, ACS_Ycbcr item);

    /** @brief Removes all items from the list.
     * @relatesalso ACS_ListYcbcr
     */
    ACS_API void ACS_ListYcbcr_clear(ACS_ListYcbcr* list);

    /** @brief Convert Ycbcr to RGB
     * @note Converting to and from Ycbcr will not always produce the same value, due to rounding.
     */
    ACS_API ACS_Rgb ACS_Rgb_fromYcbcr(ACS_Ycbcr ycbcr);

    /** @brief Convert RGB to Ycbcr
     * @note Converting to and from Ycbcr will not always produce the same value, due to rounding.
     */
    ACS_API ACS_Ycbcr ACS_Ycbcr_fromRgb(ACS_Rgb rgb);

#ifdef __cplusplus
}
#endif


#endif // ACS_COLOR_H
