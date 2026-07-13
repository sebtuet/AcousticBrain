import json
import wave
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from acousticbrain.application import AcousticSession, ExperimentDiscoveryService
from acousticbrain.importers import ExperimentImporter
from acousticbrain.models import ExperimentState, ExperimentType, ImpulseChannel
from acousticbrain.persistence import MeasurementRepository


def rew_measurement(name, dated="Jul 13, 2026 10:00:00 AM"):
    return (
        "* Measurement data measured by REW\n"
        f"* Dated: {dated}\n"
        f"* Measurement: {name}\n"
        "* Freq(Hz) SPL(dB) Phase(degrees)\n"
        "20.0 70.0 0.0\n"
        "100.0 71.0 1.0\n"
    )


def complete_experiment(directory, *, filenames=("one", "two", "three")):
    measurement_directory = directory / "measurements"
    measurement_directory.mkdir(parents=True)
    for filename, channel in zip(filenames, ("LEFT", "RIGHT", "STEREO")):
        (measurement_directory / f"{filename}.txt").write_text(
            rew_measurement(channel),
            encoding="utf-8",
        )


def test_repository_detects_channels_from_content_not_filenames(tmp_path):
    directory = tmp_path / "baseline"
    complete_experiment(
        directory,
        filenames=("totally-free-a", "anything-b", "untitled-c"),
    )

    inspected = MeasurementRepository().inspect_directory(directory)

    assert {item.channel for item in inspected} == {
        ImpulseChannel.LEFT,
        ImpulseChannel.RIGHT,
        ImpulseChannel.STEREO,
    }


def test_discovery_creates_manifests_hashes_and_chronological_descriptors(tmp_path):
    baseline = tmp_path / "baseline"
    experiment = tmp_path / "exp-001-verify-asymmetry"
    complete_experiment(baseline)
    complete_experiment(
        experiment,
        filenames=("alpha", "beta", "gamma"),
    )
    (experiment / "rew").mkdir()
    (experiment / "rew" / "opaque.mdat").write_bytes(b"not parsed")
    clock = lambda: datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc)
    service = ExperimentDiscoveryService(clock=clock)

    descriptors = service.discover(tmp_path)

    assert [item.experiment_type for item in descriptors] == [
        ExperimentType.BASELINE,
        ExperimentType.EXPERIMENT,
    ]
    assert all(item.state is ExperimentState.READY for item in descriptors)
    assert descriptors[1].mdat_file == "rew/opaque.mdat"
    assert descriptors[1].content_hash
    manifest = json.loads((experiment / "manifest.json").read_text())
    assert manifest["imported_at"] == "2026-07-13T12:00:00+00:00"
    assert manifest["state"] == "READY"
    assert set(manifest["channel_assignments"].values()) == {
        "LEFT",
        "RIGHT",
        "STEREO",
    }


def test_discovery_preserves_explicit_comparison_metadata(tmp_path):
    baseline = tmp_path / "baseline"
    experiment = tmp_path / "exp-001-arbitrary-name"
    complete_experiment(baseline)
    complete_experiment(experiment)
    (experiment / "manifest.json").write_text(json.dumps({
        "comparison": {
            "parent_experiment_id": "baseline",
            "source_protocol_id": "protocol.repeat-pair",
            "source_hypothesis_code": "ASYMMETRIC_SPEAKER_ROOM_INTERACTION",
            "declared_change_codes": ["LEFT_RIGHT_REMEASUREMENT"],
            "required_fact_codes": ["spatial.left_right.level_difference_abs_db"],
        }
    }), encoding="utf-8")

    descriptor = ExperimentDiscoveryService().discover(tmp_path)[1]

    assert descriptor.parent_experiment_ids == ("baseline",)
    assert descriptor.source_protocol_id == "protocol.repeat-pair"
    assert descriptor.declared_change_codes == ("LEFT_RIGHT_REMEASUREMENT",)
    assert descriptor.required_comparison_fact_codes == (
        "spatial.left_right.level_difference_abs_db",
    )


def test_discovery_preserves_explicit_causal_protocol_step(tmp_path):
    directory = tmp_path / "exp-002"
    complete_experiment(directory)
    (directory / "manifest.json").write_text(json.dumps({
        "causal_protocol_step": {
            "protocol_code": "VERIFY_SPEAKER_ROOM_ASYMMETRY",
            "step_code": "STEP_2_SPEAKER_SWAP",
            "step_index": 2,
            "controlled_variable_codes": [
                "ROOM_SIDE", "SIGNAL_CHAIN_ASSIGNMENT", "MICROPHONE_POSITION"
            ],
            "changed_variable_codes": ["LOUDSPEAKER_ASSIGNMENT"],
            "unknown_variable_codes": [],
            "observation_codes": [
                "ANOMALY_MOVED_WITH_SWAPPED_LOUDSPEAKER"
            ],
        }
    }), encoding="utf-8")

    descriptor = ExperimentDiscoveryService().discover(tmp_path)[0]
    causal_step = descriptor.causal_protocol_step

    assert causal_step.protocol_code == "VERIFY_SPEAKER_ROOM_ASYMMETRY"
    assert causal_step.step_index == 2
    assert causal_step.changed_variable_codes == ("LOUDSPEAKER_ASSIGNMENT",)
    persisted = json.loads((directory / "manifest.json").read_text())
    assert persisted["causal_protocol_step"]["observation_codes"] == [
        "ANOMALY_MOVED_WITH_SWAPPED_LOUDSPEAKER"
    ]


