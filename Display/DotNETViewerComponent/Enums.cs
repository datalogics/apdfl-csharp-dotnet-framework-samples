/*
Copyright (C) 2008-2023, Datalogics, Inc. All rights reserved.
 
*/

/*
 * Enums.cs
 * 
 * Contains a the declarations of all enumerations used in DotNETViewerComponent
 */

using System;
using System.Text;
using System.Collections.Generic;

namespace DotNETViewerComponent
{
    // Possible Display Modes
    public enum PageViewMode
    {
        continuousPage,
        singlePage,
        notApplicable
    };

    // Possible modes for the application
    public enum ApplicationFunctionMode
    {
        ZoomMode,
        MarqueeZoomMode,
        ScrollMode,
        TargetMode,
        AnnotationEditMode,
        AnnotationShapeCreateMode,
    };

    // Highlight states
    public enum ApplicationHighlight
    {
        Highlight,
        NoHighlight
    };

    // Zoom fit modes
    public enum FitModes
    {
        FitNone,
        FitWidth,
        FitPage
    };
}
