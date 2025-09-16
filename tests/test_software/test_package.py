import shutil
import subprocess
import tempfile
from pathlib import Path


def test_package() -> None:
    """
    build package from source code, installs the package within a docker
    container and runs system tests using the built package
    """
    # build package
    dist_dir = Path("dist").resolve()
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    eggs_dir = Path("saveables.egg-info").resolve()
    if eggs_dir.exists():
        shutil.rmtree(eggs_dir)
    subprocess.run(["python", "-m", "build"], check=True)

    # get paths for docker mounting
    wheels = list(dist_dir.glob("*.whl"))
    assert wheels, "No .whl file found after build"
    wheel_path = wheels[0].resolve()
    mnt_wheel = "/mnt/wheel"
    tests_path = Path("tests").resolve()
    mnt_tests = "/mnt/tests"

    with tempfile.TemporaryDirectory() as tmpdir:
        # create docker file
        tmp_path = Path(tmpdir)
        dockerfile = tmp_path / "Dockerfile"

        dockerfile.write_text(
            """
            FROM python:3.11-slim

            WORKDIR /app

            RUN python -m venv venv && \\
                . venv/bin/activate && \\
                pip install --upgrade pip && \\
                pip install pytest

            COPY entrypoint.sh /app/entrypoint.sh
            RUN chmod +x /app/entrypoint.sh

            ENTRYPOINT ["/app/entrypoint.sh"]
            """
        )
        # create entry point script that activates venv, installs wheel
        # and runs the tests
        entrypoint = tmp_path / "entrypoint.sh"
        entrypoint.write_text(
            f"""#!/bin/sh
                                  . venv/bin/activate
                                  pip install {mnt_wheel}/{wheel_path.name}
                                  cd {mnt_tests}
                                  pytest test_system
                                  """
        )

        entrypoint.chmod(0o755)

        # build image
        image_tag = "saveables_test_env_mount"
        subprocess.run(
            ["docker", "build", "-t", image_tag, "."], cwd=tmp_path, check=True
        )

        # run the container
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{wheel_path.parent}:{mnt_wheel}:ro",
                "-v",
                f"{tests_path}:{mnt_tests}",
                "-e",
                f"PYTHONPATH={mnt_tests}",
                image_tag,
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, "Tests failed inside Docker container"
