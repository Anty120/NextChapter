from functools import lru_cache
from io import BytesIO, StringIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject, TextStringObject

from catalog.models import UploadedMedia
from catalog.upload_validation import MAX_FILE_BYTES, MAX_USER_BYTES, inspect_file


def pdf_bytes(encrypted=False, active=False, pages=3):
    writer=PdfWriter()
    for _ in range(pages):
        page=writer.add_blank_page(width=612,height=792)
        font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
        content=DecodedStreamObject();content.set_data(b'BT /F1 20 Tf 50 700 Td (A public test book for NextChapter.) Tj ET')
        page[NameObject('/Contents')]=writer._add_object(content)
    if encrypted:writer.encrypt('test-password')
    if active:writer._root_object[NameObject('/OpenAction')]=DictionaryObject({NameObject('/S'):NameObject('/JavaScript'),NameObject('/JS'):TextStringObject('app.alert("test");')})
    stream=BytesIO();writer.write(stream);return stream.getvalue()


@lru_cache
def mp3_bytes():
    raw=(Path(__file__).resolve().parents[1]/'catalog/static/catalog/audio/library/audiobook-es-01.mp3').read_bytes()
    # An in-memory test excerpt of the existing credited LibriVox recording.
    # Start at a verified complete MPEG-1 Layer III frame after the source tags.
    offset=10+sum(n<<shift for n,shift in zip(raw[6:10],(21,14,7,0))) if raw.startswith(b'ID3') else 0
    frames=[]
    for _ in range(300):
        header=int.from_bytes(raw[offset:offset+4],'big')
        assert header>>21==2047
        version=(header>>19)&3;rate=(44100,48000,32000)[(header>>10)&3]//(1 if version==3 else 2 if version==2 else 4)
        table=(32,40,48,56,64,80,96,112,128,160,192,224,256,320) if version==3 else (8,16,24,32,40,48,56,64,80,96,112,128,144,160)
        length=(144000 if version==3 else 72000)*table[((header>>12)&15)-1]//rate+((header>>9)&1)
        frame=raw[offset:offset+length];offset+=length
        if b'Xing' not in frame and b'Info' not in frame:frames.append(frame)
    return b''.join(frames)


class UploadTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user('file-owner')
        self.other=get_user_model().objects.create_user('other-reader')
        self.client.force_login(self.user)

    def upload(self,raw=None,name='book.pdf',**extra):
        return self.client.post('/my-library/new/',{'title':'My test book','creator':'Test author','language':'French',
            'description':'A test file','permission':'on','file':SimpleUploadedFile(name,raw or pdf_bytes(),content_type='application/octet-stream'),**extra})

    def item(self):
        self.assertEqual(self.upload().status_code,302)
        return UploadedMedia.objects.get()

    def test_pdf_upload_private_reader_range_and_saved_page(self):
        item=self.item()
        self.assertEqual(item.owner,self.user);self.assertEqual(item.kind,'book');self.assertEqual(item.page_count,3)
        self.assertEqual(item.review_status,'private')
        self.assertContains(self.client.get(item.get_absolute_url()),'Read your PDF')
        url=reverse('uploads:file',args=[item.pk]);response=self.client.get(url)
        self.assertEqual(response['Content-Type'],'application/pdf');self.assertTrue(response.content.startswith(b'%PDF-'))
        self.assertIn('no-store',response['Cache-Control']);self.assertIn('sandbox',response['Content-Security-Policy'])
        partial=self.client.get(url,HTTP_RANGE='bytes=10-29');self.assertEqual(partial.status_code,206)
        self.assertEqual(partial.content,response.content[10:30])
        self.assertEqual(self.client.head(url)['Content-Length'],str(item.byte_size))
        self.assertEqual(self.client.get(url,HTTP_RANGE='bytes=-15').content,response.content[-15:])
        for header in ['bytes=99999999-','bytes=4-1','bytes=-0','bytes=1-3,5-7','bytes='+'1'*5000+'-']:
            self.assertEqual(self.client.get(url,HTTP_RANGE=header).status_code,416)
        path=reverse('uploads:progress',args=[item.pk])
        self.assertEqual(self.client.post(path,{'page':2}).status_code,302)
        item.refresh_from_db();self.assertEqual(item.saved_page,2)
        self.assertContains(self.client.get(item.get_absolute_url()),'#page=2')
        for value in ['0','4','nan']:
            self.assertEqual(self.client.post(path,{'page':value}).status_code,400)

    def test_real_mp3_validation_and_listening_position(self):
        self.assertEqual(self.upload(mp3_bytes(),'song.mp3').status_code,302)
        item=UploadedMedia.objects.get();self.assertEqual(item.kind,'song');self.assertGreater(item.duration_seconds,5)
        response=self.client.get(item.get_absolute_url());self.assertContains(response,'<audio',html=False)
        url=reverse('uploads:progress',args=[item.pk]);self.assertEqual(self.client.post(url,{'seconds':'2.4'},HTTP_ACCEPT='application/json').status_code,200)
        item.refresh_from_db();self.assertEqual(item.saved_seconds,2.4)
        for value in ['-1','nan','inf','999999']:
            self.assertEqual(self.client.post(url,{'seconds':value}).status_code,400)

    def test_owner_and_csrf_protection(self):
        item=self.item()
        paths=[item.get_absolute_url(),reverse('uploads:file',args=[item.pk]),reverse('uploads:delete',args=[item.pk]),reverse('uploads:submit',args=[item.pk])]
        self.client.force_login(self.other)
        for path in paths:self.assertEqual(self.client.get(path).status_code,404)
        for route,data in [('progress',{'page':2}),('delete',{'confirm':'delete'}),('withdraw',{}),('edit',{'title':'Stolen'})]:
            self.assertEqual(self.client.post(reverse('uploads:'+route,args=[item.pk]),data).status_code,404)
        self.assertNotContains(self.client.get('/my-library/'),item.title)
        browser=Client(enforce_csrf_checks=True);browser.force_login(self.user)
        for path in ['/my-library/new/',reverse('uploads:progress',args=[item.pk]),reverse('uploads:delete',args=[item.pk]),reverse('uploads:submit',args=[item.pk]),reverse('uploads:withdraw',args=[item.pk])]:
            self.assertEqual(browser.post(path,{}).status_code,403)
        self.client.logout()
        for path in ['/my-library/',*paths]:self.assertEqual(self.client.get(path).status_code,302)

    def test_invalid_files_rights_size_and_parser_bounds(self):
        for raw,name in [(b'<script>bad</script>','book.pdf'),(b'ID3'+b'x'*200,'song.mp3'),(pdf_bytes(),'song.mp3'),
                         (pdf_bytes(encrypted=True),'locked.pdf'),(pdf_bytes(active=True),'active.pdf'),
                         (mp3_bytes()[:-4],'cut.mp3'),(pdf_bytes(),'book.exe'),(b'x'*(MAX_FILE_BYTES+1),'large.pdf')]:
            self.assertIn(self.upload(raw,name).status_code,[400,413],name)
        self.assertEqual(self.upload(permission='').status_code,400)
        self.assertEqual(UploadedMedia.objects.count(),0)

    def test_duplicate_quota_no_binary_list_fetch_and_seed_preservation(self):
        item=self.item();self.assertEqual(self.upload().status_code,302);self.assertEqual(UploadedMedia.objects.count(),1)
        with CaptureQueriesContext(connection) as queries:self.client.get('/my-library/')
        self.assertFalse(any('"content"' in q['sql'] for q in queries))
        with patch('catalog.upload_views.MAX_USER_BYTES',item.byte_size):
            self.assertContains(self.upload(pdf_bytes(pages=2)), 'Your library is full',status_code=400)
        call_command('seed_demo',stdout=StringIO());item.refresh_from_db();self.assertEqual(bytes(item.content),pdf_bytes())
        url=reverse('uploads:delete',args=[item.pk]);self.assertEqual(self.client.get(url).status_code,200)
        self.assertEqual(UploadedMedia.objects.count(),1)
        self.assertEqual(self.client.post(url,{}).status_code,400)
        self.assertEqual(self.client.post(url,{'confirm':'delete'}).status_code,302);self.assertFalse(UploadedMedia.objects.exists())

    def submit(self,item):
        return self.client.post(reverse('uploads:submit',args=[item.pk]),{'creator':'Test author','license_name':'Original work',
            'rights_note':'I wrote this original test book.','permission':'on'})

    def test_explicit_review_publish_reject_and_withdraw(self):
        item=self.item();url=reverse('uploads:submit',args=[item.pk])
        self.assertEqual(self.client.post(url,{}).status_code,400)
        self.assertEqual(self.submit(item).status_code,302);item.refresh_from_db();self.assertEqual(item.review_status,'pending')
        public=reverse('uploads:public_file',args=[item.pk]);self.assertEqual(self.client.get(public).status_code,404)
        admin=get_user_model().objects.create_superuser('reviewer',password='test-only-password')
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse('uploads:review_file',args=[item.pk])).status_code,200)
        change=reverse('admin:catalog_uploadedmedia_change',args=[item.pk])
        self.assertEqual(self.client.post(change,{'review_status':'rejected','review_notes':''}).status_code,200)
        item.refresh_from_db();self.assertEqual(item.review_status,'pending')
        self.assertEqual(self.client.post(change,{'review_status':'rejected','review_notes':'Please add permission evidence.'}).status_code,302)
        self.client.force_login(self.user);self.assertContains(self.client.get(item.get_absolute_url()),'Please add permission evidence.')
        self.submit(item);self.client.force_login(admin)
        self.assertEqual(self.client.post(change,{'review_status':'approved','review_notes':'Original test work accepted.'}).status_code,302)
        item.refresh_from_db();self.assertEqual(item.reviewed_by,admin)
        self.client.logout();self.assertEqual(self.client.get(item.public_url).status_code,200);self.assertEqual(self.client.get(public).status_code,200)
        self.assertContains(self.client.get('/'),'Community · unrated')
        self.client.force_login(self.user);self.client.post(reverse('uploads:withdraw',args=[item.pk]))
        self.assertEqual(self.client.get(public).status_code,404)
        self.client.force_login(admin);self.client.post(change,{'review_status':'approved','review_notes':'Stale review'})
        item.refresh_from_db();self.assertEqual(item.review_status,'private')

    def test_staff_without_review_permission_and_private_admin_visibility(self):
        item=self.item()
        staff=get_user_model().objects.create_user('limited-staff',is_staff=True)
        self.client.force_login(staff)
        path=reverse('uploads:review_file',args=[item.pk]);self.assertEqual(self.client.get(path).status_code,403)
        staff.user_permissions.add(Permission.objects.get(codename='change_uploadedmedia'))
        self.assertEqual(self.client.get(path).status_code,404)
        self.assertNotContains(self.client.get(reverse('admin:catalog_uploadedmedia_changelist')),item.title)

    def test_corrections_unpublish_and_cannot_edit_owner_or_file(self):
        item=self.item();UploadedMedia.objects.filter(pk=item.pk).update(review_status='approved')
        result=self.client.post(reverse('uploads:edit',args=[item.pk]),{'title':'Corrected title','creator':'Correct author',
            'language':'German','description':'Updated description','owner':self.other.pk,'review_status':'approved'})
        self.assertEqual(result.status_code,302);item.refresh_from_db()
        self.assertEqual(item.owner,self.user);self.assertEqual(item.review_status,'private')
        self.assertEqual(item.title,'Corrected title');self.assertEqual(bytes(item.content),pdf_bytes())
        self.assertEqual(self.client.get(item.public_url).status_code,404)

    def test_multiple_files_and_pre_csrf_body_limit(self):
        result=self.client.post('/my-library/new/',{'title':'Multiple files','language':'French','permission':'on',
            'file':[SimpleUploadedFile('one.pdf',pdf_bytes()),SimpleUploadedFile('two.pdf',pdf_bytes())]})
        self.assertEqual(result.status_code,400)
        browser=Client(enforce_csrf_checks=True);browser.force_login(self.user)
        result=browser.post('/my-library/new/',b'x'*(MAX_FILE_BYTES+65537),content_type='application/octet-stream')
        self.assertEqual(result.status_code,413)
        self.assertEqual(UploadedMedia.objects.count(),0)

    def test_community_search_and_filters_keep_unrated_files_separate(self):
        item=self.item()
        UploadedMedia.objects.filter(pk=item.pk).update(title='Unique community book',language='German',review_status='approved')
        response=self.client.get('/',{'q':'Unique community book'})
        self.assertContains(response,'Your matches are on the community shelf.')
        self.assertNotContains(response,'No media matches these filters')
        self.assertContains(response,'value="German"')
        for filters in [{'format':'audio'},{'level':'A1'},{'language':'French'}]:
            self.assertNotContains(self.client.get('/',filters),'Unique community book')
