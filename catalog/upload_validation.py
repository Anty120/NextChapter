"""Bounded structural validation, never trust a browser's MIME or filename."""
import hashlib
import io
import math
from pathlib import PurePosixPath

from django.core.exceptions import ValidationError
from mutagen.mp3 import MP3
from pypdf import PdfReader, apply_configuration
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, NameObject

from .upload_limits import MAX_PDF_BYTES, MAX_SONG_BYTES, MAX_USER_BYTES, MAX_USER_FILES

MAX_FILE_BYTES = MAX_PDF_BYTES  # Compatibility for the bounded direct/PDF path.


def inspect_file(upload):
    name = str(upload.name).replace('\\', '/')
    extension = PurePosixPath(name).suffix.lower()
    if extension not in {'.pdf', '.mp3'}:
        raise ValidationError('Choose a PDF book (.pdf) or MP3 song (.mp3).')
    limit = MAX_SONG_BYTES if extension == '.mp3' else MAX_PDF_BYTES
    if not upload.size or upload.size > limit:
        raise ValidationError('MP3 songs must be 10 MB or less; PDF books must be 3 MiB or less. Choose a nonempty file.')
    raw = upload.read(limit + 1)
    if not raw or len(raw) > limit or len(raw) != upload.size:
        raise ValidationError('The file is empty, too large, or incomplete. Choose it again.')
    if extension == '.pdf':
        details = inspect_pdf(raw)
    else:
        details = inspect_mp3(raw)
    return {**details, 'content': raw, 'byte_size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def inspect_pdf(raw):
    if not raw.startswith(b'%PDF-') or b'%%EOF' not in raw[-1024:]:
        raise ValidationError('This file is not a complete PDF. Export an unencrypted PDF and try again.')
    try:
        with apply_configuration(
                maximum_declared_stream_length=8*1024*1024,
                zlib_maximum_output_length=8*1024*1024,
                stream_decoding_work_maximum_length=16*1024*1024,
                page_tree_maximum_entries=1000, page_tree_maximum_depth=30,
                page_tree_maximum_page_entries=50000,
                array_maximum_element_count=20000, dictionary_maximum_element_count=20000):
            reader = PdfReader(io.BytesIO(raw), strict=True)
            if reader.is_encrypted:
                raise ValidationError('Password-protected PDFs are not supported. Upload an unencrypted copy.')
            pages = len(reader.pages)
            if not 1 <= pages <= 1000:
                raise ValidationError('Choose a PDF with 1–1000 pages.')
            # Reject active documents and attachments, including escaped PDF names.
            # Content streams are not executed, rendered or sent to another service.
            blocked = {'/JavaScript','/JS','/OpenAction','/AA','/Launch','/EmbeddedFiles',
                       '/EmbeddedFile','/RichMedia','/XFA','/SubmitForm','/ImportData','/GoToR'}
            pending, visited, count = [reader.trailer], set(), 0
            while pending:
                node = pending.pop(); count += 1
                if count > 50000:
                    raise ValidationError('This PDF is too complex. Try a simpler PDF export.')
                if isinstance(node, IndirectObject):
                    key = (node.idnum, node.generation)
                    if key in visited:
                        continue
                    visited.add(key); pending.append(node.get_object())
                elif isinstance(node, DictionaryObject):
                    if blocked.intersection(str(k) for k in node):
                        raise ValidationError('Interactive PDFs and embedded files are not supported. Export a plain PDF.')
                    pending.extend(node.values())
                elif isinstance(node, ArrayObject):
                    pending.extend(node)
                elif isinstance(node, NameObject) and str(node) in blocked:
                    raise ValidationError('Interactive PDFs are not supported. Export a plain PDF.')
    except ValidationError:
        raise
    except Exception:
        # Parser errors may contain excerpts from a private document.
        raise ValidationError('This PDF could not be read safely. Export a plain, unencrypted PDF and try again.') from None
    return {'kind':'book', 'page_count':pages, 'duration_seconds':0}


def inspect_mp3(raw):
    if not (raw.startswith(b'ID3') or (len(raw) > 2 and raw[0] == 255 and raw[1] & 224 == 224)):
        raise ValidationError('This file is not an MP3. Export or convert your song to MP3 first.')
    try:
        info = MP3(io.BytesIO(raw)).info
        if (info.layer != 3 or not math.isfinite(info.length) or not 0 < info.length <= 7200
                or not 8000 <= info.sample_rate <= 48000 or info.channels not in (1,2)
                or info.bitrate <= 0 or info.sketchy):
            raise ValueError
        duration = mp3_frame_duration(raw)
        if abs(duration-info.length) > max(2, duration*.05):
            raise ValueError
    except Exception:
        raise ValidationError('This MP3 is damaged or unsupported. Try exporting it again (up to 2 hours).') from None
    return {'kind':'song', 'page_count':0, 'duration_seconds':duration}


def mp3_frame_duration(raw):
    """Require complete Layer III frames, not just a convincing ID3 header."""
    offset, end, duration, frames = 0, len(raw), 0.0, 0
    if raw.startswith(b'ID3'):
        if len(raw) < 10 or any(n >= 128 for n in raw[6:10]):
            raise ValueError
        offset = 10 + sum(n << shift for n,shift in zip(raw[6:10],(21,14,7,0)))
        if raw[3] == 4 and raw[5] & 16:
            offset += 10
    if raw[-128:-125] == b'TAG':
        end -= 128
    while offset < end:
        if end-offset < 4:
            raise ValueError
        header = int.from_bytes(raw[offset:offset+4],'big')
        version, layer, rate_index, bitrate_index = (header>>19)&3,(header>>17)&3,(header>>10)&3,(header>>12)&15
        if header>>21 != 2047 or version == 1 or layer != 1 or rate_index == 3 or bitrate_index in [0,15]:
            raise ValueError
        rates = (44100,48000,32000)
        rate = rates[rate_index] // (1 if version == 3 else 2 if version == 2 else 4)
        table = (32,40,48,56,64,80,96,112,128,160,192,224,256,320) if version == 3 else (8,16,24,32,40,48,56,64,80,96,112,128,144,160)
        length = (144000 if version == 3 else 72000)*table[bitrate_index-1]//rate + ((header>>9)&1)
        if offset+length > end:
            raise ValueError
        duration += (1152 if version == 3 else 576)/rate
        frames += 1; offset += length
    if frames < 2 or not 0 < duration <= 7200:
        raise ValueError
    return duration
