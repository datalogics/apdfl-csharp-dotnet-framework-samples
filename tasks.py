from invoke import Collection, Exit, task
from invoke.tasks import Task
import glob
import os
import shutil
import subprocess

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

# The package sources build-samples can test against:
#   Nightly - the .nupkgs above, copied off the raid share into a local feed.
#   Public  - resolved from nuget.org. Nothing is copied locally, so this is the
#             pass that fails when a release is approved but not actually
#             usable: a wrong or partial upload, an unlisted version, or a
#             dependency package that never made it up. The samples reference
#             the license-managed ids either way, so nothing has to be
#             rewritten -- only where the packages come from changes.
PACKAGE_SOURCES = ('Nightly', 'Public')

# Emptied before it is populated, rather than the repo root the nupkgs used to
# be copied into: the nightly and public packages share version numbers, so a
# leftover .nupkg from an earlier run could outrank the one under test.
NIGHTLY_FEED_DIR = 'packages_nightly'


def _sample_name(sample):
    """'Images/RasterizePage/' -> 'RasterizePage'"""
    return os.path.basename(os.path.dirname(sample))


def _make_package_dir(name):
    """Returns an absolute, empty local feed directory named `name`."""
    package_dir = os.path.join(os.getcwd(), name)
    shutil.rmtree(package_dir, ignore_errors=True)
    os.makedirs(package_dir)
    return package_dir


def _copy_packages_locally(packages, package_dir):
    for package in packages:
        shutil.copy(package, package_dir)


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


def get_nightly_packages(package_dir):
    """Copy only the .NETFramework packages and their dependencies from the raid
    into the local feed (skips the unrelated .NET/SharedLibs nupkgs)."""
    wanted = [
        os.path.join(NIGHTLY_PKG_DIR, f)
        for f in os.listdir(NIGHTLY_PKG_DIR)
        if f.endswith('.nupkg') and any(f.startswith(pid + '.') for pid in NIGHTLY_PACKAGE_IDS)
    ]
    # Checked here rather than left to the restore: an unreachable or empty
    # share otherwise shows up as NU1101 on every sample, naming a package id
    # instead of the share that failed to provide it.
    if not wanted:
        raise Exit(f'no matching .nupkg files found in {NIGHTLY_PKG_DIR} -- '
                   f'is the raid share reachable from this node?')

    library = NIGHTLY_PACKAGE_IDS[0]
    if not any(os.path.basename(p).startswith(library + '.') for p in wanted):
        raise Exit(f'{library} is not in the nightly drop at {NIGHTLY_PKG_DIR}. '
                   f'The share had packages but not that one -- check what '
                   f'nuget-builder last published to it.')

    _copy_packages_locally(wanted, package_dir)
    print(f'... copied {len(wanted)} packages into {package_dir}')


@task
def clean_samples(ctx):
    """Reset every sample dir and remove any locally-copied nupkgs."""
    shutil.rmtree(os.path.join(os.getcwd(), NIGHTLY_FEED_DIR), ignore_errors=True)
    # Kept for the nupkgs older runs left loose in the repo root, before they
    # were copied into NIGHTLY_FEED_DIR instead.
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
def clean_nuget_packages(ctx):
    """Clear extracted packages, keeping the http cache.

    Restore reuses an already-extracted package without consulting any source,
    so the nightly and public passes have to run against an empty
    global-packages folder to be sure of which bits they built against. This
    matters most for the packages the two passes share by id and version --
    SampleInput, Resources, the OCR data -- where a copy cached from the
    nightly feed would hide a version that was never published. The http cache
    is left alone so the nuget.org packages do not download twice.
    """
    ctx.run('nuget locals global-packages -clear')


# pkg_source is defaulted rather than required so a bare `invoke build-samples`
# keeps working the way it always has, on the nightly packages. Invoke never
# treats an argument that has a default as positional, so the value has to come
# in as a flag: `invoke build-samples --pkg-source Public`. config stays the
# msbuild configuration, which both passes build the same way -- run-samples
# looks for the .exe under bin/<config>.
@task(help={'pkg_source': f'Packages to build against: {" or ".join(PACKAGE_SOURCES)}',
            'config': 'msbuild configuration to build'})
def build_samples(ctx, pkg_source='Nightly', config='Debug'):
    """Build every sample with msbuild (x64) against the Nightly or Public
    packages."""
    # Checked before anything else: an unrecognized value used to fall through
    # every branch and build against whatever packages were left in the tree,
    # which passes without testing anything.
    if pkg_source not in PACKAGE_SOURCES:
        raise Exit(f'unknown package source {pkg_source!r}, '
                   f'expected one of {list(PACKAGE_SOURCES)}')

    ctx.run('invoke clean-samples')

    # nuget.org is in both passes: -Source overrides the default feeds, and the
    # samples also pull Newtonsoft.Json from it. Passing it explicitly means the
    # public pass cannot fall back to a local or raid feed left in NuGet.config.
    sources = f'-Source "{NUGET_ORG}"'
    if pkg_source == 'Nightly':
        nightly_feed = _make_package_dir(NIGHTLY_FEED_DIR)
        get_nightly_packages(nightly_feed)
        sources += f' -Source "{nightly_feed}"'

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
    """Run each built sample's .exe, skipping GUI/printing/viewer samples.

    The packages are the license-managed ones, so a sample prompts on stdin for
    an evaluation key before it will do any work. In CI stdin is not a terminal,
    the prompt reads EOF and the sample fails, so the key comes in from the
    APDFL_KEY environment variable that the Jenkinsfile fills from the
    apdfl-rlm-key credential.

    See _run_sample for why this does not go through ctx.run.
    """
    apdfl_key = os.environ.get('APDFL_KEY', '')
    for sample in samples_list:
        full_path = os.path.join(os.getcwd(), sample)
        sample_name = _sample_name(sample)
        if sample_name in SKIP_RUN:
            print(f'{sample_name} will not be run (interactive/GUI/printing).')
            continue
        # Absolute: CreateProcess resolves a relative program path against the
        # calling process's directory, not the cwd handed to the child.
        command = [os.path.join(full_path, 'bin', config, f'{sample_name}.exe')]
        if sample_name == 'DocToImages':
            command += ['-format=png', _sample_input('ducky.pdf')]
        _run_sample(full_path, sample_name, command, apdfl_key)


def _run_sample(full_path, sample_name, command, apdfl_key):
    """Run one built sample, handing it the activation key on stdin.

    Deliberately not ctx.run. invoke pumps a non-tty in_stream one byte per 10ms
    poll (see bytes_to_read in invoke/terminals.py), and it is hard to reason
    about when the key actually lands. subprocess writes it in one go and closes
    stdin behind it, so the second fgets() in the library's retry loop sees EOF
    instead of blocking on an idle pipe until the pipeline's four-hour timeout.

    stdout and stderr stay inherited so sample output keeps streaming into the
    build log. Passing the arguments as a list also keeps a space in the
    SampleInput cache path from being re-split by a shell.
    """
    print(f'{sample_name}: {" ".join(command)}', flush=True)
    # Key is supplied on stdin only, never in the echoed command.
    result = subprocess.run(command, cwd=full_path, shell=False,
                            input=(apdfl_key + '\n').encode())
    if result.returncode != 0:
        raise Exit(f'{sample_name} exited {result.returncode}',
                   code=result.returncode)


tasks = []
tasks.extend([v for v in locals().values() if isinstance(v, Task)])

ns = Collection(*tasks)
ns.configure({'run': {'echo': 'true'}})