def test_identical_manifest_is_not_rewritten(tmp_path):
    directory = tmp_path / "baseline"
    complete_experiment(directory)
    service = ExperimentDiscoveryService(
        clock=lambda: datetime(2026, 7, 13, tzinfo=timezone.utc)
    )
    service.discover(tmp_path)
    manifest = directory / "manifest.json"
    first_timestamp = manifest.stat().st_mtime_ns

    service.discover(tmp_path)

    assert manifest.stat().st_mtime_ns == first_timestamp


def test_aggregate_hash_does_not_depend_on_filenames(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    complete_experiment(first, filenames=("a", "b", "c"))
    complete_experiment(second, filenames=("x", "y", "z"))
    repository = MeasurementRepository()

    first_hash = repository.aggregate_hash(repository.inspect_directory(first))
    second_hash = repository.aggregate_hash(repository.inspect_directory(second))

    assert first_hash == second_hash


def test_missing_measurement_channels_make_experiment_incomplete(tmp_path):
    directory = tmp_path / "exp-001"
    directory.mkdir()
    (directory / "arbitrary.txt").write_text(
        rew_measurement("LEFT"),
        encoding="utf-8",
    )

    descriptor = ExperimentDiscoveryService().discover(tmp_path)[0]

    assert descriptor.state is ExperimentState.INCOMPLETE
    assert descriptor.available_channels == (ImpulseChannel.LEFT,)


def test_manifest_can_assign_a_channel_to_metadata_free_wav(tmp_path):
    directory = tmp_path / "baseline"
    complete_experiment(directory)
    impulse_directory = directory / "impulse"
    impulse_directory.mkdir()
    wav_path = impulse_directory / "arbitrary-audio.wav"
    with wave.open(str(wav_path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(48000)
        stream.writeframes(b"\x00\x00\xff\x7f")
    (directory / "manifest.json").write_text(
        json.dumps(
            {
                "channel_assignments": {
                    "impulse/arbitrary-audio.wav": "LEFT"
                }
            }
        ),
        encoding="utf-8",
    )

    descriptor = ExperimentDiscoveryService().discover(tmp_path)[0]
    project = ExperimentImporter().load(descriptor)

    impulse = project.get_impulse_response(ImpulseChannel.LEFT)
    assert impulse is not None
    assert impulse.sample_rate_hz == 48000.0
    assert impulse.samples == [0.0, 1.0]


def test_wav_is_associated_by_content_signature_not_filename(tmp_path):
    directory = tmp_path / "baseline"
    directory.mkdir()
    sample_rate = 8000
    samples = np.zeros(1024, dtype=np.int16)
    samples[100] = 20000
    samples[130] = -9000
    wav_path = directory / "opaque-audio.wav"
    with wave.open(str(wav_path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(sample_rate)
        stream.writeframes(samples.astype("<i2").tobytes())
    frequencies = np.fft.rfftfreq(len(samples), 1.0 / sample_rate)
    magnitude = 20.0 * np.log10(
        np.maximum(np.abs(np.fft.rfft(samples.astype(float))), 1e-12)
    )
    selected = np.linspace(20, 3500, 80)
    spl = np.interp(selected, frequencies, magnitude)
    response = (
        "* Measurement: LEFT\n"
        "* Freq(Hz) SPL(dB) Phase(degrees)\n"
        + "".join(
            f"{frequency} {level} 0\n"
            for frequency, level in zip(selected, spl)
        )
    )
    (directory / "opaque-table.txt").write_text(response, encoding="utf-8")
    repository = MeasurementRepository()

    associated = repository.associate_wav_channels(
        repository.inspect_directory(directory)
    )

    wav = next(
        item for item in associated if item.path.suffix.lower() == ".wav"
    )
    assert wav.channel is ImpulseChannel.LEFT


def test_ambiguous_wav_signature_does_not_invent_a_channel(tmp_path):
    directory = tmp_path / "baseline"
    directory.mkdir()
    samples = np.zeros(512, dtype=np.int16)
    samples[50] = 20000
    wav_path = directory / "opaque.wav"
    with wave.open(str(wav_path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(8000)
        stream.writeframes(samples.astype("<i2").tobytes())
    response = (
        "* Freq(Hz) SPL(dB) Phase(degrees)\n"
        "20 70 0\n100 70 0\n1000 70 0\n"
    )
    (directory / "first.txt").write_text(
        "* Measurement: LEFT\n" + response,
        encoding="utf-8",
    )
    (directory / "second.txt").write_text(
        "* Measurement: RIGHT\n" + response,
        encoding="utf-8",
    )
    repository = MeasurementRepository()

    associated = repository.associate_wav_channels(
        repository.inspect_directory(directory)
    )

    wav = next(
        item for item in associated if item.path.suffix.lower() == ".wav"
    )
    assert wav.channel is None


def test_acoustic_session_auto_open_attaches_without_business_iterations(tmp_path):
    baseline = tmp_path / "baseline"
    experiment = tmp_path / "exp-001"
    complete_experiment(baseline)
    complete_experiment(experiment)

    session = AcousticSession.auto_open(tmp_path)

    assert session.baseline.descriptor.experiment_id == "baseline"
    assert session.current_project.name == "exp-001"
    assert [item.descriptor.experiment_id for item in session.experiments] == [
        "baseline",
        "exp-001",
    ]
    assert not hasattr(session, "iterations")
