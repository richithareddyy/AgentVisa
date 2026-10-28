"""Install one wheel in a fresh environment and exercise bundled offline commands."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import venv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('wheel', type=Path)
    args = parser.parse_args()
    wheel = args.wheel.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix='agentvisa-package-') as directory:
        root = Path(directory)
        environment = root / 'environment'
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / 'bin' / 'python'
        # Offline commands use the standard library; no source checkout or dependency
        # installation is needed to prove that the wheel contains its own dataset.
        subprocess.run([str(python), '-I', '-m', 'pip', 'install', '--no-index', '--no-deps', str(wheel)],
                       cwd=root, check=True, capture_output=True, text=True)
        origin = subprocess.run([str(python), '-I', '-c', 'import agentvisa; print(agentvisa.__file__)'],
                                cwd=root, check=True, capture_output=True, text=True).stdout.strip()
        if not Path(origin).resolve().is_relative_to(environment.resolve()):
            raise RuntimeError('package resolved outside the clean environment')
        def command(name):
            result = subprocess.run([str(python), '-I', '-m', 'agentvisa', name], cwd=root,
                                    check=True, capture_output=True, text=True)
            return json.loads(result.stdout)
        evaluation = command('evaluate')
        demo = command('demo')
        if evaluation['case_count'] != 42 or evaluation['exact_decision_accuracy'] != 1:
            raise RuntimeError('installed evaluation failed')
        if [row['decision'] for row in demo] != ['ALLOW', 'DENY', 'ASK_HUMAN', 'ALLOW', 'DENY', 'DENY', 'DENY']:
            raise RuntimeError('installed demo failed')
        print('Wheel installed outside checkout: 42 evaluation cases and all demo scenarios passed.')


if __name__ == '__main__':
    main()
