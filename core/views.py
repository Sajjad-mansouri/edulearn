# core/views.py

import os
import re

from django.conf import settings
from django.http import Http404, HttpResponse, StreamingHttpResponse
from django.views import View


class MediaRangeView(View):
    chunk_size = 1024 * 1024

    def get(self, request, path):
        file_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, path))

        media_root = os.path.abspath(settings.MEDIA_ROOT)

        # Prevent ../ path traversal.
        if not file_path.startswith(media_root + os.sep):
            raise Http404

        if not os.path.isfile(file_path):
            raise Http404

        file_size = os.path.getsize(file_path)

        range_header = request.headers.get("Range")

        if not range_header:
            response = StreamingHttpResponse(
                self._file_iterator(
                    file_path,
                    0,
                    file_size - 1,
                ),
                content_type=self._content_type(file_path),
            )
            response["Content-Length"] = str(file_size)
            response["Accept-Ranges"] = "bytes"
            return response

        match = re.fullmatch(
            r"bytes=(\d*)-(\d*)",
            range_header.strip(),
        )

        if not match:
            return self._range_not_satisfiable(file_size)

        start_str, end_str = match.groups()

        if not start_str and not end_str:
            return self._range_not_satisfiable(file_size)

        if start_str:
            start = int(start_str)
        else:
            # bytes=-500
            suffix_length = int(end_str)

            if suffix_length <= 0:
                return self._range_not_satisfiable(file_size)

            start = max(file_size - suffix_length, 0)

        if end_str and start_str:
            end = int(end_str)
        else:
            end = file_size - 1

        if start >= file_size or start > end:
            return self._range_not_satisfiable(file_size)

        end = min(end, file_size - 1)

        content_length = end - start + 1

        response = StreamingHttpResponse(
            self._file_iterator(
                file_path,
                start,
                end,
            ),
            status=206,
            content_type=self._content_type(file_path),
        )

        response["Accept-Ranges"] = "bytes"
        response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        response["Content-Length"] = str(content_length)

        return response

    def _file_iterator(self, file_path, start, end):
        with open(file_path, "rb") as file:
            file.seek(start)

            remaining = end - start + 1

            while remaining > 0:
                chunk = file.read(min(self.chunk_size, remaining))

                if not chunk:
                    break

                yield chunk
                remaining -= len(chunk)

    def _range_not_satisfiable(self, file_size):
        response = HttpResponse(status=416)
        response["Content-Range"] = f"bytes */{file_size}"
        return response

    def _content_type(self, file_path):
        import mimetypes

        content_type, _ = mimetypes.guess_type(file_path)

        return content_type or "application/octet-stream"
