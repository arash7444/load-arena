"""Project configuration, preflight, integration, and export regressions."""

from pathlib import Path
from importlib import import_module
from unittest.mock import Mock

import pandas as pd
import pytest
import yaml

from load_arena import LoadArenaProject
from load_arena.project.config import ProjectConfigError, check_simulation_file, load_cases
from load_arena.process.concatenate_stats import concatenate_stats
from load_arena.process.family_avg import calc_family_avg
from load_arena.process.uls import calc_uls


@pytest.fixture
def project_files(tmp_path):
    """Create portable configuration and placeholder input files.

    Parameters: tmp_path is pytest's temporary directory.
    Returns: YAML path and its mutable source document.
    Examples: Use project_files in a project test.
    """
    results = tmp_path / "simulations"
    results.mkdir()
    for name in ("a.int", "b.res", "sensor"):
        (results / name).touch()
    pd.DataFrame({
        "Folder": [".", "."], "Case_folder": ["dlc", "dlc"],
        "Timeseries": ["a", "b.res"], "Family": [1, 1], "PLF": [1.5, 1.5],
        "Averaging_method": ["mean", "mean"], "Occurrences": [2, 3],
    }).to_csv(tmp_path / "cases.csv", index=False)
    document = {
        "project": {"name": "Test campaign"},
        "data": {"software": "HAWC2", "results_path": "simulations"},
        "analysis": {
            "statistics": {"enabled": True},
            "uls": {"enabled": True, "cases": "cases.csv"},
            "fls": {"enabled": True, "cases": "cases.csv",
                    "wohler_exponents": [4, 6], "n_ref": 100, "method": "astm"},
        },
        "output": {"directory": "outputs"},
    }
    path = tmp_path / "project.yaml"
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    return path, document


def test_preflight_resolves_paths_without_reading_samples(project_files, monkeypatch, tmp_path):
    """Preflight enabled CSVs without constructing the sample reader.

    Parameters: project_files, monkeypatch, and tmp_path are pytest fixtures.
    Returns: None; assertions verify paths and absence of writes/reads.
    Examples: pytest tests/test_project.py -k preflight
    """
    path, _ = project_files
    reader = Mock(side_effect=AssertionError("Time-series reader must not run"))
    monkeypatch.setattr("load_arena.data_reader.Hawc2io.ReadHawc2", reader)
    monkeypatch.setattr(import_module("load_arena.process.concatenate_stats"), "ReadHawc2", reader)
    monkeypatch.setattr("load_arena.process.fls.ReadHawc2", reader)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    project = LoadArenaProject.from_yaml(path)
    assert project.source_path == path
    assert project.config.data.results_path == path.parent / "simulations"
    assert project.config.analysis.uls.cases == path.parent / "cases.csv"
    assert not project.config.output.directory.exists()
    cases = load_cases(project.config, "uls")
    assert cases.Timeseries.tolist() == ["a.int", "b.res"]
    assert cases.Folder.tolist() == [str(path.parent / "simulations")] * 2
    reader.assert_not_called()


@pytest.mark.parametrize("keys,value", [
    (("project", "name"), " "),
    (("data", "software"), "QBlade"),
    (("data", "results_path"), ""),
    (("data", "results_path"), "missing"),
    (("analysis", "statistics", "enabled"), "true"),
    (("analysis", "statistics", "enabled"), 1),
    (("analysis", "uls", "cases"), None),
    (("analysis", "fls", "wohler_exponents"), []),
    (("analysis", "fls", "wohler_exponents"), [0]),
    (("analysis", "fls", "wohler_exponents"), [float("inf")]),
    (("analysis", "fls", "wohler_exponents"), [True]),
    (("analysis", "fls", "wohler_exponents"), ["4"]),
    (("analysis", "fls", "n_ref"), -1),
    (("analysis", "fls", "n_ref"), float("nan")),
    (("analysis", "fls", "method"), "unknown"),
    (("analysis", "fls", "channels"), ["Load"]),
    (("analysis", "fls", "wohler_exponent"), 4),
])
def test_invalid_configuration(project_files, keys, value):
    """Reject invalid values with configuration context.

    Parameters: project_files supplies YAML; keys and value select a bad field.
    Returns: None; configuration errors retain their cause and filename.
    Examples: pytest tests/test_project.py -k invalid_configuration
    """
    path, document = project_files
    section = document
    for key in keys[:-1]:
        section = section[key]
    section[keys[-1]] = value
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    with pytest.raises(ProjectConfigError) as error:
        LoadArenaProject.from_yaml(path)
    assert str(path) in str(error.value)
    assert error.value.__cause__ is not None


@pytest.mark.parametrize("source", ["", "[]", "project: [", "project: a\nproject: b", "!!python/object:builtins.object {}"])
def test_bad_yaml(project_files, source):
    """Reject malformed, duplicate, nonmapping, and unsafe YAML.

    Parameters: project_files supplies a path; source is invalid YAML.
    Returns: None; safe loading raises ProjectConfigError.
    Examples: pytest tests/test_project.py -k bad_yaml
    """
    path, _ = project_files
    path.write_text(source, encoding="utf-8")
    with pytest.raises(ProjectConfigError):
        LoadArenaProject.from_yaml(path)


