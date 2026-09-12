from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_windows_distribution_files_exist_and_are_project_local():
    required = [
        "Install-Windows.bat",
        "Run-Windows.bat",
        "environment-windows.yml",
        "scripts/install-local.ps1",
        "scripts/run-local.ps1",
    ]
    for relative_path in required:
        assert (ROOT / relative_path).is_file(), relative_path

    environment = (ROOT / "environment-windows.yml").read_text(encoding="utf-8")
    assert "rdkit=2025.09.6" in environment
    assert "streamlit=1.35.0" in environment
    assert "linux-64" not in environment
    assert ".molecular-knn-env" in (ROOT / "scripts/install-local.ps1").read_text(encoding="utf-8")


def test_launcher_contract_covers_ports_readiness_browser_and_cleanup():
    script = (ROOT / "scripts/run-local.ps1").read_text(encoding="utf-8")
    assert "TcpListener" in script
    assert "IPAddress]::Loopback" in script
    assert "MaxRetries" in script
    assert "_stcore/health" in script
    assert "Start-Process $LocalUrl" in script
    assert "NoBrowser" in script
    assert "finally" in script
    assert "127.0.0.1" in script
    assert "Stop-Process -Name" not in script


def test_clean_extract_is_supported_without_python_or_existing_environment():
    install = (ROOT / "scripts/install-local.ps1").read_text(encoding="utf-8")
    run = (ROOT / "scripts/run-local.ps1").read_text(encoding="utf-8")
    assert "micromamba.exe" in install
    assert "Invoke-WebRequest" in install
    assert "create --yes --prefix" in install
    assert "python.exe" in run
    assert "Install-Windows.bat first" in run
