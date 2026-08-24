from invoke import Collection, task
from invoke.tasks import Task
import glob
import io
import os
import shutil

# Sample directories built/run by CI. Matches the (proven) GitHub-workflow list
# plus the four Forms Extension samples. Forms Extension and base APDFL LM
# packages are 64-bit only, so everything builds/runs x64.
samples_list = [
    'Annotations/Annotations/',
    'Annotations/InkAnnotations/',
    'Annotations/LinkAnnotation/',
    'Annotations/PolygonAnnotations/',
    'Annotations/PolyLineAnnotations/',
    'ContentCreation/AddElements/',
    'ContentCreation/AddHeaderFooter/',
    'ContentCreation/Clips/',
    'ContentCreation/CreateBookmarks/',
    'ContentCreation/GradientShade/',
    'ContentCreation/MakeDocWithCalGrayColorSpace/',
    'ContentCreation/MakeDocWithCalRGBColorSpace/',
    'ContentCreation/MakeDocWithDeviceNColorSpace/',
    'ContentCreation/MakeDocWithICCBasedColorSpace/',
    'ContentCreation/MakeDocWithIndexedColorSpace/',
    'ContentCreation/MakeDocWithLabColorSpace/',
    'ContentCreation/MakeDocWithSeparationColorSpace/',
    'ContentCreation/NameTrees/',
    'ContentCreation/NumberTrees/',
    'ContentCreation/RemoteGoToActions/',
    'ContentCreation/WriteNChannelTiff/',
    'ContentModification/Action/',
    'ContentModification/AddCollection/',
    'ContentModification/AddQRCode/',
    'ContentModification/ChangeLayerConfiguration/',
    'ContentModification/ChangeLinkColors/',
    'ContentModification/CreateLayer/',
    'ContentModification/ExtendedGraphicStates/',
    'ContentModification/FlattenTransparency/',
    'ContentModification/LaunchActions/',
    'ContentModification/MergePDF/',
    'ContentModification/PageLabels/',
    'ContentModification/PDFObject/',
    'ContentModification/UnderlinesAndHighlights/',
    'ContentModification/Watermark/',
    'Display/DisplayPDF/',
    'Display/DotNETViewer/',
    'Display/DotNETViewerComponent/',
    'Display/PDFObjectExplorer/',
    'DocumentConversion/ColorConvertDocument/',
    'DocumentConversion/ConvertToOffice/',
    'DocumentConversion/CreateDocFromXPS/',
    'DocumentConversion/Factur-XConverter/',
    'DocumentConversion/PDFAConverter/',
    'DocumentConversion/PDFXConverter/',
    'DocumentConversion/ZUGFeRDConverter/',
    'DocumentOptimization/PDFOptimize/',
    'Forms/ConvertXFAToAcroForms/',
    'Forms/ExportFormsData/',
    'Forms/FlattenForms/',
    'Forms/ImportFormsData/',
    'Images/DocToImages/',
    'Images/DrawSeparations/',
    'Images/DrawToBitmap/',
    'Images/EPSSeparations/',
    'Images/GetSeparatedImages/',
    'Images/ImageEmbedICCProfile/',
    'Images/ImageExport/',
    'Images/ImageExtraction/',
    'Images/ImageFromStream/',
    'Images/ImageImport/',
    'Images/ImageResampling/',
    'Images/ImageSoftMask/',
    'Images/OutputPreview/',
    'Images/RasterizePage/',
    'InformationExtraction/ListBookmarks/',
    'InformationExtraction/ListInfo/',
    'InformationExtraction/ListLayers/',
    'InformationExtraction/ListPaths/',
    'InformationExtraction/Metadata/',
    'OpticalCharacterRecognition/AddTextToDocument/',
    'OpticalCharacterRecognition/AddTextToImage/',
    'OpticalCharacterRecognition/OCRDocument/',
    'Other/MemoryFileSystem/',
    'Other/StreamIO/',
    'Printing/PrintPDF/',
    'Printing/PrintPDFGUI/',
    'Security/AddBasicPAdESElectronicSignature/',
    'Security/AddPAdESPolicySignature/',
    'Security/AddDigitalSignatureCMS/',
    'Security/AddDigitalSignatureRFC3161/',
    'Security/AddRegexRedaction/',
    'Security/Redactions/',
    'Text/AddGlyphs/',
    'Text/AddUnicodeText/',
    'Text/AddVerticalText/',
    'Text/ExtractAcroFormFieldData/',
    'Text/ExtractCJKTextByPatternMatch/',
    'Text/ExtractTextByPatternMatch/',
    'Text/ExtractTextByRegion/',
    'Text/ExtractTextFromAnnotations/',
    'Text/ExtractTextFromMultiRegions/',
    'Text/ExtractTextPreservingStyleAndPositionInfo/',
    'Text/ListWords/',
    'Text/RegexExtractText/',
    'Text/RegexTextSearch/',
    'Text/TextExtract/',
]

# Samples that cannot run unattended on a CI agent (GUI / printing / viewers).
# They are still BUILT; they are skipped only at run time.
SKIP_RUN = {
    'PrintPDF', 'PrintPDFGUI', 'DisplayPDF',
    'DotNETViewer', 'DotNETViewerComponent', 'PDFObjectExplorer',
}