def test_omitted_and_disabled_analyses(project_files):
    """Default analyses to disabled and ignore disabled file availability.

    Parameters: project_files supplies the basic project configuration.
    Returns: None; all disabled calls fail before writing.
    Examples: pytest tests/test_project.py -k disabled
    """
    path, document = project_files
    document["analysis"] = {"uls": {"cases": "missing.csv"}}
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    project = LoadArenaProject.from_yaml(path)
    for method in (project.run_statistics, project.run_uls, project.run_fls):
        with pytest.raises(ProjectConfigError, match="enabled is false"):
            method()
    assert not project.config.output.directory.exists()


@pytest.mark.parametrize("missing", ["cases.csv", "simulations/a.int", "simulations/sensor"])
def test_missing_inputs_fail_during_loading(project_files, missing):
    """Catch missing CSV, samples, and companions during project loading.

    Parameters: project_files supplies inputs; missing selects the removed file.
    Returns: None; loading reports the enabled case file.
    Examples: pytest tests/test_project.py -k missing_inputs
    """
    path, _ = project_files
    (path.parent / missing).unlink()
    with pytest.raises(ProjectConfigError, match="analysis.uls.cases"):
        LoadArenaProject.from_yaml(path)


@pytest.mark.parametrize("column,value", [("PLF", 0), ("Occurrences", -1), ("Timeseries", ""), ("Averaging_method", "bad")])
def test_invalid_case_values(project_files, column, value):
    """Reject invalid case rows before simulation reads.

    Parameters: project_files supplies CSV; column and value define bad data.
    Returns: None; preflight raises with CSV context.
    Examples: pytest tests/test_project.py -k invalid_case_values
    """
    path, _ = project_files
    csv = path.parent / "cases.csv"
    table = pd.read_csv(csv)
    table.loc[0, column] = value
    table.to_csv(csv, index=False)
    with pytest.raises(ProjectConfigError, match="cases.csv"):
        LoadArenaProject.from_yaml(path)


def test_empty_and_single_mean_max_cases(project_files):
    """Reject empty tables and mean_max groups that select zero records.

    Parameters: project_files supplies an editable CSV.
    Returns: None; both invalid inputs fail preflight.
    Examples: pytest tests/test_project.py -k mean_max
    """
    path, _ = project_files
    csv = path.parent / "cases.csv"
    table = pd.read_csv(csv).iloc[:1].copy()
    table["Averaging_method"] = "mean_max"
    table.to_csv(csv, index=False)
    with pytest.raises(ProjectConfigError, match="at least two"):
        LoadArenaProject.from_yaml(path)
    table.iloc[:0].to_csv(csv, index=False)
    with pytest.raises(ProjectConfigError, match="at least one row"):
        LoadArenaProject.from_yaml(path)


def test_sel_companions_and_absolute_paths(project_files):
    """Resolve SEL/DAT pairs and preserve absolute CSV paths.

    Parameters: project_files supplies the temporary project.
    Returns: None; all reader-compatible SEL forms resolve consistently.
    Examples: pytest tests/test_project.py -k sel_companions
    """
    path, document = project_files
    folder = path.parent / "separate"
    folder.mkdir()
    (folder / "case.sel").touch()
    with pytest.raises(ProjectConfigError, match="case.dat"):
        check_simulation_file(folder / "case")
    (folder / "case.dat").touch()
    for name in ("case", "case.sel", "case.dat"):
        assert check_simulation_file(folder / name) == folder / "case.sel"
    csv = path.parent / "cases.csv"
    table = pd.read_csv(csv)
    table["Folder"] = str(folder)
    table["Timeseries"] = "case.dat"
    table.to_csv(csv, index=False)
    document["analysis"]["uls"]["cases"] = str(csv)
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    project = LoadArenaProject.from_yaml(path)
    assert load_cases(project.config, "uls").Folder.tolist() == [str(folder)] * 2


