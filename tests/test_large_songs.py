"""Real 10 MB MP3 boundary, bounded transport, isolation and retry checks."""
from datetime import timedelta
from functools import lru_cache
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase
from django.utils import timezone

from catalog.models import SongUploadDraft, UploadedMedia
from catalog.upload_limits import CHUNK_BYTES, MAX_SONG_BYTES, MAX_PDF_BYTES, MAX_USER_BYTES
from catalog.upload_validation import inspect_file
from tests.test_uploads import mp3_bytes


@lru_cache
def large_mp3():
    frames=mp3_bytes()
    count=(MAX_SONG_BYTES-10)//len(frames)
    padding=MAX_SONG_BYTES-10-count*len(frames)
    tag_size=bytes((padding>>shift)&127 for shift in (21,14,7,0))
    return b'ID3\x03\x00\x00'+tag_size+b'\0'*padding+frames*count


class LargeSongTests(TestCase):
    def setUp(self):
        self.owner=get_user_model().objects.create_user('large-song-owner')
        self.other=get_user_model().objects.create_user('large-song-other')
        self.client.force_login(self.owner)

    def start(self,**changes):
        return self.client.post('/my-library/song-upload/start/',{
            'title':'Full size song','language':'Spanish','permission':True,'size':MAX_SONG_BYTES,**changes},content_type='application/json')

    def send_all(self,draft,raw):
        for offset in range(0,len(raw),CHUNK_BYTES):
            response=self.client.post(draft['chunk_url']+'?offset='+str(offset),raw[offset:offset+CHUNK_BYTES],content_type='application/octet-stream')
            self.assertEqual(response.status_code,200,response.content)
            self.assertEqual(response.json()['offset'],min(offset+CHUNK_BYTES,len(raw)))

    def test_exact_limit_upload_finish_play_download_and_retry(self):
        raw=large_mp3();self.assertEqual(len(raw),MAX_SONG_BYTES)
        draft=self.start().json()
        self.assertEqual(self.client.post(draft['finish_url']).status_code,409)
        self.send_all(draft,raw)
        response=self.client.post(draft['finish_url']);self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(self.client.post(draft['finish_url']).json(),response.json())
        item=UploadedMedia.objects.get();self.assertEqual(bytes(item.content),raw);self.assertEqual(item.kind,'song')
        pending=SongUploadDraft.objects.get();self.assertTrue(pending.complete);self.assertEqual(bytes(pending.content),b'')
        url=item.get_absolute_url()+'file/'
        self.assertEqual(self.client.head(url)['Content-Length'],str(MAX_SONG_BYTES))
        self.assertContains(self.client.get(url+'?download=1'),'data-song-download')
        collected=[]
        for offset in range(0,len(raw),CHUNK_BYTES):
            response=self.client.get(url,HTTP_RANGE=f'bytes={offset}-')
            self.assertEqual(response.status_code,206);self.assertLessEqual(len(response.content),CHUNK_BYTES)
            collected.append(response.content)
        self.assertEqual(b''.join(collected),raw)
        item.review_status='approved';item.save(update_fields=['review_status'])
        public='/my-library/public/'+str(item.pk)+'/file/'
        self.assertEqual(Client().get(public,HTTP_RANGE='bytes=9000000-').content,raw[9000000:])
        self.client.post(item.get_absolute_url()+'withdraw/')
        self.assertEqual(Client().get(public,HTTP_RANGE='bytes=0-').status_code,404)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url,HTTP_RANGE='bytes=0-').status_code,404)
        self.assertEqual(self.client.post(draft['finish_url']).status_code,404)
        self.client.force_login(self.owner);item.delete()
        self.assertEqual(self.client.post(draft['finish_url']).status_code,410)

    def test_format_limits_and_invalid_mp3(self):
        for name,size in [('song.mp3',MAX_SONG_BYTES+1),('book.pdf',MAX_PDF_BYTES+1)]:
            with self.assertRaises(ValidationError):inspect_file(SimpleUploadedFile(name,b'x'*size))
        self.assertEqual(self.start(size=MAX_SONG_BYTES+1).status_code,400)
        self.assertEqual(self.start(permission=False).status_code,400)
        self.assertEqual(self.start(language='invented').status_code,400)
        size=MAX_PDF_BYTES+1;draft=self.start(size=size).json();self.send_all(draft,b'x'*size)
        self.assertEqual(self.client.post(draft['finish_url']).status_code,400)
        self.assertFalse(UploadedMedia.objects.exists());self.assertFalse(SongUploadDraft.objects.exists())

    def test_chunk_retries_order_size_permissions_and_csrf(self):
        draft=self.start().json();url=draft['chunk_url'];chunk=b'a'*CHUNK_BYTES
        self.assertEqual(self.client.post(url+'?offset=1',chunk,content_type='application/octet-stream').status_code,409)
        for _ in range(2):
            self.assertEqual(self.client.post(url+'?offset=0',chunk,content_type='application/octet-stream').json()['offset'],CHUNK_BYTES)
        self.assertEqual(self.client.post(url+'?offset=0',b'b',content_type='application/octet-stream').status_code,409)
        self.assertEqual(self.client.post(url+'?offset=0',chunk+b'a',content_type='application/octet-stream').status_code,413)
        self.assertEqual(len(bytes(SongUploadDraft.objects.get().content)),CHUNK_BYTES)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(draft['cancel_url']).status_code,404)
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.owner)
        self.assertEqual(csrf.post(url+'?offset=0',b'a',content_type='application/octet-stream').status_code,403)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(draft['cancel_url']).status_code,200);self.assertFalse(SongUploadDraft.objects.exists())

    def test_quota_reservation_replacement_and_expiry(self):
        item=UploadedMedia.objects.create(owner=self.owner,title='Existing',kind='song',language='French',
            byte_size=MAX_SONG_BYTES,content=b'',sha256='a'*64,permission_confirmed_at=timezone.now())
        UploadedMedia.objects.create(owner=self.owner,title='Existing 2',kind='song',language='French',
            byte_size=MAX_SONG_BYTES,content=b'',sha256='b'*64,permission_confirmed_at=timezone.now())
        self.assertEqual(self.start().status_code,200)
        self.assertEqual(self.start().status_code,200);self.assertEqual(SongUploadDraft.objects.count(),1)
        from tests.test_uploads import pdf_bytes
        from unittest.mock import patch
        # A reserved song consumes quota before finalization.
        with patch('catalog.upload_views.MAX_USER_BYTES',20_000_100):
            response=self.client.post('/my-library/new/',{'title':'Book','language':'French','permission':'on',
                'file':SimpleUploadedFile('book.pdf',pdf_bytes())})
        self.assertEqual(response.status_code,400);self.assertContains(response,'library is full',status_code=400)
        SongUploadDraft.objects.update(expires_at=timezone.now()-timedelta(seconds=1))
        call_command('cleanup_upload_drafts',stdout=StringIO());self.assertFalse(SongUploadDraft.objects.exists())
        with patch('catalog.song_uploads.MAX_USER_BYTES',20_000_000):self.assertEqual(self.start().status_code,400)
