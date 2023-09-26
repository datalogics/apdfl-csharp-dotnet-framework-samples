using System;
using Datalogics.PDFL;
using System.Collections.Generic;

/*
 * 
 * This sample demonstrates merging one PDF document into another. The program
 * prompts the user to enter the names of two PDF files, and then inserts the content 
 * of the second PDF file into the first PDF file and saves the result in a third PDF file.
 *
 * Copyright (c) 2007-2023, Datalogics, Inc. All rights reserved.
 *
 */

namespace MergePDF
{
    class MergePDF
    {
        static void Main(string[] args)
        {
            Console.WriteLine("MergePDF with Attachments or Portfolio sample:");

            using (Library lib = new Library())
            {
                String sInput1 = Library.ResourceDirectory + "Sample_Input/merge_pdf1.pdf";
                String sInput2 = Library.ResourceDirectory + "Sample_Input/merge_pdf2.pdf";
                String sOutput = "MergePDF-out.pdf";

                if (args.Length > 0)
                    sInput1 = args[0];

                if (args.Length > 1)
                    sInput2 = args[1];

                if (args.Length > 2)
                    sOutput = args[2];

                using (Document doc1 = new Document(sInput1))
                {
                    try
                    {
                        Document docMain = new Document(sInput2);

                        IList<FileAttachment> attachments = doc1.Attachments;
                        Console.WriteLine("\nDocument " + sInput1 + " has " + attachments.Count + " attachments");

                        if (doc1.Root.Contains("Names"))
                        {
                            PDFDict names = (PDFDict)doc1.Root.Get("Names");
                            if (names.Contains("EmbeddedFiles"))
                            {
                                IList<FileAttachment> attachmentsTemp = doc1.Attachments;
                                Console.WriteLine("\nDocument " + sInput1 + " has " + attachmentsTemp.Count + " attachments");
                                foreach (FileAttachment file in attachmentsTemp)
                                {
                                    Console.WriteLine("Attachement is "+ file.FileName );
                                    if (file.FileName.EndsWith(".pdf") )
                                    {
                                        file.SaveToFile("temp.pdf");
                                        using (Document tempPDF = new Document("temp.pdf"))
                                        {
                                            docMain.InsertPages(Document.LastPage, tempPDF, 0, Document.AllPages, PageInsertFlags.Bookmarks | PageInsertFlags.Threads |
                                            PageInsertFlags.DoNotMergeFonts | PageInsertFlags.DoNotResolveInvalidStructureParentReferences | PageInsertFlags.DoNotRemovePageInheritance);
                                        }
                                    }
                                }
                            }
                            else
                            {
                                Console.WriteLine("Document does not have EmbeddedFiles entry in Names dict");
                            }
                        }
                        else
                        {
                             Console.WriteLine("Document does not have Names entry in catalog");
                        }

                        // For best performance processing large documents, set the following flags.
                        Console.WriteLine("Saving to " + sOutput);
                        docMain.Save(SaveFlags.Full | SaveFlags.SaveLinearizedNoOptimizeFonts | SaveFlags.Compressed, sOutput);

                    }
                    catch(LibraryException ex)
                    {
                        Console.Out.WriteLine(ex.Message);
                    }
                }
            }
        }
    }
}

