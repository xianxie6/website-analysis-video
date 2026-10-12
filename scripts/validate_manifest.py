#!/usr/bin/env python3
"""Check local evidence, edit windows, captions, and optional ffprobe metadata."""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys


def validate(data, base, probe=False):
    errors, warnings = [], []
    def number(value, where, positive=False):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 or (positive and value == 0):
            errors.append(f'{where}: expected finite {"positive" if positive else "nonnegative"} number')
            return None
        return float(value)
    def local(value, where):
        if not isinstance(value, str) or not value or '://' in value:
            errors.append(f'{where}: expected local file path')
            return None
        path = (base / value).resolve()
        if not path.is_file():
            errors.append(f'{where}: missing {value}')
            return None
        return path
    def info(path):
        if not probe or path is None:
            return None
        try:
            return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)], text=True, stderr=subprocess.PIPE))
        except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as e:
            errors.append(f'ffprobe {path.name}: {e}')
            return None
    duration = number(data.get('duration'), 'duration', True)
    fps = number(data.get('fps'), 'fps', True)
    evidence = {}
    for item in data.get('evidence', []):
        ident = item.get('id')
        if not ident or ident in evidence:
            errors.append('evidence: missing or duplicate id')
            continue
        evidence[ident] = item
        if item.get('kind') not in ('observed', 'public_file', 'inference', 'unknown'):
            errors.append(f'{ident}: invalid evidence kind')
        if not item.get('source'):
            errors.append(f'{ident}: missing source or explanation of uncertainty')
    end_previous = 0
    seen = set()
    scenes = data.get('scenes', [])
    if not scenes:
        errors.append('scenes: at least one required')
    for scene in scenes:
        sid = scene.get('id')
        if not sid or sid in seen:
            errors.append('scenes: missing or duplicate id')
        seen.add(sid)
        start = number(scene.get('start'), f'{sid}.start')
        end = number(scene.get('end'), f'{sid}.end', True)
        if start is None or end is None:
            continue
        if end <= start or start < end_previous - .001 or (duration is not None and end > duration + .001):
            errors.append(f'{sid}: invalid, overlapping, or out-of-project window')
        end_previous = max(end_previous, end)
        length = end - start
        for claim in scene.get('claims', []):
            refs = claim.get('evidence_ids', [])
            if not claim.get('text') or not refs or any(ref not in evidence for ref in refs):
                errors.append(f'{sid}: claim missing text or valid evidence reference')
        for media in scene.get('media', []):
            path = local(media.get('path'), f'{sid}.media')
            metadata = info(path)
            coverage = media.get('coverage')
            if coverage not in ('complete', 'partial', 'before_after', 'not_recorded', 'illustration'):
                errors.append(f'{sid}: invalid coverage')
            if coverage in ('partial', 'before_after', 'not_recorded') and not media.get('limitation'):
                errors.append(f'{sid}: incomplete capture needs limitation')
            capture_fps = media.get('capture_fps')
            if capture_fps is not None:
                cap = number(capture_fps, f'{sid}.capture_fps', True)
                if cap is not None and fps is not None and cap < fps:
                    warnings.append(f'{sid}: capture {cap:g} fps < output {fps:g} fps; disclose sampling quality')
            if metadata and not metadata.get('streams'):
                errors.append(f'{sid}: media has no streams')
        voice = scene.get('voice')
        if voice:
            path = local(voice.get('path'), f'{sid}.voice')
            # duration describes this file BEFORE optional playback-rate adjustment.
            vd = number(voice.get('duration'), f'{sid}.voice.duration', True)
            offset = number(voice.get('offset', 0), f'{sid}.voice.offset')
            rate = number(voice.get('rate', 1), f'{sid}.voice.rate', True)
            metadata = info(path)
            if metadata:
                actual = float(metadata['format']['duration'])
                if vd is not None and abs(actual - vd) > .12:
                    errors.append(f'{sid}: voice duration differs from actual file ({actual:.3f}s)')
                vd = actual
            if None not in (vd, offset, rate) and offset + vd / rate > length + .04:
                errors.append(f'{sid}: voice overruns scene')
        last_cue_end = 0
        for cue in scene.get('captions', []):
            cs = number(cue.get('start'), f'{sid}.caption.start')
            ce = number(cue.get('end'), f'{sid}.caption.end', True)
            if cs is None or ce is None:
                continue
            if not cue.get('text') or ce <= cs or cs < last_cue_end - .001 or ce > length + .001:
                errors.append(f'{sid}: invalid, overlapping, or out-of-scene caption')
            last_cue_end = max(last_cue_end, ce)
    if data.get('final_video'):
        metadata = info(local(data['final_video'], 'final_video'))
        if metadata:
            actual = float(metadata['format']['duration'])
            if duration is not None and abs(actual - duration) > .12:
                errors.append(f'final_video: duration mismatch ({actual:.3f}s)')
            vs = next((x for x in metadata['streams'] if x['codec_type'] == 'video'), None)
            if vs is None:
                errors.append('final_video: no video stream')
            else:
                for key in ('width', 'height'):
                    if data.get(key) is not None and vs.get(key) != data[key]:
                        errors.append(f'final_video: {key} mismatch')
                a, b = map(float, vs.get('avg_frame_rate', '0/1').split('/'))
                if fps and (not b or abs(a / b - fps) > .01):
                    errors.append('final_video: fps mismatch')
            if data.get('require_audio', False) and not any(x['codec_type'] == 'audio' for x in metadata['streams']):
                errors.append('final_video: no required audio stream')
    return {'ok': not errors, 'errors': errors, 'warnings': warnings}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('manifest', type=Path)
    ap.add_argument('--probe', action='store_true', help='Use ffprobe for actual media duration and final format')
    args = ap.parse_args()
    try:
        result = validate(json.loads(args.manifest.read_text()), args.manifest.resolve().parent, args.probe)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
        result = {'ok': False, 'errors': [f'malformed manifest: {e}'], 'warnings': []}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