def test_statistics_and_uls_match_existing_pipeline(project_files, monkeypatch):
    """Compare project results and exports against the direct core pipeline.

    Parameters: project_files supplies inputs; monkeypatch supplies reader samples.
    Returns: None; statistics and ULS preserve calculations and attribution.
    Examples: pytest tests/test_project.py -k match_existing
    """
    path, _ = project_files
    reader = Mock()
    reader.ReadAll.return_value = [[0.0, -2.0], [1.0, 4.0], [2.0, 0.0]]
    reader.ChInfo = [["Time", "Load"], ["s", "kN"], ["", ""]]
    monkeypatch.setattr(import_module("load_arena.process.concatenate_stats"), "ReadHawc2", Mock(return_value=reader))
    project = LoadArenaProject.from_yaml(path)
    stats = project.run_statistics()
    assert [Path(name).name for name in stats.filename] == ["a.int", "b.res"]
    assert stats.mean["Load_[kN]"].iloc[0] == pytest.approx(2 / 3)
    cases = load_cases(project.config, "uls")
    direct_stats = concatenate_stats(cases)
    expected = calc_uls(calc_family_avg(direct_stats, cases), direct_stats)
    actual = project.run_uls()
    pd.testing.assert_frame_equal(expected.ULS, actual.ULS)
    pd.testing.assert_frame_equal(expected.Family_ULS, actual.Family_ULS)
    saved = pd.read_csv(project.config.output.directory / "statistics/mean.csv")
    assert saved.filename.tolist() == stats.filename
    assert actual.ULS["Load_[kN]"].iloc[0] == 6


def test_statistics_discovery_and_empty_directory(project_files, monkeypatch):
    """Discover FLEX and SEL files once, excluding DAT and HDF5.

    Parameters: project_files supplies files; monkeypatch intercepts calculations.
    Returns: None; discovered filenames are sorted and empty roots fail.
    Examples: pytest tests/test_project.py -k discovery
    """
    path, _ = project_files
    project = LoadArenaProject.from_yaml(path)
    root = project.config.data.results_path
    for name in ("z.sel", "z.dat", "ignored.hdf5"):
        (root / name).touch()
    calculation = Mock(side_effect=RuntimeError("captured"))
    monkeypatch.setattr("load_arena.project.project.concatenate_stats", calculation)
    with pytest.raises(RuntimeError, match="captured"):
        project.run_statistics()
    assert [p.name for p in calculation.call_args.args[0]] == ["a.int", "b.res", "z.sel"]
    project.config.data.results_path = root / "empty"
    project.config.data.results_path.mkdir()
    with pytest.raises(ProjectConfigError, match="No supported"):
        project.run_statistics()


def test_runs_recheck_cases_and_output_errors(project_files, monkeypatch):
    """Reread changed CSVs and propagate output failures with context.

    Parameters: project_files supplies inputs; monkeypatch replaces FLS calculation.
    Returns: None; fresh validation and contextual output errors are asserted.
    Examples: pytest tests/test_project.py -k recheck
    """
    from load_arena.process.fls import FLSResult

    path, _ = project_files
    project = LoadArenaProject.from_yaml(path)
    result = FLSResult(pd.DataFrame({"channel": ["Time"], "wohler_exponent": [4], "DEL": [1]}),
                       pd.DataFrame({"channel": ["Time"], "wohler_exponent": [4], "DEL": [2]}), 100, "astm")
    monkeypatch.setattr("load_arena.project.project.calc_fls", Mock(return_value=result))
    project.run_fls()
    directory = project.config.output.directory / "fls"
    (directory / "keep.txt").write_text("keep", encoding="utf-8")
    (directory / "campaign.csv").write_text("old", encoding="utf-8")
    assert project.run_fls() is result
    saved = pd.read_csv(directory / "campaign.csv")
    assert saved.loc[0, "wohler_exponent"] == 4
    assert saved.loc[0, "method"] == "astm"
    assert saved.loc[0, "n_ref"] == 100
    assert (directory / "keep.txt").read_text() == "keep"
    blocker = path.parent / "blocked"
    blocker.write_text("file", encoding="utf-8")
    project.config.output.directory = blocker
    with pytest.raises(OSError, match="Cannot write fls outputs"):
        project.run_fls()
    (path.parent / "simulations/a.int").unlink()
    with pytest.raises(ProjectConfigError, match="CSV row 2"):
        project.run_fls()


def test_real_fixture_uls(tmp_path):
    """Exercise the project ULS pipeline with portable checked-in FLEX data.

    Parameters: tmp_path supplies isolated configuration and output storage.
    Returns: None; real reader results match the direct pipeline.
    Examples: pytest tests/test_project.py -k real_fixture
    """
    root = Path(__file__).parent / "h2_res/dlc13"
    table = pd.DataFrame({"Folder": [str(root)], "Case_folder": ["dlc13"],
                          "Timeseries": ["dlc13_wsp04_wdir000_s023004"],
                          "Family": [1], "PLF": [1.5], "Averaging_method": ["mean"]})
    table.to_csv(tmp_path / "cases.csv", index=False)
    document = {"project": {"name": "Real fixture"},
                "data": {"software": "HAWC2", "results_path": str(root)},
                "analysis": {"uls": {"enabled": True, "cases": "cases.csv"}},
                "output": {"directory": "out"}}
    path = tmp_path / "project.yaml"
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    project = LoadArenaProject.from_yaml(path)
    cases = load_cases(project.config, "uls")
    stats = concatenate_stats(cases)
    direct = calc_uls(calc_family_avg(stats, cases), stats)
    pd.testing.assert_frame_equal(project.run_uls().ULS, direct.ULS)
