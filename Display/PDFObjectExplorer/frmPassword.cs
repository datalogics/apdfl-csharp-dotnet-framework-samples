using System;
using System.Windows.Forms;

/*
 * Copyright (c) 2007-2023, Datalogics, Inc. All rights reserved.
 *
 * Demonstrates a GUI-based browser for PDF objects.  This dialog prompts for passwords.
 */

namespace PDF_Object_Explorer
{
    public partial class frmPassword : Form
    {
        public string password;

        
        public frmPassword()
        {
            InitializeComponent();
        }

        private void Form1_Load(object sender, EventArgs e)
        {

        }

        private void frmPassword_Load(object sender, EventArgs e)
        {
            txtPassword.Focus();
        }

        private void maskedTextBox1_MaskInputRejected(object sender, MaskInputRejectedEventArgs e)
        {
          
        }


        private void btnOK_Click(object sender, EventArgs e)
        {
            password = txtPassword.Text;
            this.Close();
        }

        private void label1_Click(object sender, EventArgs e)
        {

        }

        private void btnCancel_Click(object sender, EventArgs e)
        {
            password = "";
            this.Close();
        }
    }
}