# nuget-builder publishes the nightly .nupkgs here (LM .NETFramework,
# FormsExtension LM .NETFramework, SampleInput). Internal raid share; reachable
# only on the corporate network with SMB auth.
NIGHTLY_PKG_DIR = r'\\ivy\raid\nuget-builder-samples-test'
# Packages the .NET Framework samples need from the nightly drop: the LM
# .NETFramework library, the Forms Extension LM .NETFramework library, and their
# Adobe dependencies (SampleInput, Resources). The raid folder also holds the
# .NET (Core), OCR, and SharedLibs packages, which these samples don't use, so we
# skip them. (Newtonsoft.Json resolves from nuget.org.)
NIGHTLY_PACKAGE_IDS = (
    'Adobe.PDF.Library.LM.NETFramework',
    'Adobe.PDF.Library.FormsExtension.LM.NETFramework',
    'Adobe.PDF.Library.SampleInput',
    'Adobe.PDF.Library.Resources',
    'APDFL.OCR.Data.English',
    'APDFL.OCR.Data.LatinScript',
)
# Public read-only feed. Required alongside the nightly folder because passing
# -Source to nuget restore overrides the default feeds, and some samples pull
# Newtonsoft.Json. Restore is download-only; nothing is published here.
NUGET_ORG = 'https://api.nuget.org/v3/index.json'


def _sample_name(sample):
    """'Images/RasterizePage/' -> 'RasterizePage'"""
    return os.path.basename(os.path.dirname(sample))


def _copy_packages_locally(packages):
    for package in packages:
        shutil.copy(package, os.getcwd())


def _sample_input(filename):
    """Resolve a SampleInput resource (e.g. ducky.pdf) from the restored
    Adobe.PDF.Library.SampleInput package in the NuGet global cache.
    NUGET_PACKAGES relocates the cache (CI isolates it per job)."""
    cache = os.environ.get('NUGET_PACKAGES') or os.path.join(
        os.path.expanduser('~'), '.nuget', 'packages')
    cache = os.path.join(cache, 'adobe.pdf.library.sampleinput')
    matches = glob.glob(os.path.join(cache, '*', 'build', 'Resources',
                                     'Sample_Input', filename))
    return matches[0] if matches else filename


def get_nightly_packages():
    """Copy only the .NETFramework packages and their dependencies from the raid
    into the repo root (skips the unrelated .NET/OCR/SharedLibs nupkgs)."""
    wanted = [
        os.path.join(NIGHTLY_PKG_DIR, f)
        for f in os.listdir(NIGHTLY_PKG_DIR)
        if f.endswith('.nupkg') and any(f.startswith(pid + '.') for pid in NIGHTLY_PACKAGE_IDS)
    ]
    _copy_packages_locally(wanted)


@task
def clean_samples(ctx):
    """Reset every sample dir and remove any locally-copied nupkgs."""
    for nupkg in glob.glob(os.path.join(os.getcwd(), '*.nupkg')):
        os.remove(nupkg)
    for sample in samples_list:
        full_path = os.path.join(os.getcwd(), sample)
        with ctx.cd(full_path):
            ctx.run('git clean -fdx')
            ctx.run('git checkout .')


@task
def clean_nuget_cache(ctx):
    """Clear the local NuGet caches."""
    ctx.run('nuget locals all -clear')


@task
def build_samples(ctx, config='Debug'):
    """Build every sample with msbuild (x64). Debug restores the nightly
    packages from the raid; Release restores from nuget.org."""
    ctx.run('invoke clean-samples')

    if config == 'Debug':
        get_nightly_packages()

    packages_path = os.getcwd()
    sources = f'-Source "{NUGET_ORG}"'
    if config == 'Debug':
        sources += f' -Source "{packages_path}"'

    for sample in samples_list:
        full_path = os.path.join(os.getcwd(), sample)
        sample_name = _sample_name(sample)
        with ctx.cd(full_path):
            if sample_name == 'DotNETViewer':
                ctx.run(f'nuget restore ../DotNETViewerComponent/DotNETViewerComponent.csproj {sources}')
                ctx.run(f'msbuild ../DotNETViewerComponent/DotNETViewerComponent.csproj /p:Configuration={config} /p:Platform=x64')
            ctx.run(f'nuget restore {sample_name}.csproj {sources}')
            ctx.run(f'msbuild {sample_name}.csproj /p:Configuration={config} /p:Platform=x64')


@task
def run_samples(ctx, config='Debug'):
    """Run each built sample's .exe, skipping GUI/printing/viewer samples."""
    apdfl_key = os.environ.get('APDFL_KEY', '')
    for sample in samples_list:
        full_path = os.path.join(os.getcwd(), sample)
        sample_name = _sample_name(sample)
        if sample_name in SKIP_RUN:
            print(f'{sample_name} will not be run (interactive/GUI/printing).')
            continue
        with ctx.cd(full_path):
            cmd = os.path.join('bin', config, f'{sample_name}.exe')
            if sample_name == 'DocToImages':
                cmd += f' -format=png "{_sample_input("ducky.pdf")}"'
            # Key is supplied on stdin only, never in the echoed command.
            ctx.run(cmd, in_stream=io.StringIO(apdfl_key + '\n'))


tasks = []
tasks.extend([v for v in locals().values() if isinstance(v, Task)])

ns = Collection(*tasks)
ns.configure({'run': {'echo': 'true'}})
