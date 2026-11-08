"""Bound upload memory before CSRF middleware reads multipart request bodies."""
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.uploadhandler import FileUploadHandler, StopUpload
from django.http import HttpResponse

MAX_BYTES = 3*1024*1024


class BoundedUploadHandler(FileUploadHandler):
    def __init__(self,request):
        super().__init__(request);self.total=0;self.count=0;self.file=None

    def new_file(self,*args,**kwargs):
        super().new_file(*args,**kwargs);self.count+=1
        if self.count>1:
            self.request.upload_rejected=True
            raise StopUpload(connection_reset=False)
        self.file=BytesIO()

    def receive_data_chunk(self,raw_data,start):
        self.total+=len(raw_data)
        if self.total>MAX_BYTES:
            self.request.upload_rejected=True
            raise StopUpload(connection_reset=False)
        self.file.write(raw_data)
        return None

    def file_complete(self,file_size):
        self.file.seek(0)
        return InMemoryUploadedFile(self.file,self.field_name,self.file_name,self.content_type,
                                    file_size,self.charset,self.content_type_extra)

    def upload_interrupted(self):
        if self.file:self.file.close()


class UploadLimitMiddleware:
    def __init__(self,get_response):
        self.get_response=get_response

    def __call__(self,request):
        if request.path=='/my-library/new/' and request.method=='POST':
            try:length=int(request.META.get('CONTENT_LENGTH') or 0)
            except (TypeError,ValueError):length=MAX_BYTES+65537
            if length>MAX_BYTES+65536 or length<0:
                response=HttpResponse('<h1>File too large</h1><p>Upload one PDF or MP3 of up to 3 MiB.</p><p><a href="/my-library/new/">Choose another file</a></p>',status=413)
                response['Cache-Control']='no-store, private'
                return response
            request.upload_handlers=[BoundedUploadHandler(request)]
        return self.get_response(request)
