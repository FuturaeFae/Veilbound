from pathlib import Path
import subprocess, sys, traceback


def main():
    root = Path(sys.argv[1]).resolve()
    ci = Path(__file__).resolve().parent
    finalizer = ci / 'full-refinement-finalize.py'
    generator = ci / 'generate-full-refinement-assets.py'

    if not finalizer.is_file() or not generator.is_file():
        raise SystemExit('missing 0.1.68 refinement reconstruction source')

    # Keep the authoritative source/GUI patch and all of its audits, but replace the interrupted
    # binary-archive staging section with deterministic asset generation. This makes reconstruction
    # independent of the partially uploaded 17-part texture payload.
    source = finalizer.read_text(encoding='utf-8')
    start = source.find("parts=[ci/f'full-refinement-assets.tar.gz.b64.part")
    end_marker = '# Superseded one-face resources are intentionally gone.'
    end = source.find(end_marker)
    if start < 0 or end < 0 or end <= start:
        raise SystemExit('could not locate replaceable refinement asset payload block')
    replacement = f"""generator = Path({str(generator)!r})\nsubprocess.run([sys.executable, str(generator), str(root)], check=True)\n\n"""
    rewritten = source[:start] + replacement + source[end:]
    namespace = {
        '__file__': str(finalizer),
        '__name__': '__main__',
    }
    exec(compile(rewritten, str(finalizer), 'exec'), namespace, namespace)

    # 0.1.68 is the refinement checkpoint; the source patch intentionally remains applicable to the
    # exact validated 0.1.67 reconstruction and the version bump occurs only after all refinement audits.
    props = root / 'gradle.properties'
    text = props.read_text(encoding='utf-8')
    if 'mod_version=0.1.67-dev' in text:
        text = text.replace('mod_version=0.1.67-dev', 'mod_version=0.1.68-dev', 1)
    elif 'mod_version=0.1.68-dev' not in text:
        raise SystemExit('unexpected Veilbound version while finalizing 0.1.68')
    props.write_text(text, encoding='utf-8')

    print('VEILBOUND_0168_RECONSTRUCTION=PASS interrupted_binary_payload=eliminated deterministic_assets=PASS version=0.1.68-dev')


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        # Workflow diagnostics tee stdout. Mirror every failure here so the artifact is actionable.
        traceback.print_exc(file=sys.stdout)
        raise
