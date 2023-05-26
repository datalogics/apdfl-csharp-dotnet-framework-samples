/*
Copyright (C) 2008-2023, Datalogics, Inc. All rights reserved.
 
*/

/*
 * frmLineWidth.cs
 * 
 * This form is for the user when they would like to set the line
 * width to a size not defined in the drop down list.
 */

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Windows.Forms;

namespace DotNETViewerComponent
{
    public partial class frmLineWidth : Form
    {
        #region Members
        public int lineWidth;
        public int savedLineWidth;
        public int newLineWidth;
        #endregion

        #region Constructor
        public frmLineWidth()
        {
            InitializeComponent();
        }
        #endregion

        #region Events
        /**
         * frmLineWidth_Load - 
         * 
         * when the form loads set the value of the control
         * to the current lineWidth and save a copy of the 
         * original lineWidth.
         */
        private void frmLineWidth_Load(object sender, EventArgs e)
        {
            lineWidthCtrl.Value = lineWidth;
            savedLineWidth = lineWidth;
        }

        /**
         * lineWidthCtrl_ValueChanged - 
         * 
         * save the new line width when the control is changed
         */
        private void lineWidthCtrl_ValueChanged(object sender, EventArgs e)
        {
            newLineWidth = (int)lineWidthCtrl.Value;
        }

        /**
         * btnOK_Click - 
         * 
         * set the lineWidth to the value of the control
         */
        private void btnOK_Click(object sender, EventArgs e)
        {
            lineWidth = (int)lineWidthCtrl.Value;
            this.Close();
        }

        /**
         * btnCancel_Click - 
         * 
         * on cancel set the lineWidth to the saveLineWidth (the
         * line width that was originally set when this form was opened)
         */
        private void btnCancel_Click(object sender, EventArgs e)
        {
            lineWidth = savedLineWidth;
            this.Close();
        }
        #endregion
    }
}