using System;
using System.Collections.Generic;
using System.Text;
using Datalogics.PDFL;

/*
 *
 * This sample program demonstrates the use of AddDigitalSignature for RFC3161 timestamp signature type.
 *
 * Copyright (c) 2025, Datalogics, Inc. All rights reserved.
 *
 */
namespace AddDigitalSignatureRFC3161
{
    class AddDigitalSignatureRFC3161
    {
        static void Main(string[] args)
        {
            Console.WriteLine("AddDigitalSignatureRFC3161 Sample:");

            using (new Library())
            {
                Console.WriteLine("Initialized the library.");

                String sInput = Library.ResourceDirectory + "Sample_Input/CreateAcroForm2h.pdf";

                String sOutput = "DigSigRFC3161-out.pdf";

                if (args.Length > 0)
                    sInput = args[0];

                if (args.Length > 1)
                    sOutput = args[1];

                Console.WriteLine("Input file: " + sInput);
                Console.WriteLine("Writing to output: " + sOutput);

                using (Document doc = new Document(sInput))
                {
                    using (Datalogics.PDFL.SignDoc sigDoc = new Datalogics.PDFL.SignDoc())
                    {
                        // Setup Sign params
                        sigDoc.FieldID = SignatureFieldID.SearchForFirstUnsignedField;

                        // Set signing attributes
                        sigDoc.DigestCategory = DigestCategory.Sha256;

                        // Set the signature type to be used, RFC3161/TimeStamp.
                        // The available types are defined in the SignatureType enum. Default CMS.
                        sigDoc.DocSignType = SignatureType.RFC3161;

                        // Setup Save params
                        sigDoc.OutputPath = sOutput;

                        // Finally, sign and save the document
                        sigDoc.AddDigitalSignature(doc);

                        Console.WriteLine();
                    }
                }
            }
        }
    }
}
