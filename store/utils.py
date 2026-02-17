import os
import uuid
import base64


def expression_image_upload_to(instance, filename):
    """Upload to 'store/image/expression/<subtitle.video.slug>/<filename>'."""
    if instance.subtitle and instance.subtitle.video:
        video_slug = instance.subtitle.video.slug
    else:
        video_slug = 'no_video'

    # Clean filename to avoid weird characters
    base, ext = os.path.splitext(filename)
    safe_filename = f'{base}{ext}'

    return f'store/image/expression/{video_slug}/{safe_filename}'


def video_upload_to(instance, filename):
    """Upload to 'store/video/<host.slug>/<filename>'."""
    if instance.host:
        host_slug = instance.host.slug
    else:
        host_slug = 'no_host'

    # Clean filename to avoid weird characters
    base, ext = os.path.splitext(filename)
    safe_filename = f'{base}{ext}'

    return f'store/video/{host_slug}/{safe_filename}'


def short_uuid():
    # Generate UUID4 and encode in URL-safe base64 without padding
    u = uuid.uuid4()
    # urlsafe_b64encode returns bytes, decode to str, strip trailing '='
    return base64.urlsafe_b64encode(u.bytes).rstrip(b'=').decode('ascii')
